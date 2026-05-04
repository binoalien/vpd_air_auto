#!/usr/bin/env bash
set -euo pipefail

if [ $# -ne 1 ]; then
  echo "Usage: $0 <homeassistant-version>" >&2
  exit 1
fi

. .venv/bin/activate
python -m pip install --upgrade "homeassistant==$1"
