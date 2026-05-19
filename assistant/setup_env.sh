#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$ROOT/venv"

if [ -d "$VENV" ]; then
  echo "Virtualenv already exists at $VENV"
  exit 0
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 required"
  exit 1
fi

python3 -m venv "$VENV"
# shellcheck disable=SC1090
source "$VENV/bin/activate"
pip install --upgrade pip
if [ -f "$ROOT/requirements.txt" ]; then
  pip install -r "$ROOT/requirements.txt"
fi

echo "Virtualenv created and dependencies installed in $VENV"
