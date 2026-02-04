# Smoke Tests

BATS smoke tests for quick validation of core functionality.

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
# Run all smoke tests
bats tests/smoke/

# Run specific test file
bats tests/smoke/stdin.bats

# Run with verbose output
bats -t tests/smoke/stdin.bats
```

## Test Files

- **stdin.bats**: Tests for stdin/stdout mode functionality
  - Local execution with `uv run`
  - Installed package execution
  - Docker execution with stdin passthrough
  - Flag validation (incompatible flags)
  - Diarization with stdin mode

## Requirements

Tests require:
- `OPENAI_API_KEY` environment variable (for transcription tests)
- `HF_TOKEN` environment variable (for diarization tests)
- Test audio file: `tests/hello_conversation.mp3`
- Docker image `vtt:latest` (for Docker tests)

Tests will skip gracefully if requirements are not met.
