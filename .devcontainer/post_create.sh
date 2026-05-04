#!/usr/bin/env bash
set -euo pipefail

python - <<'PY'
import sys
if sys.version_info < (3, 14, 2):
    raise SystemExit(
        f"Python 3.14.2 or newer is required for the pinned Home Assistant version; got {sys.version.split()[0]}"
    )
PY

python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements_dev.txt

mkdir -p .devcontainer/config
ln -sfn ../../custom_components .devcontainer/config/custom_components

if command -v pre-commit >/dev/null 2>&1; then
  pre-commit install || true
fi
