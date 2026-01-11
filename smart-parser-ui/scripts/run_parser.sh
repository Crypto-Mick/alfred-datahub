#!/usr/bin/env bash
set -euo pipefail

# Resolve directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UI_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SP_ROOT="$(cd "${UI_ROOT}/../smart-parser" && pwd)"

# Use smart-parser's own venv
PYTHON="${SP_ROOT}/.venv/bin/python"

if [ ! -x "$PYTHON" ]; then
  echo "ERROR: smart-parser venv not found at $PYTHON"
  exit 1
fi

cd "$SP_ROOT"
exec "$PYTHON" -m src.main
