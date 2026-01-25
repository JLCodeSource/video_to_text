
PYTHON ?= python
PIP ?= pip

.PHONY: help install test lint ruff-check ruff-fix mypy format clean

help:
	@echo "Available targets: install, test, lint, ruff-check, ruff-fix, mypy, format, clean"

# Install development tooling (uv) and sync environment
install:
	@set -e; \
	curl -LsSf https://astral.sh/uv/install.sh | sh; \
	uv venv && \
	uv sync || true

# Use `uv run` for all runtime targets so commands run inside the project's environment
test:
	@uv run pytest -v --cov=./ --cov-report=term-missing

ruff-check:
	@uv run ruff check .

ruff-fix:
	@uv run ruff format .

mypy:
	@uv run mypy .

lint: ruff-check mypy

format: ruff-fix

clean:
	@find . -name "*.pyc" -delete || true
	@find . -name "__pycache__" -type d -exec rm -rf {} + || true
