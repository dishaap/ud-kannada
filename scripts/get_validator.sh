#!/usr/bin/env bash
# Fetch official UD validator (git; deps: pip install regex udapi)
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p vendor
if [ -d vender/ud-tools/.git ]; then git -C vendor/ud-tools pull --ff-only; else
  git clone --depth 1 https://github.com/UniversalDependencies/tools vendor/ud-tools; fi
echo "validator at vendor/ud-tools/validate.py"