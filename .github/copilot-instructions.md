# Copilot Instructions for vtt-transcribe

## Project Overview
A Python CLI tool (`vtt-transcribe`) that extracts audio from video files and transcribes it using OpenAI's Whisper model. **Published on PyPI** as of v0.3.0b3 (Released 2026-02-01). The key architectural challenge is handling large audio files that exceed the 25MB Whisper API limit by intelligently chunking them into minute-aligned segments.

**Current Version**: v0.3.0b3
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
This project uses **bd (beads)** for issue tracking.
Run `bd prime` for workflow context, or install hooks (`bd hooks install`) for auto-injection.

**Quick reference:**
- `bd ready` - Find unblocked work
- `bd create "Title" --type task --priority 2` - Create issue
- `bd close <id>` - Complete work
- `bd sync` - Sync with git (run at session end)

For full workflow details: `bd prime`

### 3. GitHub Operations
**Use `.github/skills/gh-cli/SKILL.md` for all GitHub interactions**:
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

## Critical Developer Workflows

### Git & PR Workflow

**⚠️ CRITICAL RULE: NEVER merge directly to main without a Pull Request!**

All changes to main MUST go through PRs:
1. Create feature branch from main
2. Make changes and commit
3. Push branch to remote
4. Create Pull Request on GitHub
5. Wait for CI/PR checks to pass
6. Get review if needed
7. Merge PR (NOT direct git merge to main)

### Setup
```bash
make install  # Installs uv, creates venv, syncs dependencies
bd init       # Initialize beads (if not already initialized)
```

### Development Commands (Always run before PRs)
- `make test` — Run full pytest suite with coverage (97%+ required)
- `make lint` — Run ruff check + mypy (must pass, zero errors)
- `make format` — Auto-fix formatting with ruff

### Task Workflow Example
```bash
# 1. Check beads for next task
bd list --ready

# 2. Start task
bd update <id> --claim

# 3. Create feature branch
git checkout -b feature/T095-subtask-work

# 4. Follow TDD workflow (.github/skills/pytest-tdd/SKILL.md)
* Create [branch]-work for Red-Green-Refactor cycles
* Write test (red), implement (green), refactor
* Squash merge back to feature branch

# 5. Validate before PR
make lint && make test

# 6. Create PR using gh CLI
gh pr create --title "feat(<id>): description" --body "..."

# 7. Mark task complete
bd update <id> --status closed
```

## Project-Specific Conventions

### Testing Patterns
- **Unit tests** split between `test_main.py` (CLI, transcriber, formatting) and `test_audio_management.py` (audio/chunk management)
- **Mock strategy**: Avoid mocks where possible, but currently heavy use of `unittest.mock.patch` to avoid OpenAI API calls and file I/O
- **Test doubles**: Some tests inject mocked modules (hence `# type: ignore` annotations for type checking)
- **Chunk file discovery**: `find_existing_chunks()` uses glob pattern matching (`{stem}_chunk*.mp3`)

### Code Quality Standards
- **Type hints**: Required everywhere (Python 3.13+); mypy strict checking
- **Ruff rules**: Comprehensive set enabled (E, W, F, UP, N, S, B, etc.); disabled only COM812 (comma conflicts)
- **Per-file ignores**: Tests have special ruff rules allowing private member access for testing
- **API key handling**: Supports both `-k` flag and `OPENAI_API_KEY` env var; `get_api_key()` function handles precedence

### Pre-commit Hooks
Project includes `.pre-commit-config.yaml`; CI runs `make install && make lint && make test` on all PRs

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
