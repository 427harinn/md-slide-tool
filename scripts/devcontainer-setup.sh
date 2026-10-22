#!/usr/bin/env bash
set -euo pipefail

cd /work

npm install
npm link

completion_line='source /work/completions/slidegen.bash'
if ! grep -qxF "$completion_line" "$HOME/.bashrc"; then
  printf '\n%s\n' "$completion_line" >> "$HOME/.bashrc"
fi
