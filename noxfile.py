import nox

# Default sessions
nox.options.sessions = ["tests", "lint"]


@nox.session(python=["3.10", "3.11", "3.12", "3.13"])
def tests(session: nox.Session) -> None:
    """Run the test suite in multiple Python versions.

    Installs the package in editable mode with dev and diarization extras and runs pytest.
    """
    session.install("pip>=23.0")
    # Install package with development and diarization extras
    session.install(".[dev,diarization]")
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
