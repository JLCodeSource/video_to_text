# Video To Text

Takes a video file, extracts or splits the audio, and transcribes the audio to text
using OpenAI's Whisper model (via the `openai` Python client).

This repository provides a small CLI tool (`main.py`) and a set of helper
functions for handling audio extraction, chunking large audio files, and
formatting verbose JSON transcripts into readable timestamped output.

Features
 - Extract audio from a video file (writes `.mp3` by default)
 - Prefer minute-aligned chunk durations for large audio files
 - Transcribe audio via Whisper with `verbose_json` response format
 - Format transcripts into human-friendly lines: `[MM:SS - MM:SS] text`
 - Shift chunk-local timestamps into absolute timeline when chunking
 - Keep or delete intermediate audio/chunk files based on flags

Dependencies
 - Python 3.13+
 - moviepy (audio/video helpers)
 - openai (Whisper API client)
 - Dev / test: pytest, mypy, ruff, pre-commit, coverage

Quick start

1. Run the single installer which installs `uv`, creates the project's virtual
environment, and syncs the development environment:

```bash
make install
```

2. Run the CLI (simple example):

```bash
uv run python main.py -k $OPENAI_API_KEY path/to/video.mp4
```

CLI options
 - `video_file`: positional path to the input video file
 - `-k, --api-key`: OpenAI API key (or set `OPENAI_API_KEY` env var)
 - `-o, --output-audio`: path for extracted audio file (defaults to video name with `.mp3`)
 - `-s, --save-transcript`: path to save the transcript (will ensure `.txt` extension)
 - `-f, --force`: re-extract audio even if it already exists
 - `--delete-audio`: delete audio files after transcription (default is to keep them)

Makefile targets
 - `make install` — installs `uv` (via the installer script) and runs `uv sync`.
 - `make test` — runs the test suite (`pytest`).
 - `make ruff-check` — runs `ruff check .`.
 - `make ruff-fix` — runs `ruff format .` (autoformat where supported).
 - `make mypy` — runs `mypy .` for static typing checks.
 - `make lint` — runs both `ruff` and `mypy` (alias for `ruff-check mypy`).
 - `make format` — runs the automatic ruff-format step (`ruff format .`).
 - `make clean` — remove compiled python artifacts.

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

Continuous Integration
 - The repository includes a GitHub Actions workflow (`.github/workflows/ci.yml`) that
   runs `make install` followed by `make lint` and `make test` on pushes and pull
   requests to `main`. This mirrors the recommended local `make install` setup.

Acknowledgements
 - This project was developed with test-driven iterations and linting guidance.
 - Parts of the implementation and assistance during development were produced
	 with help from GitHub Copilot.

Files of interest
 - [main.py](main.py) — CLI entrypoint and `VideoTranscriber` implementation
 - [test_main.py](test_main.py) — main test suite (integration + unit tests)
 - [test_audio_management.py](test_audio_management.py) — audio/chunk management tests
 - [Makefile](Makefile) — convenience commands for dev tooling
 - [ruff.toml](ruff.toml) — ruff configuration
 - [.pre-commit-config.yaml](.pre-commit-config.yaml) — pre-commit hooks for formatting/linting

Contributing
 - Please run `make format` and `make lint` before submitting a PR.
 - Run `make test` to ensure all tests pass locally.

License
 - See the `LICENSE` file in the repository root.

