"""Tests for version handling."""

import subprocess
import sys
from importlib.metadata import PackageNotFoundError
from unittest.mock import patch


def test_version_when_package_installed() -> None:
    """Should retrieve version from package metadata when installed."""
    import vtt_transcribe

    # When installed normally, __version__ should be a valid version string
    assert vtt_transcribe.__version__ is not None
    assert isinstance(vtt_transcribe.__version__, str)


def test_version_when_package_not_found() -> None:
    """Should fall back to 'unknown' when package not found."""
    # Mock the version function to raise PackageNotFoundError
    with patch("importlib.metadata.version", side_effect=PackageNotFoundError):
        # Force re-import to trigger the except block
        import importlib

        import vtt_transcribe

        importlib.reload(vtt_transcribe)

        assert vtt_transcribe.__version__ == "unknown"


def test_version_flag_long() -> None:
    """Should display version with --version flag."""
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-m", "vtt_transcribe.main", "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    # Check that version is displayed (should be in format "program version" with version containing dots or "unknown")
    output_parts = result.stdout.strip().split()
    assert len(output_parts) == 2, f"Version output should have program name and version, got: {result.stdout.strip()}"
    version = output_parts[1]  # Second part should be the version
    assert "." in version or version == "unknown", f"Expected version format with dots or 'unknown', got: {version}"


def test_version_flag_short() -> None:
    """Should display version with -v flag."""
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-m", "vtt_transcribe.main", "-v"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    # Check that version is displayed (should be in format "program version" with version containing dots or "unknown")
    output_parts = result.stdout.strip().split()
    assert len(output_parts) == 2, f"Version output should have program name and version, got: {result.stdout.strip()}"
    version = output_parts[1]  # Second part should be the version
    assert "." in version or version == "unknown", f"Expected version format with dots or 'unknown', got: {version}"
