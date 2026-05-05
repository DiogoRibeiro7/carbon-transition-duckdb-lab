#!/usr/bin/env bash
set -euo pipefail

if ! command -v poetry >/dev/null 2>&1; then
  echo "Poetry is required. Install it first: https://python-poetry.org/docs/#installation"
  exit 1
fi

poetry install --with dev
echo "Environment ready."
