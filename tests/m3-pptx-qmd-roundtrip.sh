#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

mkdir -p "$WORK/images"
cp "$ROOT/templates/pptx/template/template.pptx" "$WORK/template.pptx"
python3 - "$WORK/images/picture.png" <<'PY'
from PIL import Image
import sys
Image.new("RGB", (640, 360), "navy").save(sys.argv[1])
PY

cat > "$WORK/deck.qmd" <<'QMD'
---
title: M3 roundtrip
format:
  pptx:
    reference-doc: template.pptx
---

## Original title

Original body.

![Original caption](images/picture.png)
QMD

node "$ROOT/cli/slidegen.js" render "$WORK/deck.qmd"

python3 - "$WORK/deck.pptx" <<'PY'
from pptx import Presentation
import sys

pptx = sys.argv[1]
prs = Presentation(pptx)
slide = next(slide for slide in prs.slides if any(
    shape.is_placeholder and int(shape.placeholder_format.type) == 1
    for shape in slide.shapes
))
title = next(shape for shape in slide.shapes if shape.is_placeholder and int(shape.placeholder_format.type) == 1)
title.text = "Escaped *title*"
body = next(shape for shape in slide.shapes if shape.is_placeholder and int(shape.placeholder_format.type) == 7)
body.text = "Literal [body] and \\ slash"
caption = next(shape for shape in slide.shapes if shape.name.startswith("mdst-caption-"))
caption.text = "Caption ] plus *mark*"
prs.save(pptx)
PY

node "$ROOT/cli/slidegen.js" import "$WORK/deck.pptx"
python3 - "$WORK/deck.qmd" <<'PY'
from pathlib import Path
import sys
text = Path(sys.argv[1]).read_text(encoding="utf-8")
assert r"## Escaped \*title\*" in text
assert r"Literal \[body\] and \\ slash" in text
assert r"![Caption \] plus \*mark\*]" in text
PY

node "$ROOT/cli/slidegen.js" render "$WORK/deck.qmd"
python3 - "$WORK/deck.pptx" "$WORK/deck.assets.json" <<'PY'
import json
from pathlib import Path
from pptx import Presentation
import sys

pptx, assets_path = sys.argv[1:]
assets = json.loads(Path(assets_path).read_text(encoding="utf-8"))
prs = Presentation(pptx)
slide_id = assets["elements"][0]["slideId"]
slide = next(slide for slide in prs.slides if slide.name == slide_id)
title = next(shape for shape in slide.shapes if shape.is_placeholder and int(shape.placeholder_format.type) == 1)
body = next(shape for shape in slide.shapes if shape.is_placeholder and int(shape.placeholder_format.type) == 7)
caption = next(shape for shape in slide.shapes if shape.name.startswith("mdst-caption-"))
assert title.text == "Escaped *title*"
assert "Literal [body] and \\ slash" in body.text
assert caption.text == "Caption ] plus *mark*"
PY
