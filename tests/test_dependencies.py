"""Tests for dependency checks in vtt_transcribe.dependencies module."""

from unittest.mock import MagicMock, Mock, patch

import pytest


def _make_import_error(name: str, *_args, **_kwargs):  # type: ignore[no-untyped-def]
    """Helper to simulate ImportError for specific modules."""
    if name in ("torch", "pyannote.audio"):
        msg = f"No module named '{name}'"
        raise ImportError(msg)
    return Mock()


def test_check_ffmpeg_installed_when_available() -> None:
    """Test check_ffmpeg_installed() passes when ffmpeg is available."""
    from vtt_transcribe.dependencies import check_ffmpeg_installed

    with patch("vtt_transcribe.dependencies.shutil.which", return_value="/usr/bin/ffmpeg"):
        # Should not raise or exit
        check_ffmpeg_installed()


def test_check_ffmpeg_installed_when_missing() -> None:
    """Test check_ffmpeg_installed() exits when ffmpeg is not found."""
    from vtt_transcribe.dependencies import check_ffmpeg_installed

    with (
        patch("vtt_transcribe.dependencies.shutil.which", return_value=None),
        pytest.raises(SystemExit) as exc_info,
    ):
        check_ffmpeg_installed()

    assert exc_info.value.code == 1


def test_check_ffmpeg_prints_error_message() -> None:
    """Test check_ffmpeg_installed() prints helpful error message."""
    from vtt_transcribe.dependencies import check_ffmpeg_installed

    with (
        patch("vtt_transcribe.dependencies.shutil.which", return_value=None),
        patch("builtins.print") as mock_print,
        pytest.raises(SystemExit),
    ):
        check_ffmpeg_installed()

    # Verify error message was printed
    print_calls = [str(call) for call in mock_print.call_args_list]
    error_output = " ".join(print_calls)
    assert "ffmpeg is not installed" in error_output
    assert "Installation instructions" in error_output


def test_check_diarization_dependencies_when_available() -> None:
    """Test check_diarization_dependencies() passes when dependencies are available."""
    from unittest.mock import MagicMock

    from vtt_transcribe.dependencies import check_diarization_dependencies

    # Mock torch and pyannote as installed with MagicMock objects
    mock_torch = MagicMock()
    mock_pyannote_audio = MagicMock()

    with patch.dict("sys.modules", {"torch": mock_torch, "pyannote.audio": mock_pyannote_audio, "pyannote": MagicMock()}):
        # Should not raise or exit
        check_diarization_dependencies()


def test_check_diarization_dependencies_when_missing() -> None:
    """Test check_diarization_dependencies() exits when dependencies are not found."""
    from vtt_transcribe.dependencies import check_diarization_dependencies

    with (
        patch("builtins.__import__", side_effect=_make_import_error),
        pytest.raises(SystemExit) as exc_info,
    ):
        check_diarization_dependencies()

    assert exc_info.value.code == 1


def test_check_diarization_dependencies_prints_error_message() -> None:
    """Test check_diarization_dependencies() prints helpful error message."""
    # Skip if diarization dependencies are actually installed
    try:
        import pyannote.audio  # noqa: F401
        import torch  # noqa: F401

        pytest.skip("Diarization dependencies installed, cannot test error message")
    except ImportError:
        pass

    from vtt_transcribe.dependencies import check_diarization_dependencies

    with (
        patch("builtins.__import__", side_effect=_make_import_error),
        patch("builtins.print") as mock_print,
        pytest.raises(SystemExit),
    ):
        check_diarization_dependencies()

    # Verify error message was printed
    print_calls = [str(call) for call in mock_print.call_args_list]
    error_output = " ".join(print_calls)
    assert "Diarization dependencies not installed" in error_output
    assert "pip install vtt-transcribe[diarization]" in error_output


def test_check_diarization_dependencies_handles_torch_missing() -> None:
    """Test that missing torch is caught."""
    from vtt_transcribe.dependencies import check_diarization_dependencies

    def import_error_torch(name: str, *_args, **_kwargs):  # type: ignore[no-untyped-def]
        if name == "torch":
            msg = "No module named 'torch'"
            raise ImportError(msg)
        return Mock()

    with (
        patch("builtins.__import__", side_effect=import_error_torch),
        pytest.raises(SystemExit) as exc_info,
    ):
        check_diarization_dependencies()
    assert exc_info.value.code == 1


def test_check_diarization_dependencies_handles_pyannote_missing() -> None:
    """Test that missing pyannote.audio is caught."""
    from vtt_transcribe.dependencies import check_diarization_dependencies

    def import_error_pyannote(name: str, *_args, **_kwargs):  # type: ignore[no-untyped-def]
        if name == "pyannote.audio":
            msg = "No module named 'pyannote.audio'"
            raise ImportError(msg)
        # Return mock torch to pass first import
        if name == "torch":
            return MagicMock()
        return Mock()

    with (
        patch("builtins.__import__", side_effect=import_error_pyannote),
        pytest.raises(SystemExit) as exc_info,
    ):
        check_diarization_dependencies()
    assert exc_info.value.code == 1
