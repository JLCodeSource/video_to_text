# Video To Text

Takes a video file, extracts or splits the audio, and transcribes the audio to text
using OpenAI's Whisper model (via the `openai` Python client).

This repository provides a small CLI tool (`main.py`) and a set of helper
functions for handling audio extraction, chunking large audio files, and
formatting verbose JSON transcripts into readable timestamped output.

Features
 - Extract audio from video files (writes `.mp3` by default) or transcribe audio directly (.mp3, .wav, .ogg, .m4a)
 - Prefer minute-aligned chunk durations for large audio files exceeding 25MB API limit
 - Transcribe audio via OpenAI's Whisper API with `verbose_json` response format
 - Speaker diarization using pyannote.audio to identify and label speakers in transcripts
 - Format transcripts into human-friendly lines: `[HH:MM:SS - HH:MM:SS] text` with optional speaker labels
 - Shift chunk-local timestamps into absolute timeline when chunking
 - Keep or delete intermediate audio/chunk files based on flags
 - Interactive speaker review to rename/merge speakers after diarization

## Upgrading from 0.2.0

**Important:** Version 0.3.0 introduces optional dependencies for speaker diarization. If you are upgrading from 0.2.0 and want to use diarization features, you need to explicitly install the `[diarization]` extra. See the [CHANGELOG](CHANGELOG.md) for detailed upgrade instructions.

Dependencies
 - Python 3.13+
 - **ffmpeg** (required for video/audio processing via moviepy)
 - moviepy (audio/video helpers)
 - openai (Whisper API client)
 - pyannote.audio (speaker diarization, optional - requires [diarization] extra)
 - torch (required for pyannote.audio)
 - Dev / test: pytest, mypy, ruff, pre-commit, coverage, python-dotenv

Prerequisites
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

Speaker Diarization
 - The speaker diarization feature (`--diarize`) identifies and labels different speakers in audio
 - **Requirements:**
   - Hugging Face token (set `HF_TOKEN` environment variable or use `--hf-token` flag)
   - **User must accept pyannote model access at https://huggingface.co/pyannote/speaker-diarization-3.1**
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



Quick start

**Option 1: Using devcontainer (Recommended)**
1. Open project in VS Code
2. Install "Dev Containers" extension
3. Click "Reopen in Container" when prompted (or use Command Palette: "Dev Containers: Reopen in Container")
4. The devcontainer includes ffmpeg, GPU support, and all dependencies pre-configured

**Option 2: Manual setup**

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

### From Source

1. Ensure ffmpeg is installed on your system (see Prerequisites above)

2. Run the installer which installs `uv` and creates the project's virtual environment:

```bash
# Basic install (transcription only, no diarization)
make install

# OR: Install with diarization support (includes torch + pyannote.audio)
make install-diarization
```

### Setup Environment Variables

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

CLI options

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

Makefile targets
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
 - `make build` — build distribution packages (requires TWINE credentials in environment)
 - `make publish-test` — publish to TestPyPI (requires TWINE_TEST_USERNAME and TWINE_TEST_PASSWORD)
 - `make publish` — publish to PyPI (requires TWINE_USERNAME and TWINE_PASSWORD)

Notes on linting and typing
 - `ruff` is configured in `ruff.toml`. The rule `COM812` is disabled to avoid
	 conflicts with formatters. A per-file ignore exists for tests to allow certain
	 private-member accesses used in unit tests.
 - Some tests use light mypy `# type: ignore[...]` annotations to accommodate
	 test doubles and dynamically injected modules.

Testing
 - Run the full test suite with `make test`. The project includes comprehensive
	 unit tests for audio extraction, chunking, timestamp formatting, and the CLI
	 wiring.
 - Note: The project has only been tested on Linux (and WSL2)

Continuous Integration
 - The repository includes a GitHub Actions workflow (`.github/workflows/ci.yml`) that
   runs `make install` followed by `make lint` and `make test` on pushes and pull
   requests to `main`. This mirrors the recommended local `make install` setup.

Acknowledgements
 - This project was developed with test-driven iterations and linting guidance.
 - Parts of the implementation and assistance during development were produced
	 with help from GitHub Copilot.

Files of interest
 - [CHANGELOG.md](CHANGELOG.md) — version history and upgrade instructions
 - [main.py](main.py) — CLI entrypoint and `VideoTranscriber` implementation
 - [test_main.py](test_main.py) — main test suite (integration + unit tests)
 - [test_audio_management.py](test_audio_management.py) — audio/chunk management tests
 - [Makefile](Makefile) — convenience commands for dev tooling
 - [ruff.toml](ruff.toml) — ruff configuration
 - [.pre-commit-config.yaml](.pre-commit-config.yaml) — pre-commit hooks for formatting/linting

Contributing
 - Please run `make format` and `make lint` before submitting a PR.
 - Run `make test` to ensure all tests pass locally.
 - See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed development setup and workflow.

## Building and Publishing (For Maintainers)

The project uses Hatch as the build system. Build artifacts can be created and tested locally:

```bash
# Build distribution packages (installs build dependencies as needed, creates dist/*.whl and dist/*.tar.gz)
make build

# Test publishing to TestPyPI
make publish-test

# Production publish to PyPI (via GitHub Actions on release)
# Tag a release: git tag v0.3.0b1 && git push origin v0.3.0b1
# Create GitHub release (triggers automated publish workflow)
```

For complete build and publish workflow documentation, see [CONTRIBUTING.md](CONTRIBUTING.md).

License
 - See the `LICENSE` file in the repository root.

