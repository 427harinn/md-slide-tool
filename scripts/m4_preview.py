#!/usr/bin/env python3
"""Small T-402A probe helpers for disposable, versioned PPTX previews."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from m3_core import read_custom_properties, valid_document_id, write_custom_properties

PROBE_STATES = frozenset({
    "Rendering Preview", "Preview Ready", "Importing", "Applying QMD",
    "Pending", "Conflict", "Error",
})


def allocate_preview(project_dir: Path, document_id: str) -> tuple[Path, int]:
    """Reserve a never-before-used preview path; callers hold the M3 doc lock."""
    if not valid_document_id(document_id):
        raise ValueError("invalid documentId")
    directory = project_dir / ".md-slide-tool" / "previews" / document_id
    directory.mkdir(parents=True, exist_ok=True)
    pattern = re.compile(r"preview-(\d{6,})\.pptx$")
    generations = [int(m.group(1)) for p in directory.iterdir() if (m := pattern.fullmatch(p.name))]
    generation = max(generations, default=0) + 1
    while True:
        path = directory / f"preview-{generation:06d}.pptx"
        try:
            with path.open("xb"):
                pass
            return path, generation
        except FileExistsError:
            generation += 1


def mark_preview(pptx: Path, qmd: Path, document_id: str, generation: int) -> None:
    if generation < 1 or not valid_document_id(document_id):
        raise ValueError("invalid preview identity")
    write_custom_properties(pptx, {
        "md-slide-tool.preview": "1",
        "md-slide-tool.preview-generation": str(generation),
        "md-slide-tool.preview-source-qmd": str(qmd.resolve()),
        "md-slide-tool.document-id": document_id,
    })


def is_preview(pptx: Path) -> bool:
    return read_custom_properties(pptx).get("md-slide-tool.preview") == "1"


def cleanup_decision(path: Path, *, canonical_path: Path, is_open: bool | None,
                     is_dirty: bool | None) -> str:
    """Unknown/open/dirty previews are retained; the caller performs deletion."""
    if path.resolve(strict=False) == canonical_path.resolve(strict=False):
        return "keep"
    if is_open is None or is_dirty is None:
        return "keep"
    if is_open or is_dirty:
        return "keep"
    return "delete-eligible"


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    allocate = sub.add_parser("allocate")
    allocate.add_argument("--project-dir", type=Path, required=True)
    allocate.add_argument("--document-id", required=True)
    mark = sub.add_parser("mark")
    mark.add_argument("--pptx", type=Path, required=True)
    mark.add_argument("--qmd", type=Path, required=True)
    mark.add_argument("--document-id", required=True)
    mark.add_argument("--generation", type=int, required=True)
    args = parser.parse_args()
    if args.command == "allocate":
        path, _ = allocate_preview(args.project_dir, args.document_id)
        print(path)
    else:
        mark_preview(args.pptx, args.qmd, args.document_id, args.generation)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
