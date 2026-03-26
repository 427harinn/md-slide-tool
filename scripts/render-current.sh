#!/usr/bin/env bash
set -e

FILE="$1"

if [ -z "$FILE" ]; then
  echo "使い方: bash scripts/render-current.sh <file.qmd>"
  exit 1
fi

FILE="$(realpath "$FILE")"
DIR="$(dirname "$FILE")"
BASENAME="$(basename "$FILE")"
STEM="${BASENAME%.*}"

RENDER_QMD="$DIR/.${STEM}.render.qmd"
IMAGES_JSON="$DIR/.${STEM}.images.json"
RENDER_BASENAME="$(basename "$RENDER_QMD")"
RENDER_STEM="${RENDER_BASENAME%.*}"
RENDER_PPTX="$DIR/${RENDER_STEM}.pptx"
FINAL_PPTX="$DIR/${STEM}.pptx"

echo "Rendering: $FILE"

# ----------------------------
# ① 前処理
# ----------------------------
python3 /work/scripts/prepare-qmd-for-pptx.py \
  --input "$FILE" \
  --output "$RENDER_QMD" \
  --images-json "$IMAGES_JSON"

# ----------------------------
# ② テンプレ正規化
# ----------------------------
if grep -q "pptx" "$RENDER_QMD"; then
  TEMPLATE=$(grep -E "reference-doc:" "$RENDER_QMD" | head -1 | sed 's/.*reference-doc:[[:space:]]*//')

  if [ -n "$TEMPLATE" ]; then
    TEMPLATE_PATH="$DIR/$TEMPLATE"

    if [ -f "$TEMPLATE_PATH" ]; then
      echo "テンプレ検出: $TEMPLATE_PATH"
      node /work/scripts/normalize-pptx-template.js "$TEMPLATE_PATH"
    fi
  fi
fi

# ----------------------------
# ③ Quarto render
# ----------------------------
cd "$DIR"
quarto render "$RENDER_BASENAME"

# ----------------------------
# ④ ファイル名整理
# ----------------------------
if [ -f "$RENDER_PPTX" ]; then
  if [ "$RENDER_PPTX" != "$FINAL_PPTX" ]; then
    cp "$RENDER_PPTX" "$FINAL_PPTX"
  fi
else
  echo "PPTXが見つかりません: $RENDER_PPTX"
  exit 1
fi

# ----------------------------
# ⑤ 画像後処理
# ----------------------------
echo "画像後処理: $FINAL_PPTX"
python3 /work/scripts/postprocess-pptx.py \
  --pptx "$FINAL_PPTX" \
  --images-json "$IMAGES_JSON"

# ----------------------------
# ⑥ cleanup（ここ追加）
# ----------------------------
echo "cleanup..."

rm -f "$RENDER_QMD"
rm -f "$IMAGES_JSON"
rm -f "$RENDER_PPTX"

echo "完了: $FINAL_PPTX"