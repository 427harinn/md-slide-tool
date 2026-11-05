#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

FILE="$1"
DOCUMENT_ID="$2"
PREVIEW_OUTPUT="${3:-}"

if [ -z "$FILE" ]; then
  echo "使い方: bash scripts/render-current-pipeline.sh <file.qmd>"
  exit 1
fi

FILE="$(realpath "$FILE")"
DIR="$(dirname "$FILE")"
BASENAME="$(basename "$FILE")"
STEM="${BASENAME%.*}"

RENDER_QMD="$DIR/.${STEM}.render.qmd"
IMAGES_JSON="$DIR/.${STEM}.images.json"
ASSETS_JSON="$DIR/${STEM}.assets.json"
RENDER_BASENAME="$(basename "$RENDER_QMD")"
RENDER_STEM="${RENDER_BASENAME%.*}"
RENDER_PPTX="$DIR/${RENDER_STEM}.pptx"
FINAL_PPTX="$DIR/${STEM}.pptx"
WORK_DIR="$(mktemp -d "$DIR/.${STEM}.m3-render.XXXXXX")"
trap 'rm -rf "$WORK_DIR"; rm -f "$RENDER_QMD" "$IMAGES_JSON" "$RENDER_PPTX"' EXIT
CANDIDATE_PPTX="$WORK_DIR/${STEM}.pptx"
CANDIDATE_ASSETS="$WORK_DIR/${STEM}.assets.json"

echo "Rendering: $FILE"

python3 "$REPO_ROOT/scripts/prepare-qmd-for-pptx.py" \
  --input "$FILE" \
  --output "$RENDER_QMD" \
  --images-json "$IMAGES_JSON"

if grep -q "pptx" "$RENDER_QMD"; then
  TEMPLATE=$(grep -E "reference-doc:" "$RENDER_QMD" | head -1 | sed 's/.*reference-doc:[[:space:]]*//')
  if [ -n "$TEMPLATE" ]; then
    TEMPLATE_PATH="$DIR/$TEMPLATE"
    if [ -f "$TEMPLATE_PATH" ]; then
      echo "テンプレ検出: $TEMPLATE_PATH"
      node "$REPO_ROOT/scripts/normalize-pptx-template.js" "$TEMPLATE_PATH"
    fi
  fi
fi

cd "$DIR"
quarto render "$RENDER_BASENAME"

if [ -f "$RENDER_PPTX" ]; then
  cp "$RENDER_PPTX" "$CANDIDATE_PPTX"
else
  echo "PPTXが見つかりません: $RENDER_PPTX"
  exit 1
fi

POSTPROCESS_ASSETS="$CANDIDATE_ASSETS"

echo "画像後処理: ${PREVIEW_OUTPUT:-$FINAL_PPTX}"
python3 "$REPO_ROOT/scripts/m3_render_seed.py" \
  --qmd "$FILE" --output "$CANDIDATE_ASSETS" --document-id "$DOCUMENT_ID"
python3 "$REPO_ROOT/scripts/postprocess-pptx.py" \
  --pptx "$CANDIDATE_PPTX" \
  --images-json "$IMAGES_JSON" \
  --assets "$POSTPROCESS_ASSETS" \
  --qmd "$FILE"

if [ -n "$PREVIEW_OUTPUT" ]; then
  python3 "$REPO_ROOT/scripts/m4_preview.py" mark \
    --pptx "$CANDIDATE_PPTX" --qmd "$FILE" --document-id "$DOCUMENT_ID" \
    --generation "$(basename "$PREVIEW_OUTPUT" .pptx | sed 's/^preview-//')"
  python3 - "$CANDIDATE_PPTX" "$PREVIEW_OUTPUT" <<'PY'
import os, sys
os.replace(sys.argv[1], sys.argv[2])
PY
else
  python3 "$REPO_ROOT/scripts/m3_render_commit.py" \
    --qmd "$FILE" --pptx "$CANDIDATE_PPTX" --assets "$CANDIDATE_ASSETS"
fi

echo "cleanup..."
echo "完了: ${PREVIEW_OUTPUT:-$FINAL_PPTX}"
