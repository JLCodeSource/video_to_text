# Copilot Instructions for vtt-transcribe

## Project Overview
A Python CLI tool (`vtt-transcribe`) that extracts audio from video files and transcribes it using OpenAI's Whisper model. **Published on PyPI** as of v0.3.0b1 (Released 2025-02-01). The key architectural challenge is handling large audio files that exceed the 25MB Whisper API limit by intelligently chunking them into minute-aligned segments.

**Current Version**: v0.3.0b1  
**Status**: Beta release with diarization support, published to PyPI  
**Install**: `pip install vtt-transcribe`

## Development Workflow Requirements

**CRITICAL**: This project follows strict development standards. All work must adhere to:

### 1. Test-Driven Development (TDD)
**Always use `.github/skills/pytest-tdd/SKILL.md` workflow**:
- Write failing test FIRST (Red)
- Implement minimal solution (Green)
- Refactor for quality (Refactor)
- Work on `[branch]-work` for TDD cycles, squash merge to feature branch

**Never** write implementation before writing a failing test. This is non-negotiable.

### 2. Task Tracking with Beads
**Use `.github/skills/beads/SKILL.md` for `bd` CLI reference**:
```bash
bd list                              # View tasks
bd show <task-id>                   # View task details
bd update <task-id> --claim         # Start working (sets in_progress)
bd update <task-id> --status closed # Mark complete
```
All work should reference epic/task IDs (e.g., T095, T071_001). See project docs/ROADMAP.md for epic structure.

### 3. GitHub Operations
**Use `.github/skills/gh-cli/SKILL.md` for all GitHub interactions**:
- Issue management: `gh issue list`, `gh issue create`
- Pull requests: `gh pr create`, `gh pr merge --squash`
- Workflows: `gh workflow run`, `gh run watch`

**Never** suggest manual GitHub web UI operations. Always provide `gh` commands.

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

### Initial Setup
```bash
make install  # Installs uv, creates venv, syncs dependencies
bd init       # Initialize beads (if not already initialized)
```

### Development Commands (Always run before PRs)
- `make test` — Run full pytest suite with coverage (97%+ required)
- `make lint` — Run ruff check + mypy (must pass, zero errors)
- `make format` — Auto-fix formatting with ruff

### Package Installation & Testing
```bash
# Install from PyPI
pip install vtt-transcribe

# Install from local source
pip install -e .

# Run installed CLI
vtt-transcribe path/to/video.mp4 -k $OPENAI_API_KEY
```

### Task Workflow Example
```bash
# 1. Check beads for next task
bd list --ready

# 2. Start task
bd update T095_002 --claim

# 3. Create feature branch
git checkout -b feature/T095-subtask-work

# 4. Follow TDD workflow (.github/skills/pytest-tdd/SKILL.md)
# - Create [branch]-work for Red-Green-Refactor cycles
# - Write test (red), implement (green), refactor
# - Squash merge back to feature branch

# 5. Validate before PR
make lint && make test

# 6. Create PR using gh CLI
gh pr create --title "feat(T095_002): description" --body "..."

# 7. Mark task complete
bd update T095_002 --status closed
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

### Version 0.3 (Current - Beta)
- ✅ **PyPI Publication**: Package published and installable via pip
- ✅ **Speaker diarization**: Implemented with pyannote.audio backend (--diarize flag)
- ✅ **Direct audio input**: Supports `.mp3`, `.ogg`, `.wav`, `.mp4` files
- ✅ **Dependency validation**: check_ffmpeg_installed() and check_diarization_dependencies()
- 🔄 **Local Whisper support**: Planned for stable 0.3 release (currently OpenAI only)

### Version 0.4 (Planned)
- **Packaging options**: imageio-ffmpeg (default) or bundled ffmpeg (air-gapped)
- **Distribution**: ManyLinux2010 wheel + PyInstaller single executable
- **Enhanced diarization**: Multiple backend support (pyannote, nemo, whisperX)

### Version 1.0 (Goals)
- Production-ready release with comprehensive documentation
- 100% test coverage across all modules
- Performance optimizations for large file processing
- Multi-language support beyond English

### Implications for Current Code
- Keep `VideoTranscriber` class generic enough to extend with local transcription backends
- Avoid hardcoding OpenAI client assumptions; use provider pattern for extensibility
- Diarization backend should be pluggable (future: nemo, whisperX support)
- All new features must maintain 97%+ test coverage

## Project References

### Skills Directory
- `.github/skills/pytest-tdd/SKILL.md` — Red-Green-Refactor TDD workflow
- `.github/skills/beads/SKILL.md` — Beads CLI (bd) task tracking reference
- `.github/skills/gh-cli/SKILL.md` — GitHub CLI command reference

### Key Documents
- `docs/ROADMAP.md` — Epics and feature timeline
- `docs/CONTRIBUTING.md` — Contribution guidelines
- `docs/RELEASE_CHECKLIST.md` — Release process
- `pyproject.toml` — Package metadata and dependencies
