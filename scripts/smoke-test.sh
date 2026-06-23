#!/usr/bin/env bash
set -euo pipefail

npm run start -- --help
npm run start -- list-templates
npm pack --dry-run
