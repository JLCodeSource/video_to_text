"""Tests for package structure and entry points."""

import subprocess
import sys


def test_vtt_transcribe_package_import() -> None:
    """Test that vtt_transcribe package can be imported."""
    import vtt_transcribe

    assert vtt_transcribe is not None
    assert hasattr(vtt_transcribe, "__version__")
    version = vtt_transcribe.__version__
    assert isinstance(version, str)
    assert version != ""


def test_vtt_cli_entry_point_exists() -> None:
    """Test that vtt CLI command is available."""
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-m", "vtt_transcribe.main", "--help"],
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )

    assert result.returncode == 0
    assert "usage: vtt" in result.stdout or "Transcribe" in result.stdout


def test_vtt_command_via_entry_point() -> None:
    """Test that 'vtt' command exists as entry point."""
    # This tests the entry point defined in pyproject.toml
    import_code = (
        "from importlib.metadata import entry_points; "
        "eps = entry_points(); "
        "print([ep for ep in eps.select(group='console_scripts') if ep.name == 'vtt'])"
    )
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-c", import_code],
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )

    assert result.returncode == 0
    assert "vtt" in result.stdout
