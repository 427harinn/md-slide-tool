#!/usr/bin/env bash
set -euo pipefail

if ! command -v code >/dev/null 2>&1; then
  printf '%s\n' "VS Code remote 'code' CLI is unavailable. This installer must run after VS Code attaches via postAttachCommand." >&2
  exit 127
fi

EXTENSION_DIR="/work/vscode-extension"
EXTENSION_VERSION="$(node -p "require('$EXTENSION_DIR/package.json').version")"
VSIX_PATH="$EXTENSION_DIR/md-slide-tool-powerpoint-$EXTENSION_VERSION.vsix"
EXTENSION_ID="md-slide-tool.md-slide-tool-powerpoint"
STATE_DIR="$HOME/.cache/md-slide-tool"
STATE_FILE="$STATE_DIR/powerpoint-extension.sha256"

cd /work

source_hash="$(sha256sum "$EXTENSION_DIR/package.json" "$EXTENSION_DIR/package-lock.json" "$EXTENSION_DIR/.vscodeignore" "$EXTENSION_DIR/README.md" "$EXTENSION_DIR"/src/*.js | sha256sum | cut -d ' ' -f 1)"
installed_extensions="$(code --list-extensions)"

if [[ ! -f "$STATE_FILE" || "$(cat "$STATE_FILE")" != "$source_hash" || ! -f "$VSIX_PATH" ]] || ! grep -Fxq "$EXTENSION_ID" <<< "$installed_extensions"; then
  npm --prefix "$EXTENSION_DIR" ci
  npm --prefix "$EXTENSION_DIR" run package
  code --install-extension "$VSIX_PATH" --force
  mkdir -p "$STATE_DIR"
  printf '%s\n' "$source_hash" > "$STATE_FILE"
fi
