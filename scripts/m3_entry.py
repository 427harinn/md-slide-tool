#!/usr/bin/env python3
"""M3 CLI entry orchestration: lock, recover, then invoke Core operations."""

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from m3_core import new_document_id, valid_document_id, read_custom_properties
from m3_transaction import _atomic_lock, bootstrap_key, recover_transactions, recover_bootstrap_transactions


def assets_path(qmd: Path) -> Path:
    return qmd.with_name(qmd.stem + ".assets.json")


def current_document_id(qmd: Path) -> str | None:
    path = assets_path(qmd)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid assets file: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("invalid assets schema")
    if data.get("schemaVersion") == 2:
        value = data.get("documentId")
        if not valid_document_id(value):
            raise ValueError("invalid assets documentId")
        return value
    if data.get("schemaVersion") != 1 or not isinstance(data.get("elements"), list):
        raise ValueError("unsupported assets schema")
    return None


def bootstrap_document_id(qmd: Path) -> str:
    """Choose an ID while bootstrap is held, without publishing a partial pair.

    The render pipeline publishes schema-v2 assets and managed PPTX metadata
    together through its file transaction. Until that commit, legacy v1 assets
    and the previous PPTX remain untouched and import remains unavailable.
    """
    path = assets_path(qmd)
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
    else:
        data = {"schemaVersion": 1, "slideSize": None, "elements": []}
    if data.get("schemaVersion") == 2:
        doc_id = data.get("documentId")
        if not valid_document_id(doc_id):
            raise ValueError("invalid assets documentId")
        return doc_id
    if data.get("schemaVersion") != 1 or not isinstance(data.get("elements"), list):
        raise ValueError("unsupported assets schema")
    # A legacy assets file may still be paired with an M3-marked PPTX from an
    # interrupted/older migration. Reuse only a complete, valid presentation
    # identity; never mint a conflicting ID over it.
    pptx = qmd.with_suffix(".pptx")
    doc_id = None
    if pptx.is_file():
        props = read_custom_properties(pptx)
        if any(key.startswith("md-slide-tool.") for key in props):
            doc_id = props.get("md-slide-tool.document-id")
            if (props.get("md-slide-tool.managed") != "1" or
                    props.get("md-slide-tool.format-version") != "1" or
                    not valid_document_id(doc_id)):
                raise ValueError("invalid paired PPTX document metadata")
    doc_id = doc_id or new_document_id()
    return doc_id


def run_locked(qmd: Path, operation: list[str]) -> int:
    qmd = qmd.resolve(strict=True)
    if not qmd.is_file() or qmd.suffix.lower() != ".qmd":
        raise ValueError("paired input must be a QMD file")
    project_dir = qmd.parent
    doc_id = current_document_id(qmd)
    lock_base = project_dir / ".md-slide-tool" / "locks"
    if operation[0] == "import" and doc_id is None:
        raise ValueError("unmanaged legacy presentation; render with an M3-capable version first")

    def invoke(active_id: str) -> int:
        recover_transactions(project_dir, active_id, qmd)
        if operation[0] == "render":
            shell = Path(__file__).resolve().parent / "render-current-pipeline.sh"
            command = ["bash", str(shell), str(qmd), active_id]
            return subprocess.call(command)
        importer = Path(__file__).resolve().parent / "import-pptx.py"
        return subprocess.call([sys.executable, str(importer), "--pptx", operation[1], "--locked"])

    if doc_id is None:
        # Keep bootstrap through reread, render, and paired-file commit. The
        # document lock is acquired before any work; neither lock is released
        # until schema-v2 assets and the managed PPTX have been published.
        bootstrap_context = _atomic_lock(lock_base / "bootstrap" / bootstrap_key(qmd) / "owner.lock")
        document_context = None
        bootstrap_context.__enter__()
        try:
            recover_bootstrap_transactions(project_dir, qmd)
            doc_id = current_document_id(qmd) or bootstrap_document_id(qmd)
            document_context = _atomic_lock(lock_base / "document" / doc_id / "owner.lock")
            document_context.__enter__()
        except BaseException:
            bootstrap_context.__exit__(*sys.exc_info())
            raise
        try:
            return invoke(doc_id)
        finally:
            bootstrap_context.__exit__(*sys.exc_info())
            document_context.__exit__(*sys.exc_info())
    with _atomic_lock(lock_base / "document" / doc_id / "owner.lock"):
        recover_transactions(project_dir, doc_id, qmd)
        return invoke(doc_id)


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    render = sub.add_parser("render")
    render.add_argument("qmd")
    imp = sub.add_parser("import")
    imp.add_argument("pptx")
    args = parser.parse_args()
    if args.command == "render":
        qmd = Path(args.qmd)
        return run_locked(qmd, ["render"])
    pptx = Path(args.pptx).resolve(strict=True)
    qmd = pptx.with_suffix(".qmd")
    return run_locked(qmd, ["import", str(pptx)])


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
