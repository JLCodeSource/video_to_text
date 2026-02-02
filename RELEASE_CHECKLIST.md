# Release Checklist for vtt-transcribe

## Pre-Release Validation

### Code Quality
- [ ] All tests passing: `uv run pytest`
- [ ] Type checking clean: `uv run mypy vtt_transcribe/`
- [ ] Linting clean: `uv run ruff check`
- [ ] Pre-commit hooks passing
- [ ] Code coverage ≥ 95%
- [ ] Test coverage 100% on all vtt_transcribe files

### Documentation
- [ ] README.md updated with correct version
- [ ] CHANGELOG.md updated with release notes
- [ ] Installation instructions verified
- [ ] Usage examples tested
- [ ] API documentation current

### Package Configuration
- [ ] pyproject.toml version bumped
- [ ] Package name correct: `vtt-transcribe`
- [ ] Entry points configured: `vtt`
- [ ] Dependencies up to date
- [ ] Python version requirement verified (>=3.13)

### Build & Test
- [ ] Local build successful: `uv run python -m build`
- [ ] Package structure verified
- [ ] Wheel and sdist created
- [ ] Local install test: `pip install dist/*.whl`
- [ ] CLI works after install: `vtt --help`

## PyPI Configuration

### Environments
- [ ] GitHub environment "pypi" configured with protection rules
- [ ] OIDC Trusted Publisher configured for PyPI
- [ ] (Optional) TestPyPI environment for testing

### Workflow
- [ ] `.github/workflows/publish.yml` configured
- [ ] OIDC permissions set correctly
- [ ] Workflow tested with `workflow_dispatch` (dry-run)

## Release Process

### 1. Create Tag
```bash
git tag v0.3.0b1
git tag -n  # Verify tag
```

### 2. Push Tag
```bash
git push origin v0.3.0b1
```

### 3. Create GitHub Release
1. Go to https://github.com/JLCodeSource/vtt-transcribe/releases/new
2. Select tag: v0.3.0b1
3. Release title: "v0.3.0b1 - PyPI Package Release"
4. Description: Copy from CHANGELOG.md
5. Mark as pre-release (beta)
6. Publish release (triggers workflow)

### 4. Monitor GitHub Actions
1. Go to https://github.com/JLCodeSource/vtt-transcribe/actions
2. Watch "Publish to PyPI" workflow
3. Verify all steps complete successfully
4. Check for any errors in logs

### 5. Verify PyPI Publication
- [ ] Package visible at: https://pypi.org/project/vtt-transcribe/
- [ ] Version 0.3.0b1 listed
- [ ] Metadata correct (description, classifiers, URLs)
- [ ] README rendering properly

## Post-Release Validation

### Installation Testing
- [ ] Test pip install: `pip install vtt-transcribe`
- [ ] Test uv run: `uv run vtt --help`
- [ ] Verify CLI works: `vtt --version`
- [ ] Test in fresh virtual environment
- [ ] Test import: `python -c "import vtt_transcribe"`

### Functionality Testing
- [ ] Run sample transcription
- [ ] Verify output format
- [ ] Check error handling
- [ ] Test main features work

### Documentation Verification
- [ ] PyPI page looks correct
- [ ] Links work (homepage, repository, issues)
- [ ] README displays properly
- [ ] Classifiers appropriate

## Cleanup & Next Steps

### Branch Management
- [ ] Commit all changes
- [ ] Push worktree branch
- [ ] Merge to packaging/v0.3.0b1
- [ ] Create PR to main
- [ ] Review and merge PR
- [ ] Delete worktree branch
- [ ] Prune old worktrees

### Issue Management
- [ ] Close completed GitHub issues
- [ ] Archive completed tasks in project
- [ ] Update project board

### Documentation
- [ ] Update main README with PyPI install
- [ ] Document release process for future
- [ ] Note any lessons learned

## Rollback Plan

If something goes wrong:

1. **Before Publishing**: Simply don't create the GitHub release
2. **After Publishing**: 
   - Cannot delete PyPI releases
   - Publish a patch version (v0.3.0b2) with fixes
   - Mark problematic version as "yanked" on PyPI if critical

## Notes

- First PyPI release: v0.3.0b1 (beta)
- Package name: `vtt-transcribe`
- Import name: `vtt_transcribe`
- CLI command: `vtt`
- Python requirement: >=3.13
- OIDC publishing (no API tokens needed)

