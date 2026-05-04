#!/usr/bin/env bash
set -euo pipefail

mkdir -p .devcontainer/config
ln -sfn ../../custom_components .devcontainer/config/custom_components

. .venv/bin/activate
python -m homeassistant --config .devcontainer/config --debug
