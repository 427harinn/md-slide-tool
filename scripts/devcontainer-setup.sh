#!/usr/bin/env bash
set -euo pipefail

cd /work

npm install
npm link

if [ -d /work/vscode-extension ]; then
  npm --prefix /work/vscode-extension install
  npm --prefix /work/vscode-extension run build
  npm --prefix /work/vscode-extension run package:vsix

  if command -v code >/dev/null 2>&1; then
    code --install-extension /work/vscode-extension/dist/md-slide-tool-pptx-preview.vsix --force
  else
    echo "VS Code CLI 'code' was not found; skipping extension install."
  fi
fi

completion_line='source /work/completions/slidegen.bash'
if ! grep -qxF "$completion_line" "$HOME/.bashrc"; then
  printf '\n%s\n' "$completion_line" >> "$HOME/.bashrc"
fi
