# vtt-transcribe

Takes a video file, extracts or splits the audio, and transcribes the audio to text
using OpenAI's Whisper model (via the `openai` Python client).

This repository provides a small CLI tool (`vtt`) and a set of helper
functions for handling audio extraction, chunking large audio files, and
formatting verbose JSON transcripts into readable timestamped output.

## Features
 - Extract audio from video files (writes `.mp3` by default) or transcribe audio directly (.mp3, .wav, .ogg, .m4a)
 - Prefer minute-aligned chunk durations for large audio files exceeding 25MB API limit
 - Transcribe audio via OpenAI's Whisper API with `verbose_json` response format
 - Speaker diarization using pyannote.audio to identify and label speakers in transcripts
 - Format transcripts into human-friendly lines: `[HH:MM:SS - HH:MM:SS] text` with optional speaker labels
 - Shift chunk-local timestamps into absolute timeline when chunking
 - Keep or delete intermediate audio/chunk files based on flags
 - Interactive speaker review to rename/merge speakers after diarization

## Dependencies
 - Python 3.10+

 Compatibility:
 - Core package supports Python 3.10 through 3.14 (tests run on 3.10–3.14).
 - Speaker diarization extras require specific native wheels (torch==2.8.0) and pyannote packages that currently provide prebuilt wheels up to Python 3.13. Therefore, diarization is officially supported up to Python 3.13.
 - If you run on Python 3.14 and need diarization, you may need to build torch from source or use a compatible wheel; this is not recommended for general users.

 - **ffmpeg** (required for video/audio processing via moviepy)
 - moviepy (audio/video helpers)
 - openai (Whisper API client)
 - pyannote.audio (speaker diarization, optional - requires [diarization] extra)
 - torch (required for pyannote.audio)
 - Dev / test: pytest, mypy, ruff, pre-commit, coverage, python-dotenv

## Prerequisites
 - **ffmpeg must be installed** on your system for video/audio processing
 - **Recommended approach**: Use the provided `.devcontainer` which includes:
   - Pre-configured ffmpeg installation
   - GPU support for diarization (if host has NVIDIA GPU + drivers)
   - All Python dependencies
   - VS Code extensions and settings
 - **Manual setup**: If not using devcontainer, ensure ffmpeg is installed:
   - Ubuntu/Debian: `sudo apt-get install ffmpeg`
   - macOS: `brew install ffmpeg`
   - Windows: Download from https://ffmpeg.org/download.html

## Speaker Diarization
 - The speaker diarization feature (`--diarize`) identifies and labels different speakers in audio
 - **Requirements:**
   - Hugging Face token (set `HF_TOKEN` environment variable or use `--hf-token` flag)
   - **Accept pyannote model terms**: Before using diarization, you must accept the terms for the following models on Hugging Face:
      - [pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1) ⭐ **Required** - main diarization model
      - [pyannote/segmentation-3.0](https://huggingface.co/pyannote/segmentation-3.0) ⭐ **Required** - speaker segmentation
      - [pyannote/speaker-diarization-community-1](https://huggingface.co/pyannote/speaker-diarization-community-1) ⭐ **Required** - community model
      - [pyannote/wespeaker-voxceleb-resnet34-LM](https://huggingface.co/pyannote/wespeaker-voxceleb-resnet34-LM) - speaker embedding (auto-downloaded)
      - **How to accept terms**: Visit each ⭐ marked model page while logged into Hugging Face and click "Accept" on the terms
      - Without accepting terms, you'll get authentication errors when attempting diarization
   - Minimum audio duration: ~10 seconds (shorter files may fail)
 - **GPU Support (Optional):**
   - Can leverage CUDA GPUs for faster processing (10-100x speedup)
   - By default, uses `--device auto` which automatically detects and uses CUDA if available
   - To explicitly control device selection, use `--device cuda` or `--device cpu`
   - .devcontainer handles prerequisites for GPU support
   - Prerequisites for GPU support:
     - NVIDIA GPU with CUDA support
     - NVIDIA drivers installed on the host system
     - `nvidia-container-toolkit` installed on the host (for Docker/devcontainer)
   - If GPU is not available or fails, automatically falls back to CPU



## Quick Start

### Option 1: Using devcontainer (Recommended)
1. Open project in VS Code
2. Install "Dev Containers" extension
3. Click "Reopen in Container" when prompted (or use Command Palette: "Dev Containers: Reopen in Container")
4. The devcontainer includes ffmpeg, GPU support, and all dependencies pre-configured

### Option 2: Manual setup

1. Ensure ffmpeg is installed on your system (see Prerequisites above)

## Installation

### From PyPI (Recommended)

```bash
# Basic installation (transcription only)
pip install vtt-transcribe

# OR: With diarization support
pip install vtt-transcribe[diarization]

# Using uv (faster)
uv pip install vtt-transcribe
uv pip install vtt-transcribe[diarization]
```

> **Note:** Installing with `[diarization]` extras adds large dependencies such as PyTorch and `pyannote.audio`, which significantly increases the download and install size of your environment. The actual diarization model weights are typically downloaded at runtime (e.g., via the Hugging Face cache) on first use, so overall disk usage for diarization (dependencies + cached models) can reach several GB. Only install these extras if you need speaker identification features.

### Using Docker (Alternative)

Docker images are available on Docker Hub and GitHub Container Registry in three variants:

- **Base image** (`latest`): Fast, lightweight, transcription-only (~27s build)
- **Diarization image** (`diarization`): Speaker diarization with PyTorch (CPU-only)
- **Diarization GPU image** (`diarization-gpu`): GPU-accelerated speaker diarization with CUDA 12.8

```bash
# Pull from Docker Hub (base image)
docker pull jlcodesource/vtt-transcribe:latest

# Pull diarization image (CPU-only, ~2.5 GB)
docker pull jlcodesource/vtt-transcribe:diarization

# Pull diarization GPU image (CUDA 12.8, ~8 GB, amd64 only)
docker pull jlcodesource/vtt-transcribe:diarization-gpu

# OR: Pull from GitHub Container Registry
docker pull ghcr.io/jlcodesource/vtt-transcribe:latest
docker pull ghcr.io/jlcodesource/vtt-transcribe:diarization
docker pull ghcr.io/jlcodesource/vtt-transcribe:diarization-gpu

# Use stdin mode to pipe audio/video data (recommended for Docker)
# Supports video formats (MP4, AVI, WebM) and audio formats (MP3, WAV, OGG)
cat input.mp4 | docker run -i -e OPENAI_API_KEY="your-key" jlcodesource/vtt-transcribe:latest

# Or redirect to save transcript to file
cat input.mp4 | docker run -i -e OPENAI_API_KEY="your-key" jlcodesource/vtt-transcribe:latest > transcript.txt

# With diarization (use diarization image, requires HF_TOKEN)
# Note: Interactive review (--no-review-speakers) automatically disabled in stdin mode
cat input.mp4 | docker run -i -e OPENAI_API_KEY="your-key" -e HF_TOKEN="your-hf-token" jlcodesource/vtt-transcribe:diarization --diarize

# GPU support for diarization (requires nvidia-docker + :diarization-gpu image)
cat input.mp4 | docker run -i --gpus all -e OPENAI_API_KEY="your-key" -e HF_TOKEN="your-hf-token" jlcodesource/vtt-transcribe:diarization-gpu --diarize --device cuda
```

**Docker Stdin Mode Limitations:**
- Volume mounting (`-v`) is not supported - use stdin/stdout instead
- Interactive speaker review (`--review-speakers`) is unavailable in stdin mode (auto-disabled)
- For diarization workflows, speaker labels will be generic (SPEAKER_00, SPEAKER_01, etc.)
- Cannot use `-s/--save-transcript`, `-o/--output-audio`, `--apply-diarization`, or `--scan-chunks` flags

**Docker Image Tags:**
- `latest` - Latest stable release (base, transcription-only)
- `diarization` - Latest release with diarization support (CPU-only, multi-arch)
- `diarization-gpu` - Latest release with diarization + CUDA GPU support (amd64 only)
- `0.3.0b4` - Specific version tags (PEP 440 format)

For more Docker usage patterns and troubleshooting, see [Docker Registry Documentation](docs/DOCKER_REGISTRY.md).

### From Source

1. Ensure ffmpeg is installed on your system (see Prerequisites above)

2. Run the installer which installs `uv` and creates the project's virtual environment:

```bash
# Basic install (transcription only, no diarization)
make install

# OR: Install with diarization support (includes torch + pyannote.audio)
make install-diarization
```

## Upgrading from 0.2.0

**Important:** Version 0.3.0 introduces optional dependencies for speaker diarization. If you are upgrading from 0.2.0 and want to use diarization features, you need to explicitly install the `[diarization]` extra. See the [CHANGELOG](docs/CHANGELOG.md) for detailed upgrade instructions.

## Setup Environment Variables

You can set environment variables in your shell or create a `.env` file in your project directory:

**Option 1: Shell environment**
```bash
export OPENAI_API_KEY="your-openai-key"
export HF_TOKEN="your-huggingface-token"  # Only needed for --diarize
```

**Option 2: .env file (automatically loaded)**
```bash
# Create a .env file in your project directory
echo 'OPENAI_API_KEY="your-openai-key"' > .env
echo 'HF_TOKEN="your-huggingface-token"' >> .env

# For publishing to PyPI (developers only)
echo 'TWINE_USERNAME=__token__' >> .env
echo 'TESTPYPI_API_TOKEN=your-testpypi-token' >> .env
echo 'PYPI_API_TOKEN=your-pypi-token' >> .env
```

The tool will automatically load variables from `.env` if the file exists.

**Publishing Environment Variables (Developers Only):**
- `TWINE_USERNAME`: Should always be `__token__` for PyPI token authentication
- `TESTPYPI_API_TOKEN`: Your TestPyPI API token
- `PYPI_API_TOKEN`: Your PyPI API token
- These are only needed if you're building and publishing packages using `make build`, `make publish-test`, or `make publish`

## Usage

### Command Line

```bash
# Basic transcription
vtt path/to/input.mp4

# With speaker diarization
vtt path/to/input.mp4 --diarize

# Direct audio transcription
vtt path/to/audio.mp3 --diarize

# Using uv run (if installed from source)
uv run vtt path/to/input.mp4
```

#### Stdin/Stdout Mode

For containerized or pipeline usage, vtt supports stdin/stdout mode with both audio and video files:

```bash
# Pipe audio directly to vtt (outputs transcript to stdout)
cat audio.mp3 | vtt

# Pipe video directly to vtt (supports MP4, AVI, WebM, etc.)
cat video.mp4 | vtt

# With Docker (video support)
cat video.mp4 | docker run -i -e OPENAI_API_KEY="$OPENAI_API_KEY" jlcodesource/vtt-transcribe:latest

# With diarization in Docker (--no-review-speakers auto-enabled)
cat video.mp4 | docker run -i \
  -e OPENAI_API_KEY="$OPENAI_API_KEY" \
  -e HF_TOKEN="$HF_TOKEN" \
  jlcodesource/vtt-transcribe:diarization --diarize

# In a pipeline
cat audio.mp3 | vtt > transcript.txt

# Process and save
cat recording.mp3 | vtt | tee transcript.txt | grep "SPEAKER_00"
```

**Notes:**
- Stdin mode is auto-detected when input is piped (non-TTY)
- Output goes to stdout instead of saving to file
- The `-s/--save-transcript` and `-o/--output-audio` flags are incompatible with stdin mode
- **Diarization automatically enables `--no-review-speakers` in stdin mode** (interactive speaker review requires TTY)

### CLI options

**Input/Output:**
 - `input_file`: positional path to the input video or audio file (.mp4, .mp3, .wav, .ogg, .m4a)
 - `-k, --api-key`: OpenAI API key (or set `OPENAI_API_KEY` env var)
 - `-o, --output-audio`: path for extracted audio file (defaults to input name with `.mp3`; not allowed if input is already audio)
 - `-s, --save-transcript`: path to save the transcript (will ensure `.txt` extension)

**Processing Options:**
 - `-f, --force`: re-extract audio even if it already exists
 - `--delete-audio`: delete audio files after transcription (default: keep them)
 - `--scan-chunks`: when input is a chunk file (e.g., `audio_chunk0.mp3`), detect and process all sibling chunks in order

**Diarization Options:**
 - `--diarize`: enable speaker diarization (requires `HF_TOKEN` and model access)
 - `--hf-token`: Hugging Face token for pyannote models (or set `HF_TOKEN` env var)
 - `--device`: device for diarization (`auto`, `cuda`/`gpu`, or `cpu`; default: `auto`)
 - `--diarize-only`: run diarization on existing audio without transcription
 - `--apply-diarization PATH`: apply diarization to an existing transcript file
 - `--no-review-speakers`: skip interactive speaker review (default: review is enabled)

### Makefile targets
 - `make install` — installs `uv` and basic dependencies (transcription only, no diarization)
 - `make install-diarization` — installs `uv` and all dependencies including diarization support
 - `make test` — runs the test suite (`pytest`)
 - `make test-integration` — runs only integration tests
 - `make ruff-check` — runs `ruff check .`
 - `make ruff-fix` — runs `ruff format .` (autoformat where supported)
 - `make mypy` — runs `mypy .` for static typing checks
 - `make lint` — runs both `ruff` and `mypy` (alias for `ruff-check mypy`)
 - `make format` — runs the automatic ruff-format step (`ruff format .`)
 - `make clean` — remove compiled python artifacts
 - `make build` — build distribution packages
 - `make publish-test` — publish to TestPyPI (requires `TESTPYPI_API_TOKEN` in environment)
 - `make publish` — publish to PyPI (requires `PYPI_API_TOKEN` in environment)

### Notes on linting and typing
 - `ruff` is configured in `ruff.toml`. The rule `COM812` is disabled to avoid
	 conflicts with formatters. A per-file ignore exists for tests to allow certain
	 private-member accesses used in unit tests.
 - Some tests use light mypy `# type: ignore[...]` annotations to accommodate
	 test doubles and dynamically injected modules.

### Testing
 - Run the full test suite with `make test`. The project includes comprehensive
	 unit tests for audio extraction, chunking, timestamp formatting, and the CLI
	 wiring.
 - Note: The project has only been tested on Linux (and WSL2)

### Continuous Integration
 - The repository includes multiple GitHub Actions workflows:
   - `.github/workflows/test.yml` — Runs tests on multiple Python versions (3.10-3.14)
   - `.github/workflows/lint.yml` — Runs linting checks (ruff + mypy)
   - `.github/workflows/publish.yml` — Publishes to PyPI on releases
   - `.github/workflows/docker-publish.yml` — Builds and publishes Docker images
 - All workflows run on pushes and pull requests to `main`

### Acknowledgements
 - This project was developed with test-driven iterations and linting guidance.
 - Parts of the implementation and assistance during development were produced
	 with help from GitHub Copilot.

### Files of interest
 - [CHANGELOG.md](docs/CHANGELOG.md) — version history and upgrade instructions
 - [vtt_transcribe/cli.py](vtt_transcribe/cli.py) — CLI argument parsing and entrypoint
 - [vtt_transcribe/main.py](vtt_transcribe/main.py) — Core transcription logic
 - [vtt_transcribe/handlers.py](vtt_transcribe/handlers.py) — Command handlers for transcription workflows
 - [vtt_transcribe/audio_manager.py](vtt_transcribe/audio_manager.py) — Audio extraction and management
 - [vtt_transcribe/audio_chunker.py](vtt_transcribe/audio_chunker.py) — Audio chunking for large files
 - [vtt_transcribe/transcriber.py](vtt_transcribe/transcriber.py) — Whisper API interaction
 - [vtt_transcribe/diarization.py](vtt_transcribe/diarization.py) — Speaker diarization using pyannote
 - [vtt_transcribe/transcript_formatter.py](vtt_transcribe/transcript_formatter.py) — Transcript formatting and speaker labeling
 - [tests/test_main.py](tests/test_main.py) — Main module tests
 - [tests/test_handlers.py](tests/test_handlers.py) — Handler tests
 - [tests/test_audio_manager.py](tests/test_audio_manager.py) — Audio management tests
 - [tests/test_audio_chunker.py](tests/test_audio_chunker.py) — Audio chunking tests
 - [tests/test_stdin_mode.py](tests/test_stdin_mode.py) — Stdin/stdout mode tests
 - [Makefile](Makefile) — convenience commands for dev tooling
 - [ruff.toml](ruff.toml) — ruff configuration
 - [.pre-commit-config.yaml](.pre-commit-config.yaml) — pre-commit hooks for formatting/linting

### Contributing
 - Please run `make format` and `make lint` before submitting a PR.
 - Run `make test` to ensure all tests pass locally.
 - This project uses **bd (beads)** for issue tracking. Run `bd prime` for workflow context.
 - See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for detailed development setup and workflow.

## Building and Publishing (For Maintainers)

The project uses Hatch as the build system. Build artifacts can be created and tested locally:

```bash
# Install build dependencies
make install-build

# Build distribution packages (creates dist/*.whl and dist/*.tar.gz)
make build

# Test publishing to TestPyPI
make publish-test

# Production publish to PyPI (via GitHub Actions on release)
# Tag a release: git tag v0.3.0b3 && git push origin v0.3.0b3
# Create GitHub release (triggers automated publish workflow)
```

For complete build and publish workflow documentation, see [CONTRIBUTING.md](docs/CONTRIBUTING.md).

### License
 - See the `LICENSE` file in the repository root.

