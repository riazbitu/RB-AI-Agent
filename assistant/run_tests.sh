#!/usr/bin/env bash
set -euo pipefail

# Ensure Python can import the local assistant package
export PYTHONPATH="$(pwd):$PYTHONPATH"
python3 -m unittest discover -s tests -p 'test_*.py'

echo "All tests passed."
