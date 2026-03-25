#!/usr/bin/env bash
set -e

FILE="$1"

if [ -z "$FILE" ]; then
  echo "使い方: bash scripts/render-current.sh <file.qmd>"
  exit 1
fi

FILE="$(realpath "$FILE")"
DIR="$(dirname "$FILE")"

echo "Rendering: $FILE"

# pptxかどうか判定（軽め）
if grep -q "pptx" "$FILE"; then

  # reference-doc を取得
  TEMPLATE=$(grep -E "reference-doc:" "$FILE" | head -1 | sed 's/.*reference-doc:[[:space:]]*//')

  if [ -n "$TEMPLATE" ]; then
    TEMPLATE_PATH="$DIR/$TEMPLATE"

    if [ -f "$TEMPLATE_PATH" ]; then
      echo "テンプレ検出: $TEMPLATE_PATH"
      echo "テンプレを正規化します..."

      node /work/scripts/normalize-pptx-template.js "$TEMPLATE_PATH"
    else
      echo "テンプレが見つかりません: $TEMPLATE_PATH"
    fi
  else
    echo "reference-doc 未指定"
  fi
fi

quarto render "$FILE"