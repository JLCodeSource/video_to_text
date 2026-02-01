# VTT-Transcribe PyPI Publishing Implementation Tasks

## T000: Project Setup & Infrastructure
- [x] T000: Create Dockerfile with GitHub CLI (gh) and uv
- [x] T001: Setup copilot worktree in .copilot-worktrees/ (gitignored but git-tracked)
- [ ] T002: Verify git worktree workflow (commit, push, PR from worktree)

## T050: GitHub CLI & Task Management Integration
- [ ] T050: Authenticate gh CLI in container (gh auth login)
- [ ] T051: Verify gh CLI can access vtt-transcribe repository
- [ ] T052: Create GitHub issues for all tasks in this file
- [ ] T053: Add issues to vtt-transcribe GitHub project board
- [ ] T054: Create automation script to sync TASKS.md ↔ GitHub issues
- [ ] T055: Setup task status tracking (open/in-progress/done)
- [ ] T056: Link tasks to commits (reference task numbers in commit messages)
- [ ] T057: Create script to auto-close issues when tasks marked done

## T100: Package Naming & Structure
- [ ] T100: Update pyproject.toml project name to "vtt-transcribe"
- [ ] T101: Add Hatch build system to pyproject.toml
- [ ] T102: Update entry point to use "vtt_transcribe.main:main"
- [ ] T103: Rename source directory: vtt/ → vtt_transcribe/
- [ ] T104: Update all internal imports from "vtt." to "vtt_transcribe."
- [ ] T105: Update test imports from "vtt." to "vtt_transcribe."
- [ ] T106: Search/verify no remaining "from vtt." or "import vtt." references

## T200: Build System Configuration
- [ ] T200: Add pyproject.toml [tool.hatch] configuration
- [ ] T201: Configure package discovery (include vtt_transcribe/)
- [ ] T202: Test local build with: uv run python -m build
- [ ] T203: Verify sdist and wheel in dist/ contain correct package name
- [ ] T204: Test local install: pip install dist/*.whl
- [ ] T205: Verify CLI works: vtt --help and uv run vtt --help

## T300: GitHub Actions Workflow
- [ ] T300: Update .github/workflows/publish.yml to use Hatch/build
- [ ] T301: Configure OIDC permissions for PyPI publishing
- [ ] T302: Add environment: pypi to publish job
- [ ] T303: Test workflow with workflow_dispatch trigger (dry-run)
- [ ] T304: Verify package_dir: dist in pypa/gh-action-pypi-publish

## T400: Testing & Validation
- [ ] T400: Run existing test suite: uv run pytest
- [ ] T401: Add test for CLI entry point (import and execute)
- [ ] T402: Add test for package import: import vtt_transcribe
- [ ] T403: Run type checking: uv run mypy vtt_transcribe/
- [ ] T404: Run linting: uv run ruff check
- [ ] T405: Update pre-commit hooks for new package name (vtt_transcribe)
- [ ] T406: Verify pre-commit hooks pass
- [ ] T407: Test that vtt command works after local install

## T500: Documentation & Release Prep
- [ ] T500: Update README.md installation: pip install vtt-transcribe
- [ ] T501: Update README.md usage examples (vtt, uv run vtt)
- [ ] T502: Update CHANGELOG.md for v0.3.0b1 release
- [ ] T503: Update pyproject.toml version to 0.3.0b1
- [ ] T504: Add PyPI classifiers and project URLs to pyproject.toml
- [ ] T505: Review and update project description/keywords

## T600: PyPI Configuration
- [ ] T600: Verify PyPI project "vtt-transcribe" is registered
- [ ] T601: Configure TestPyPI for testing releases
- [ ] T602: Setup GitHub repository environment "pypi" with protection rules
- [ ] T603: Test publish to TestPyPI first
- [ ] T604: Verify TestPyPI install: pip install -i https://test.pypi.org/simple/ vtt-transcribe

## T700: Release Workflow
- [ ] T700: Create release checklist document
- [ ] T701: Tag version: git tag v0.3.0b1
- [ ] T702: Push tags: git push origin v0.3.0b1
- [ ] T703: Create GitHub release (draft=false triggers publish workflow)
- [ ] T704: Monitor GitHub Actions publish job
- [ ] T705: Verify package on PyPI: https://pypi.org/project/vtt-transcribe/

## T800: Post-Release Validation
- [ ] T800: Test installation from PyPI: pip install vtt-transcribe
- [ ] T801: Verify CLI works after PyPI install: vtt --help
- [ ] T802: Test uv run: uv run vtt --help (should download from PyPI)
- [ ] T803: Test import in fresh environment: python -c "import vtt_transcribe"
- [ ] T804: Check package metadata on PyPI looks correct

## T900: Merge & Cleanup
- [ ] T900: Commit all changes in worktree with descriptive messages
- [ ] T901: Push worktree branch to remote
- [ ] T902: Merge worktree branch to packaging/v0.3.0b1
- [ ] T903: Create PR from packaging/v0.3.0b1 to main
- [ ] T904: Review and merge PR
- [ ] T905: Delete merged worktree branch
- [ ] T906: Prune old worktrees: git worktree prune
- [ ] T907: Update project documentation with publishing workflow
- [ ] T908: Close all completed GitHub issues
- [ ] T909: Archive completed tasks in GitHub project

---

## Notes
- Tasks must be completed in order within each section (T050s, then T100s, then T200s, etc.)
- Complete T050 (GitHub integration) before starting T100 (package rename)
- Some tasks within a section can be done in parallel
- Run tests after each major section (T100, T200, T400)
- Commit frequently with descriptive messages referencing task numbers (e.g., "T103: Rename vtt/ to vtt_transcribe/")
- Push to remote worktree branch regularly for backup
- Update GitHub issues as tasks are completed
- Multi-platform testing (Linux/Mac/Windows) and multi-Python versions deferred to v0.4.0
