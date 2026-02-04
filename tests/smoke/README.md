# Smoke Tests

BATS smoke tests for environment/integration validation of core functionality.

## Purpose

These smoke tests focus on **environment and integration concerns** that cannot be easily tested in Python unit tests:
- Docker container behavior
- Package installation and CLI availability
- Environment variable handling
- Process piping and I/O

**Note:** Business logic and CLI flag validation is tested in Python unit tests (`tests/test_*.py`), not here.

## Setup

Install BATS:
```bash
# Ubuntu/Debian
sudo apt-get install bats

# macOS
brew install bats-core

# Or use npm
npm install -g bats
```

## Running Tests

```bash
# Export environment variables first
export OPENAI_API_KEY="your-key"
export HF_TOKEN="your-token"  # Optional, for diarization tests

# Run all smoke tests
bats tests/smoke/

# Run specific test file
bats tests/smoke/stdin.bats

# Run with verbose output
bats -t tests/smoke/stdin.bats

# Or pass environment variables inline
OPENAI_API_KEY="your-key" bats tests/smoke/stdin.bats
```

## Test Files

- **stdin.bats**: Environment/integration tests for stdin/stdout mode
  - ✅ Local execution with `uv run`
  - ✅ Installed package execution (`vtt` command)
  - ✅ Docker container with stdin passthrough
  - ✅ Docker output redirection
  - ✅ Docker diarization with environment variables
  
  **Removed tests** (now covered by Python unit tests):
  - ❌ Flag validation (see `tests/test_stdin_mode.py::TestStdinIncompatibleFlags`)
  - ❌ Auto-enable --no-review-speakers (see `tests/test_main.py::TestStdinMode`)

## Requirements

Tests require:
- `OPENAI_API_KEY` environment variable (for transcription tests)
- `HF_TOKEN` environment variable (for diarization tests)
- Test audio file: `tests/hello_conversation.mp3`
- Docker image `vtt:latest` (for Docker tests) - build with `docker build -t vtt:latest .`
- Installed `vtt` command (for installed package tests) - install with `uv pip install -e .`

Tests will skip gracefully if requirements are not met.
