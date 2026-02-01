
PYTHON ?= python
PIP ?= pip

.PHONY: help install install-diarization test test-integration lint ruff-check ruff-fix mypy format clean build build-check publish-test publish

help:
	@echo "Available targets:"
	@echo "  install                - Install uv and sync basic environment (no diarization)"
	@echo "  install-diarization    - Install with diarization support (includes pyannote.audio + torch)"
	@echo "  test                   - Run all tests with coverage"
	@echo "  test-integration       - Run only integration tests"
	@echo "  lint                   - Run ruff and mypy checks"
	@echo "  ruff-check             - Run ruff linter"
	@echo "  ruff-fix               - Auto-fix with ruff formatter"
	@echo "  mypy                   - Run mypy type checking"
	@echo "  format                 - Alias for ruff-fix"
	@echo "  build                  - Build distribution packages (wheel + sdist)"
	@echo "  build-check            - Validate built packages with twine"
	@echo "  publish-test           - Publish to TestPyPI (requires TestPyPI setup)"
	@echo "  publish                - Publish to PyPI (requires PyPI setup)"
	@echo "  clean                  - Remove compiled Python artifacts and build artifacts"

# Install development tooling (uv) and sync basic environment (no diarization)
install:
	@set -e; \
	curl -LsSf https://astral.sh/uv/install.sh | sh; \
	uv venv --clear && \
	uv sync && \
	uv run pre-commit install

# Install with full diarization support (includes torch + pyannote.audio)
install-diarization:
	@set -e; \
	curl -LsSf https://astral.sh/uv/install.sh | sh; \
	uv venv --clear && \
	uv sync --extra diarization && \
	uv run pre-commit install

# Use `uv run` for all runtime targets so commands run inside the project's environment
test:
	@uv run pytest -v --cov=./ --cov-report=term-missing

test-integration:
	@uv run pytest -v -k integration

ruff-check:
	@uv run ruff check .

ruff-fix:
	@uv run ruff format .

mypy:
	@uv run mypy . --ignore-missing-imports --disallow-untyped-defs --disallow-incomplete-defs --check-untyped-defs --warn-unused-ignores --warn-redundant-casts

lint: ruff-check mypy

format: ruff-fix

clean:
	@find . -name "*.pyc" -delete || true
	@find . -name "__pycache__" -type d -exec rm -rf {} + || true
	@rm -rf dist/ build/ *.egg-info/ || true

# Build distribution packages (wheel + source distribution)
build:
	@echo "Installing build dependencies..."
	@uv sync --extra build
	@echo "Building distribution packages..."
	@uv run python -m build --sdist --wheel
	@echo "Build complete! Artifacts in dist/"
	@ls -lh dist/

# Validate built packages
build-check: build
	@echo "Checking distribution packages..."
	@uv run twine check dist/*

# Publish to TestPyPI (for testing)
publish-test: build-check
	@echo "Publishing to TestPyPI..."
	@uv run twine upload --repository testpypi dist/*
	@echo "Published to TestPyPI! View at: https://test.pypi.org/project/vtt-transcribe/"
	@echo "Install with: pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ vtt-transcribe"

# Publish to production PyPI
publish: build-check
	@echo "⚠️  WARNING: Publishing to production PyPI!"
	@echo "Press Ctrl+C to cancel, or Enter to continue..."
	@read dummy
	@uv run twine upload dist/*
	@echo "Published to PyPI! View at: https://pypi.org/project/vtt-transcribe/"
	@echo "Install with: pip install vtt-transcribe"
