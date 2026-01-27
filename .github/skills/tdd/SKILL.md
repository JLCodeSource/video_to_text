---
name: pytest-tdd
description: Implements features using strict Red-Green-Refactor cycle with Pytest. Write the failing test first, then minimal implementation, then refactor.
tools: ["edit", "terminal"]
---

# Pytest TDD

Follow Red-Green-Refactor for every feature. Never write implementation without a failing test first.

## Workflow

1. **Red**: Write test in `tests/` that fails → run `make test`
2. **Green**: Write minimal code in `vtt/main.py` to pass → run `make test`
3. **Refactor**: Improve code → run `make test` (confirm still passes)

## Git Workflow: Red-Green-Refactor Commits

Create a working branch off your main feature branch. Each TDD phase gets its own commit:

```bash
# Main feature branch
git checkout -b feature/my-feature

# Create working branch for TDD iterations
git checkout -b feature/my-feature/work

# Red phase: write failing test, commit
# (test fails)
git commit -m "test(red): add test for [behavior]"

# Green phase: write minimal implementation, commit
# (test passes)
git commit -m "feat(green): implement [behavior] minimally"

# Refactor phase: improve code, commit
# (test still passes)
git commit -m "refactor: improve [aspect of code]"

# When complete, squash merge into feature branch
git checkout feature/my-feature
git merge --squash feature/my-feature/work
git commit -m "feat: [complete feature description]"
```

**Result**: 
- Working branch shows Red-Green-Refactor process (visible history for learning/review)
- Feature branch shows one clean commit per feature (clean for PR)
- Main branch sees only final merged features (clean history)

## Test Guidelines

Every test must have:
- **Docstring**: `"""Should [expected behavior]."""`
- **Gherkin comments**: `# Given`, `# When`, `# Then`
- **Imports**: `from vtt.main import VideoTranscriber`
- **Type hints**: On all functions

Example:
```python
def test_chunking_respects_minutes(self) -> None:
    """Should round chunk duration down to complete minutes."""
    # Given a 50MB file with 600s duration
    # When calculating chunk params
    num_chunks, duration = transcriber.calculate_chunk_params(50, 600)
    # Then duration is multiple of 60
    assert duration % 60 == 0
```

## Mocking Rules

- **Only mock external APIs & slow I/O**: OpenAI, moviepy file ops, filesystem
- **Prefer real implementations** for testable logic
- **Patch path**: Always use `patch("vtt.main.OpenAI")`, etc.
- **Type ignores**: Use `# type: ignore[...]` only for test doubles, never to suppress real errors

```python
with patch("vtt.main.OpenAI"):
    transcriber = VideoTranscriber("key")
```

## Test Organization

- `tests/test_main.py` — VideoTranscriber class, CLI entrypoint, formatting
- `tests/test_audio_management.py` — Audio extraction, chunking, file cleanup

## Key Commands

```bash
make test                    # Full suite with coverage
make lint                    # ruff + mypy (required before PR)
make format                  # Auto-fix formatting
uv run pytest tests/test_main.py::TestClass::test_name -v  # Single test
```

## Hard Rules

- Never commit code with broken tests
- Always run `make lint` and `make test` before PR
- Mock only where necessary; test real code when possible
