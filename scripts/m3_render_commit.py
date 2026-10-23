#!/usr/bin/env python3
"""Atomically publish the paired outputs of an M3 render."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from m3_core import valid_document_id, validate_assets
from m3_transaction import FileTransaction


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--qmd", required=True)
    parser.add_argument("--pptx", required=True)
    parser.add_argument("--assets", required=True)
    args = parser.parse_args()
    qmd = Path(args.qmd).resolve(strict=True)
    pptx = Path(args.pptx).resolve(strict=True)
    assets_path = Path(args.assets).resolve(strict=True)
    assets = validate_assets(json.loads(assets_path.read_text(encoding="utf-8")))
    document_id = assets.get("documentId")
    if assets["schemaVersion"] != 2 or not valid_document_id(document_id):
        raise ValueError("render candidate assets require schema v2 documentId")
    final_pptx = qmd.with_suffix(".pptx")
    final_assets = qmd.with_suffix(".assets.json")
    tx = FileTransaction(qmd.parent, document_id, paired_qmd_path=qmd)
    tx.stage(final_pptx, pptx.read_bytes())
    tx.stage(final_assets, assets_path.read_bytes())
    tx.commit()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
