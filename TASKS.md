# VTT-Transcribe PyPI Publishing Implementation Tasks

## T000: Project Setup & Infrastructure
- [x] T000_000: Create Dockerfile with GitHub CLI (gh) and uv
- [x] T000_001: Setup copilot worktree in .copilot-worktrees/ (gitignored but git-tracked)
- [ ] T000_002: Verify git worktree workflow (commit, push, PR from worktree)

## T005: GitHub CLI & Task Management Integration
- [x] T005_000: Authenticate gh CLI in container (gh auth login)
- [x] T005_001: Verify gh CLI can access vtt-transcribe repository
- [ ] T005_002: Create GitHub issues for all tasks in this file
- [ ] T005_003: Add issues to vtt-transcribe GitHub project board
- [ ] T005_004: Create automation script to sync TASKS.md ↔ GitHub issues
- [ ] T005_005: Setup task status tracking (open/in-progress/done)
- [ ] T005_006: Link tasks to commits (reference task numbers in commit messages)
- [ ] T005_007: Create script to auto-close issues when tasks marked done

## T010: Package Naming & Structure
- [x] T010_000: Update pyproject.toml project name to "vtt-transcribe"
- [x] T010_001: Add Hatch build system to pyproject.toml
- [x] T010_002: Update entry point to use "vtt_transcribe.main:main"
- [x] T010_003: Rename source directory: vtt/ → vtt_transcribe/
- [x] T010_004: Update all internal imports from "vtt." to "vtt_transcribe."
- [x] T010_005: Update test imports from "vtt." to "vtt_transcribe."
- [x] T010_006: Search/verify no remaining "from vtt." or "import vtt." references

## T020: Build System Configuration
- [x] T020_000: Add pyproject.toml [tool.hatch] configuration
- [x] T020_001: Configure package discovery (include vtt_transcribe/)
- [x] T020_002: Test local build with: uv run python -m build
- [x] T020_003: Verify sdist and wheel in dist/ contain correct package name
- [x] T020_004: Test local install: pip install dist/*.whl
- [x] T020_005: Verify CLI works: vtt --help and uv run vtt --help

## T030: GitHub Actions Workflow
- [x] T030_000: Update .github/workflows/publish.yml to use Hatch/build
- [x] T030_001: Configure OIDC permissions for PyPI publishing
- [x] T030_002: Add environment: pypi to publish job
- [x] T030_003: Test workflow with workflow_dispatch trigger (dry-run)
- [x] T030_004: Verify package_dir: dist in pypa/gh-action-pypi-publish

## T040: Testing & Validation
- [x] - [x] - [ ] T040_000: Run existing test suite: uv run pytest
- [x] - [x] - [ ] T040_001: Add test for CLI entry point (import and execute)
- [x] - [x] - [ ] T040_002: Add test for package import: import vtt_transcribe
- [x] - [x] - [ ] T040_003: Run type checking: uv run mypy vtt_transcribe/
- [x] - [x] - [ ] T040_004: Run linting: uv run ruff check
- [x] - [x] - [ ] T040_005: Update pre-commit hooks for new package name (vtt_transcribe)
- [x] - [x] - [ ] T040_006: Verify pre-commit hooks pass
- [x] - [x] - [ ] T040_007: Test that vtt command works after local install

## T050: Documentation & Release Prep
- [x] - [x] - [ ] T050_000: Update README.md installation: pip install vtt-transcribe
- [x] - [x] - [ ] T050_001: Update README.md usage examples (vtt, uv run vtt)
- [x] - [x] - [ ] T050_002: Update CHANGELOG.md for v0.3.0b1 release
- [x] - [x] - [ ] T050_003: Update pyproject.toml version to 0.3.0b1
- [x] - [x] - [ ] T050_004: Add PyPI classifiers and project URLs to pyproject.toml
- [x] - [x] - [ ] T050_005: Review and update project description/keywords

## T060: PyPI Configuration
- [x] T060_000: Verify PyPI project "vtt-transcribe" is registered
- [ ] T060_001: Configure TestPyPI for testing releases
- [ ] T060_002: Setup GitHub repository environment "pypi" with protection rules
- [ ] T060_003: Test publish to TestPyPI first
- [ ] T060_004: Verify TestPyPI install: pip install -i https://test.pypi.org/simple/ vtt-transcribe

## T070: Release Workflow
- [ ] T070_000: Create release checklist document
- [ ] T070_001: Tag version: git tag v0.3.0b1
- [ ] T070_002: Push tags: git push origin v0.3.0b1
- [ ] T070_003: Create GitHub release (draft=false triggers publish workflow)
- [ ] T070_004: Monitor GitHub Actions publish job
- [ ] T070_005: Verify package on PyPI: https://pypi.org/project/vtt-transcribe/

## T075: Runtime Validation & Documentation
- [x] T075_000: Update all documentation for vtt-transcribe rebranding
- [x] T075_001: Add ffmpeg runtime validation for --diarize option
- [x] T075_002: Update README with new branding and installation instructions
- [x] T075_003: Document .env file support for environment variables
- [x] T075_004: Document build and publish workflows in CONTRIBUTING.md
- [x] T075_005: Update CONTRIBUTING.md with development setup
- [x] T075_006: Research and document torch/CUDA installation options

## T080: Post-Release Validation
- [ ] T080_000: Test installation from PyPI: pip install vtt-transcribe
- [ ] T080_001: Verify CLI works after PyPI install: vtt --help
- [ ] T080_002: Test uv run: uv run vtt --help (should download from PyPI)
- [ ] T080_003: Test import in fresh environment: python -c "import vtt_transcribe"
- [ ] T080_004: Check package metadata on PyPI looks correct

## T090: Merge & Cleanup
- [ ] T090_000: Commit all changes in worktree with descriptive messages
- [ ] T090_001: Push worktree branch to remote
- [ ] T090_002: Merge worktree branch to packaging/v0.3.0b1
- [ ] T090_003: Create PR from packaging/v0.3.0b1 to main
- [ ] T090_004: Review and merge PR
- [ ] T090_005: Delete merged worktree branch
- [ ] T090_006: Prune old worktrees: git worktree prune
- [ ] T090_007: Update project documentation with publishing workflow
- [ ] T090_008: Close all completed GitHub issues
- [ ] T090_009: Archive completed tasks in GitHub project

---

## Notes
- Tasks must be completed in order within each section (T005s, then T100s, then T200s, etc.)
- Complete T005 (GitHub integration) before starting T100 (package rename)
- Some tasks within a section can be done in parallel
- Run tests after each major section (T100, T200, T400)
- Commit frequently with descriptive messages referencing task numbers (e.g., "T010_003: Rename vtt/ to vtt_transcribe/")
- Push to remote worktree branch regularly for backup
- Update GitHub issues as tasks are completed
- Multi-platform testing (Linux/Mac/Windows) and multi-Python versions deferred to v0.4.0
- All tasks assigned to @copilot

## T070 - Documentation Updates

### T070_000 - Update all documentation for vtt-transcribe rebranding
**Status:** Ready
**Priority:** High
**Size:** 3
**Estimate:** 2h
**Description:** Update all .md files to reflect new package name, build system, and workflows

### T070_001 - Add ffmpeg runtime validation
**Status:** Ready
**Priority:** High
**Size:** 2
**Estimate:** 30m
**Description:** Check ffmpeg installation before diarization and provide helpful error message
**Details:**
- Check `ffmpeg` is in PATH when --diarize, --diarize-only, or --apply-diarization flags used
- Provide clear installation instructions for different platforms
- Exit gracefully with actionable error message

### T070_002 - Update README.md with new package name and features
**Status:** Ready
**Priority:** High
**Size:** 2
**Estimate:** 45m
**Details:**
- Change video_to_text → vtt-transcribe throughout
- Update installation: `pip install vtt-transcribe[diarization]`
- Update command: `vtt` instead of python script
- Add .env file support documentation
- Add build/publish workflow documentation
- Update all examples

### T070_003 - Document .env file support
**Status:** Ready
**Priority:** Medium
**Size:** 1
**Estimate:** 15m
**Details:**
- Document OPENAI_API_KEY in .env
- Document HF_TOKEN in .env
- Document DISABLE_GPU in .env
- Add .env.example file

### T070_004 - Document build and publish workflows
**Status:** Ready
**Priority:** Medium
**Size:** 2
**Estimate:** 30m
**Details:**
- Document `make build`, `make build-check`
- Document `make publish-test`, `make publish`
- Document TestPyPI vs production PyPI
- Document TWINE_USERNAME/TWINE_PASSWORD setup
- Document GitHub Actions workflows

### T070_005 - Update CONTRIBUTING.md
**Status:** Ready
**Priority:** Low
**Size:** 1
**Estimate:** 20m
**Details:**
- Update with new package name
- Add packaging/publishing guidelines
- Document TDD workflow with -work branches

### T070_006 - Research and document torch/CUDA installation
**Status:** Ready
**Priority:** Medium
**Size:** 2
**Estimate:** 1h
**Details:**
- Research: Does torch automatically detect CUDA availability?
- Research: Does pyannote.audio require special torch builds?
- Document: Should we provide cpu-only extras group?
- Consider: `pip install vtt-transcribe[diarization-cpu]` for CPU-only torch

