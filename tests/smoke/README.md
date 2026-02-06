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
bats tests/smoke/standard.bats

# Run with verbose output
bats -t tests/smoke/stdin.bats

# Or pass environment variables inline
OPENAI_API_KEY="your-key" bats tests/smoke/stdin.bats

# Force Docker image rebuild (useful for testing fresh builds)
FORCE_DOCKER_REBUILD=1 bats tests/smoke/

# Force Docker rebuild with no cache
FORCE_DOCKER_REBUILD=1 DOCKER_NO_CACHE=1 bats tests/smoke/
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

- **standard.bats**: Environment/integration tests for standard (non-stdin) file processing
  - ✅ MP3 audio file transcription (vtt command, uv run)
  - ✅ MP4 video file transcription (vtt command, uv run)
  - ✅ Diarization with `--diarize --no-review-speakers`
  - ✅ Output format validation (timestamps, default filenames)
  
  **Note:** Docker is not tested in standard.bats because the Docker container only supports stdin mode

## Docker Rebuild Controls

The stdin.bats tests support environment variables to control Docker image rebuilding:

- **`FORCE_DOCKER_REBUILD=1`**: Forces Docker images to be rebuilt even if they already exist
- **`DOCKER_NO_CACHE=1`**: Adds `--no-cache` flag to Docker build commands (ensures fresh build without layer caching)

These are useful for:
- Testing fresh Docker builds before releases
- Debugging Docker-specific issues
- Validating dependency changes in containers

**Note:** Docker rebuild controls only apply to stdin.bats since the Docker container only supports stdin mode

## Requirements

Tests require:
- `OPENAI_API_KEY` environment variable (for transcription tests)
- `HF_TOKEN` environment variable (for diarization tests)
- Test audio file: `tests/hello_conversation.mp3`
- Test video file: `tests/hello_conversation.mp4` (created from MP3 with blank video stream)
- Installed `vtt` command (for installed package tests) - install with `uv pip install -e .`

**For stdin.bats Docker tests only:**
- Docker image `vtt:latest` - build with `docker build -t vtt:latest .`
- Docker image `vtt:diarization` - build with `docker build -f Dockerfile.diarization -t vtt:diarization .`

Tests will skip gracefully if requirements are not met.
