# Copilot Instructions for video-to-text

## Project Overview
A Python CLI tool that extracts audio from video files and transcribes it using OpenAI's Whisper model. The key architectural challenge is handling large audio files that exceed the 25MB Whisper API limit by intelligently chunking them into minute-aligned segments.

## Core Architecture

### Main Components (`main.py`)
- **VideoTranscriber class**: Central orchestrator handling the entire pipeline
- **Audio extraction**: Uses `moviepy.VideoFileClip` to extract MP3 audio (enforce `.mp3` extension)
- **Smart chunking**: For files >25MB, calculates optimal chunk duration using:
  - Formula: `(MAX_SIZE_MB / file_size_mb) * duration * 0.9` with 0.9 safety margin
  - Always rounds down to complete minutes (60s multiples) for clean timestamps
  - Example: 50MB file → ~12-minute chunks (not arbitrary splits)
- **Timestamp management**: When chunking, segment timestamps from responses are "absolute" (local to chunk), but must be shifted to file-level offsets when merging
- **Transcript formatting**: Whisper returns verbose JSON with segments; converts to `[MM:SS - MM:SS] text` format

### Data Flow
1. Validate video → Extract audio to MP3 → Check file size
2. If ≤25MB: Transcribe directly
3. If >25MB: Calculate chunks → Extract each chunk → Transcribe each → Shift timestamps → Merge output
4. Optional: Save transcript, delete intermediate audio/chunks

### Response Format Handling (Critical Pattern)
The `_format_transcript_with_timestamps()` method handles both dict and SDK-style responses:
- SDK response: `TranscriptionVerbose` object with `.segments` attribute (each segment has `.start`, `.end`, `.text`)
- Dict response: Fallback for alternate response formats
- Always check type and gracefully handle both formats; includes debug output for empty responses

## Critical Developer Workflows

### Setup
```bash
make install  # Installs uv, creates venv, syncs dependencies
```

### Development Commands
- `make test` — Run full pytest suite with coverage (checks both `test_main.py` and `test_audio_management.py`)
- `make lint` — Run ruff check + mypy (required before PRs)
- `make format` — Auto-fix formatting with ruff
- `make ruff-check` — Check linting violations (COM812 disabled to avoid formatter conflicts)
- `make mypy` — Type checking; some tests use `# type: ignore[...]` for test doubles

### Running the CLI
```bash
uv run python main.py -k $OPENAI_API_KEY path/to/video.mp4
# Optional flags: -o <audio_path>, -s <transcript_path>, -f (force re-extract), --delete-audio
```

## Project-Specific Conventions

### Testing Patterns
- **Unit tests** split between `test_main.py` (CLI, transcriber, formatting) and `test_audio_management.py` (audio/chunk management)
- **Mock strategy**: Heavy use of `unittest.mock.patch` to avoid actual API calls and file I/O; tests mock `OpenAI` client
- **Test doubles**: Some tests inject mocked modules (hence `# type: ignore` annotations for type checking)
- **Chunk file discovery**: `find_existing_chunks()` uses glob pattern matching (`{stem}_chunk*.mp3`)

### Code Quality Standards
- **Type hints**: Required everywhere (Python 3.13+); mypy strict checking
- **Ruff rules**: Comprehensive set enabled (E, W, F, UP, N, S, B, etc.); disabled only COM812 (comma conflicts)
- **Per-file ignores**: Tests have special ruff rules allowing private member access for testing
- **API key handling**: Supports both `-k` flag and `OPENAI_API_KEY` env var; `get_api_key()` function handles precedence

### File Organization
- Single-file architecture in `main.py` (functions + class)
- Avoid adding new files unless truly necessary; prefer extending VideoTranscriber
- Helper functions like `display_result()`, `get_api_key()`, `parse_args()` at module level
- Temporary files (chunks) use `{stem}_chunk{index}` naming; always clean up in `cleanup_audio_files()` or `cleanup_audio_chunks()`

## Integration Points & Dependencies

### External APIs
- **OpenAI Whisper API**: 25MB file size limit enforced; chunks handle overflow
- **Response type**: `openai.types.audio.transcription_verbose.TranscriptionVerbose`

### Key Dependencies
- `moviepy` (2.2.1+): Video/audio I/O; be aware of logger control (pass `logger=None` or `logger="bar"`)
- `openai` (2.15.0+): Whisper client; response format always `verbose_json`
- `pytest` + `pytest-cov`: Test framework with coverage reporting

### Pre-commit Hooks
Project includes `.pre-commit-config.yaml`; CI runs `make install && make lint && make test` on all PRs

## Common Patterns & Gotchas

### Timestamp Formatting
The `_format_timestamp()` method converts seconds to `MM:SS` format. When chunking, **segment times are local to each chunk**; you must add the chunk's start_time offset to align with the full file timeline.

### Error Handling
- Use meaningful error messages (`msg = f"..."` pattern common in codebase)
- Validate input early (e.g., `validate_video_file()`, audio path extension checks)
- Empty transcript check includes debug output to diagnose response format issues

### Path Handling
- Always use `Path` objects (from `pathlib`)
- `.with_suffix()` for extension changes
- Chunk paths: `audio_path.with_stem(f"{audio_path.stem}_chunk{index}")`

## Future Architecture (Roadmap Context)

### Version 0.3 (In Progress)
- **Direct audio input**: Support `.mp3`, `.ogg`, `.wav` files directly (not just video)
- **Speaker diarization**: Add speaker identification capabilities with configurable backends
- **Local-only processing**: Integrate local ffmpeg + offline Whisper model option (no API dependency)
- **GitHub agent support**: Add TDD workflows for automated PR validation

### Version 0.4 (Planned)
- **Packaging options**: imageio-ffmpeg (default, lightweight) or bundled ffmpeg (air-gapped environments)
- **Distribution**: ManyLinux2010 wheel + PyInstaller single executable

### Implications for Current Code
- Keep `VideoTranscriber` class generic enough to extend with audio-only paths and local transcription backends
- Avoid hardcoding OpenAI client assumptions; future versions may support local Whisper
- Consider adding plugin/backend pattern for transcription providers if adding speaker diarization

## Questions for Iteration
- Are the chunking heuristics (minute-aligned, 0.9 safety margin) sufficiently documented?
- Should I clarify the response format detection strategy further (dict vs. SDK)?
