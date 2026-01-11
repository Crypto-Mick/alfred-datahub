#!/usr/bin/env bash
set -euo pipefail

# Directory of this script: smart-parser/smart-parser-ui/scripts
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# UI root: smart-parser/smart-parser-ui
UI_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# smart-parser root: parent of UI
SP_ROOT="$(cd "${UI_ROOT}/.." && pwd)"

# Python from smart-parser venv
PYTHON="${SP_ROOT}/.venv/bin/python"

if [ ! -x "$PYTHON" ]; then
  echo "ERROR: smart-parser venv not found at $PYTHON"
  exit 1
fi

cd "$SP_ROOT"
exec "$PYTHON" -m src.main
