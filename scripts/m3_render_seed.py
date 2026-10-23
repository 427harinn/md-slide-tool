#!/usr/bin/env python3
"""Build a temporary schema-v2 asset seed for an M3 render candidate."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from m3_core import valid_document_id, validate_assets


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--qmd", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--document-id", required=True)
    args = parser.parse_args()
    qmd = Path(args.qmd).resolve(strict=True)
    output = Path(args.output).resolve(strict=False)
    if not valid_document_id(args.document_id):
        raise ValueError("invalid render documentId")
    source = qmd.with_name(qmd.stem + ".assets.json")
    if source.exists():
        data = validate_assets(json.loads(source.read_text(encoding="utf-8")))
    else:
        data = {"schemaVersion": 1, "slideSize": None, "elements": []}
    if data["schemaVersion"] == 2 and data["documentId"] != args.document_id:
        raise ValueError("assets documentId mismatch")
    seeded = {"schemaVersion": 2, "documentId": args.document_id,
              "slideSize": data.get("slideSize"), "elements": data["elements"]}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(seeded, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
