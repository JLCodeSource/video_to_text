import nox

# Default sessions
nox.options.sessions = ["tests", "lint"]


@nox.session(python=["3.10", "3.11", "3.12", "3.13"])
def tests(session: nox.Session) -> None:
    """Run the test suite with diarization support (Python 3.10-3.13).

    Installs the package in editable mode with dev and diarization extras and runs pytest.
    Diarization extras (torch) have prebuilt wheels only up to Python 3.13.
    """
    session.install("pip>=23.0")
    # Install package with development and diarization extras
    session.install(".[dev,diarization]")
    # Run tests
    session.run("pytest", "-q")


@nox.session(python=["3.14"])
def tests_core(session: nox.Session) -> None:
    """Run core tests only for Python 3.14 (without diarization).

    Python 3.14 does not have prebuilt torch wheels yet, so we test only
    the core functionality without diarization extras.
    """
    session.install("pip>=23.0")
    # Install package with development extras only (no diarization)
    session.install(".[dev]")
    # Run tests
    session.run("pytest", "-q")


@nox.session(python=["3.10"])
def lint(session: nox.Session) -> None:
    """Run linters/formatters (ruff, mypy) on earliest supported Python version."""
    session.install("pip>=23.0")
    session.install(".[dev]")
    # Run ruff
    session.run("ruff", "check", ".")
    # Run mypy with strict type checking
    session.run(
        "mypy",
        ".",
        "--ignore-missing-imports",
        "--disallow-untyped-defs",
        "--disallow-incomplete-defs",
        "--check-untyped-defs",
        "--warn-unused-ignores",
        "--warn-redundant-casts",
    )
