#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

mkdir -p "$WORK/images"
cp "$ROOT/templates/pptx/template/template.pptx" "$WORK/template.pptx"
cp "$ROOT/templates/docx/template/template.docx" "$WORK/template.docx"

python3 - "$WORK/images/diagram.png" <<'PY'
from PIL import Image
import sys
Image.new("RGB", (640, 360), "navy").save(sys.argv[1])
PY

cat > "$WORK/presentation.qmd" <<'QMD'
---
title: M2 CI render
format:
  pptx:
    reference-doc: template.pptx
---

## Original title

Stable IDs and saved image layout.

![Diagram](images/diagram.png){place="right"}
QMD

node "$ROOT/cli/slidegen.js" render "$WORK/presentation.qmd"

python3 - "$WORK/presentation.qmd" "$WORK/presentation.assets.json" "$WORK/presentation.pptx" "$ROOT" <<'PY'
import json
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(sys.argv[4]) / "scripts"))
from m3_core import read_custom_properties

qmd = Path(sys.argv[1])
assets_path = Path(sys.argv[2])
assets = json.loads(assets_path.read_text(encoding="utf-8"))
entry = assets["elements"][0]
assert assets["schemaVersion"] == 2
assert re.fullmatch(r"document-[0-9a-f-]{36}", assets["documentId"])
props = read_custom_properties(Path(sys.argv[3]))
assert props["md-slide-tool.managed"] == "1"
assert props["md-slide-tool.format-version"] == "1"
assert props["md-slide-tool.document-id"] == assets["documentId"]
assert re.fullmatch(r"[0-9a-f]{64}", props["md-slide-tool.qmd-body-sha256"])
assert entry["type"] == "image"
assert all(type(entry[key]) is int for key in ("x", "y", "width", "height"))
ids = (entry["slideId"], entry["elementId"])
assert re.fullmatch(r"slide-[0-9a-f-]{36}", ids[0])
assert re.fullmatch(r"element-[0-9a-f-]{36}", ids[1])
snapshot = {"ids": ids, "rect": [entry[key] for key in ("x", "y", "width", "height")]}
Path(qmd.parent, "m2-layout.json").write_text(json.dumps(snapshot), encoding="utf-8")
text = qmd.read_text(encoding="utf-8")
text = text.replace("## Original title", "## Renamed title")
text = text.replace("images/diagram.png", "images/replacement.png")
qmd.write_text(text, encoding="utf-8")
Path(qmd.parent, "images", "replacement.png").write_bytes(
    Path(qmd.parent, "images", "diagram.png").read_bytes()
)
PY

node "$ROOT/cli/slidegen.js" render "$WORK/presentation.qmd"

python3 - "$WORK/presentation.assets.json" "$WORK/m2-layout.json" "$WORK/presentation.pptx" "$ROOT" <<'PY'
import json
import sys
from pathlib import Path
from pptx import Presentation
sys.path.insert(0, str(Path(sys.argv[4]) / "scripts"))
from m3_core import read_custom_properties

assets = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
snapshot = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
assert assets["schemaVersion"] == 2
assert assets["documentId"].startswith("document-")
props = read_custom_properties(Path(sys.argv[3]))
assert props["md-slide-tool.document-id"] == assets["documentId"]
assert props["md-slide-tool.managed"] == "1"
expected = snapshot["ids"]
entry = assets["elements"][0]
assert [entry["slideId"], entry["elementId"]] == expected
assert [entry[key] for key in ("x", "y", "width", "height")] == snapshot["rect"]
prs = Presentation(sys.argv[3])
slide = next(slide for slide in prs.slides if slide.name == expected[0])
picture = next(shape for shape in slide.shapes if shape.shape_type == 13)
assert picture.name == expected[1]

docx_qmd = Path(sys.argv[1]).parent / "doc.qmd"
docx_qmd.write_text('''---\ntitle: DOCX regression\nformat:\n  docx:\n    reference-doc: template.docx\n---\n\n# Regression\n\nThe existing DOCX workflow remains available.\n''', encoding="utf-8")
PY

cd "$WORK"
quarto render doc.qmd
test -s "$WORK/doc.docx"
