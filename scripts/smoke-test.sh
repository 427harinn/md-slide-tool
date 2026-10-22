#!/usr/bin/env bash
set -euo pipefail

npm run start -- --help
template_list="$(npm run start -- list-templates)"
printf '%s\n' "$template_list"
grep -q '^docx:' <<< "$template_list"
grep -q '^pptx:' <<< "$template_list"
test -f templates/docx/template/template.qmd
test -f templates/docx/template/template.docx
npm pack --dry-run
npm --prefix vscode-extension test
