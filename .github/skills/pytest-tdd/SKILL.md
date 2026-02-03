---
name: pytest-tdd
description: Implements features using strict Red-Green-Refactor cycle with Pytest. Write the failing test first, then minimal implementation, then refactor.
tools: ["edit", "terminal"]
---

# Pytest TDD

Follow Red-Green-Refactor for every feature. Never write implementation without a failing test first.

## Simplified Workflow

### Branch Structure
For any current branch (e.g., `feature/my-feature`), create a working branch:
```bash
# Main feature branch
git checkout -b feature/my-feature

# Create working branch for TDD iterations
git checkout -b feature/my-feature-work
```

### TDD Cycle on `-work` Branch

**Each cycle gets 3 commits** in the order of smallest incremental change:

1. **Red Phase** (test, fail, commit)
   ```bash
   # Write failing test
   git commit -m "test(red): add test for [behavior]"
   make test  # Should fail
   ```

2. **Green Phase** (test, pass, commit)
   ```bash
   # Write minimal implementation
   git commit -m "feat(green): implement [behavior] minimally"
   make test  # Should pass
   ```

3. **Refactor Phase** (test, pass, commit)
   ```bash
   # Improve code (always improve something, even if unrelated to current task)
   git commit -m "refactor: improve [aspect of code]"
   make test  # Should still pass
   ```

### Merge Back to Feature Branch

After completing the full Red-Green-Refactor cycle:
```bash
git checkout feature/my-feature
git merge --squash feature/my-feature-work
git commit -m "feat: [complete feature description]"
git branch -d feature/my-feature-work
```

**Result:**
- `-work` branch shows Red-Green-Refactor process (detailed history)
- Feature branch shows one atomic commit per feature (clean for PR)
- Main branch sees only final merged features (clean history)

## Test Guidelines

Every test must have:
- **Docstring**: `"""Should [expected behavior]."""`
- **Type hints**: On all functions

Example:
```python
def test_chunking_respects_minutes(self) -> None:
    """Should round chunk duration down to complete minutes."""
    # Given a 50MB file with 600s duration
    num_chunks, duration = transcriber.calculate_chunk_params(50, 600)
    # When/Then: duration is multiple of 60
    assert duration % 60 == 0
```

## Mocking Rules

- **Only mock external APIs & slow I/O**: OpenAI, moviepy file ops, filesystem
- **Prefer real implementations** for testable logic
- **Patch path**: Always use `patch("vtt.main.OpenAI")`, etc.
- **Type ignores**: Use `# type: ignore[...]` only for test doubles

## Key Commands

```bash
make test                    # Full suite with coverage
make lint                    # ruff + mypy (required before PR)
make format                  # Auto-fix formatting
uv run pytest tests/test_main.py::TestClass::test_name -v  # Single test
```

## Hard Rules

- Never commit code with broken tests for squash merge commit
- Always run `make lint` and `make test` before merging to feature branch
- Mock only where necessary; test real code when possible
- Refactor phase **must** improve something (code quality, naming, organization, etc.)
