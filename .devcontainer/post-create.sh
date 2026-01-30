#!/usr/bin/env bash
set -euo pipefail

# Use the project’s make target to install uv, create venv, and sync deps
make install

# Quick sanity output
uv run python -V
