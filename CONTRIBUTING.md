# Contributing to vtt-transcribe

Thank you for your interest in contributing to vtt-transcribe! This document provides guidelines and instructions for development.

## Development Setup

### Prerequisites

- Python 3.13+
- ffmpeg installed on your system
- Git

### Recommended: Using Dev Container

The easiest way to get started is using the provided dev container:

1. Install Docker and VS Code with the "Dev Containers" extension
2. Open the project in VS Code
3. Click "Reopen in Container" when prompted
4. The container includes ffmpeg, GPU support, and all dependencies pre-configured

### Manual Setup

If not using the dev container:

1. **Install ffmpeg:**
   - Ubuntu/Debian: `sudo apt-get install ffmpeg`
   - macOS: `brew install ffmpeg`
   - Windows: Download from https://ffmpeg.org/download.html

2. **Install dependencies:**
   ```bash
   # Basic installation (transcription only)
   make install
   
   # OR: With diarization support (recommended for development)
   make install-diarization
   ```

3. **Setup environment variables:**
   Create a `.env` file in the project root:
   ```bash
   OPENAI_API_KEY="your-openai-api-key"
   HF_TOKEN="your-huggingface-token"  # Required for diarization features
   ```

4. **Install pre-commit hooks:**
   ```bash
   uv run pre-commit install
   ```

### GPU Support for Diarization

Speaker diarization can leverage CUDA GPUs for 10-100x speedup over CPU processing.

**PyTorch and CUDA:**
- The `torch>=2.1.0` dependency will install the CPU-only version by default
- PyTorch automatically detects CUDA availability at runtime
- If CUDA is available, PyTorch will use it; otherwise, it falls back to CPU
- No separate installation is needed - the same torch package works for both CPU and GPU

**To verify GPU support:**
```bash
# Check if CUDA is available
uv run python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"

# Check CUDA version
uv run python -c "import torch; print(f'CUDA version: {torch.version.cuda}')"
```

**Dev Container GPU Support:**
- The `.devcontainer` is configured for GPU passthrough
- Requires NVIDIA GPU + drivers on host
- Requires `nvidia-container-toolkit` on host
- GPU is automatically used when available

**Manual GPU Setup:**
- Ensure NVIDIA GPU drivers are installed
- For Docker/containers: Install `nvidia-container-toolkit`
- The application uses `--device auto` by default (auto-detects CUDA)
- Override with `--device cuda` or `--device cpu` if needed

## Development Workflow

### Running Tests

```bash
# Run all tests
make test

# Run only integration tests
make test-integration

# Run tests with coverage
uv run pytest --cov=vtt_transcribe --cov-report=html
```

### Code Quality

We use `ruff` for linting/formatting and `mypy` for type checking:

```bash
# Format code
make format

# Check linting
make lint

# Or run individually:
make ruff-check
make mypy
```

**Important:** Always run `make format` and `make lint` before committing.

### Pre-commit Hooks

The project uses pre-commit hooks to ensure code quality:

- `make format` - Auto-formats code with ruff
- `make lint` - Runs ruff check and mypy

These run automatically on `git commit`. To bypass (not recommended): `git commit --no-verify`

### Test-Driven Development (TDD)

We follow TDD practices:

1. **RED:** Write a failing test
   ```bash
   # Run test to confirm it fails
   uv run pytest tests/test_feature.py -v
   # Commit the failing test
   git commit -m "test: add failing test for feature X"
   ```

2. **GREEN:** Implement minimum code to pass
   ```bash
   # Implement feature
   # Run test to confirm it passes
   uv run pytest tests/test_feature.py -v
   # Commit the implementation
   git commit -m "feat: implement feature X"
   ```

3. **REFACTOR:** Improve code quality
   ```bash
   # Refactor code
   # Run tests to ensure nothing broke
   make test
   # Commit refactoring
   git commit -m "refactor: improve feature X implementation"
   ```

4. **Squash commits:** Combine RED-GREEN-REFACTOR into atomic commit
   ```bash
   git rebase -i HEAD~3  # Squash last 3 commits
   ```

## Building and Publishing

### Local Build

```bash
# Install build dependencies
make install-build

# Build distribution packages
make build

# Output: dist/vtt_transcribe-{version}-py3-none-any.whl
#         dist/vtt_transcribe-{version}.tar.gz
```

### Testing with TestPyPI

Before publishing to production PyPI, test with TestPyPI:

```bash
# Set TestPyPI credentials in .env (automatically loaded by make targets)
echo 'TWINE_USERNAME="__token__"' >> .env
echo 'TWINE_PASSWORD="your-testpypi-token"' >> .env
echo 'TWINE_REPOSITORY="testpypi"' >> .env

# Source environment to verify
source .env

# Upload to TestPyPI
make publish-test

# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ vtt-transcribe
```

**Note:** The `.env` file will be automatically loaded by Python's `dotenv`, so credentials are available to `twine` without manual export.

### Production Publishing

Production releases are automated via GitHub Actions:

1. **Update version** in `pyproject.toml`
2. **Update CHANGELOG.md** with release notes
3. **Commit and push changes**
   ```bash
   git add pyproject.toml CHANGELOG.md
   git commit -m "chore: bump version to v0.3.0"
   git push
   ```

4. **Create and push tag:**
   ```bash
   git tag v0.3.0
   git push origin v0.3.0
   ```

5. **Create GitHub Release:**
   - Go to GitHub repository → Releases → "Draft a new release"
   - Select the tag you just created
   - Add release notes (copy from CHANGELOG.md)
   - Publish release

6. **Automated workflow:**
   - GitHub Actions automatically builds and publishes to PyPI
   - Monitor workflow at: Actions tab → "Publish to PyPI"

### GitHub Actions Workflows

- **CI (`ci.yml`):** Runs on every push/PR to main
  - Installs dependencies
  - Runs linting (`make lint`)
  - Runs tests (`make test`)

- **Publish (`publish.yml`):** Runs on GitHub release creation
  - Builds package with Hatch
  - Publishes to PyPI using trusted publishing (OIDC)

## Project Structure

```
vtt-transcribe/
├── vtt_transcribe/          # Main package
│   ├── __init__.py
│   ├── main.py              # CLI entry point
│   ├── diarization.py       # Speaker diarization
│   ├── audio_management.py  # Audio extraction/chunking
│   └── formatter.py         # Transcript formatting
├── tests/                   # Test suite
│   ├── test_main.py
│   ├── test_diarization.py
│   └── ...
├── .github/workflows/       # GitHub Actions
├── .devcontainer/           # Dev container configuration
├── pyproject.toml           # Package metadata and dependencies
├── Makefile                 # Development commands
└── CONTRIBUTING.md          # This file
```

## Making Changes

### Branch Naming

- Feature branches: `feature/description`
- Bug fixes: `fix/description`
- Documentation: `docs/description`
- Releases: `packaging/v0.3.0b1`

### Commit Message Format

We use conventional commits:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Adding/updating tests
- `refactor`: Code refactoring
- `chore`: Maintenance tasks
- `ci`: CI/CD changes

**Examples:**
```
feat(diarization): add ffmpeg validation check
fix(cli): handle missing environment variables gracefully
docs(readme): update installation instructions
test(formatter): add tests for timestamp conversion
```

### Pull Request Process

1. Create a feature branch from `main`
2. Make your changes following TDD workflow
3. Ensure all tests pass: `make test`
4. Ensure linting passes: `make lint`
5. Update documentation if needed
6. Push your branch and create a Pull Request
7. Wait for CI checks to pass
8. Address review feedback
9. Once approved, maintainer will merge

## Code Style

- Follow PEP 8 (enforced by ruff)
- Use type hints (checked by mypy)
- Write docstrings for public functions/classes
- Keep functions focused and testable
- Prefer explicit over implicit
- Write tests for new features

## Getting Help

- **Issues:** Check existing issues or create a new one
- **Discussions:** Use GitHub Discussions for questions
- **Documentation:** See README.md and code docstrings

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.
