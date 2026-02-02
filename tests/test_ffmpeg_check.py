"""Tests for ffmpeg installation check."""

from unittest.mock import MagicMock, patch

import pytest


def test_check_ffmpeg_installed_when_available() -> None:
    """Test check_ffmpeg_installed() passes when ffmpeg is available."""
    from vtt_transcribe.health import check_ffmpeg_installed

    # Simulate ffmpeg being installed by mocking shutil.which to return a path
    with patch("vtt_transcribe.health.shutil.which", return_value="/usr/bin/ffmpeg"):
        # This should not raise
        check_ffmpeg_installed()


def test_check_ffmpeg_installed_when_missing() -> None:
    """Test check_ffmpeg_installed() exits with helpful message when ffmpeg missing."""
    from vtt_transcribe.health import check_ffmpeg_installed

    with patch("vtt_transcribe.health.shutil.which", return_value=None):
        with pytest.raises(SystemExit) as exc_info:
            check_ffmpeg_installed()

        assert exc_info.value.code == 1


def test_speaker_diarizer_checks_ffmpeg() -> None:
    """Test that ffmpeg check is done at CLI startup, not in SpeakerDiarizer."""
    # Mock torch and pyannote imports to avoid dependency
    # Both pyannote and pyannote.audio must be mocked for Python's import machinery
    with patch.dict("sys.modules", {"torch": MagicMock(), "pyannote": MagicMock(), "pyannote.audio": MagicMock()}):
        from vtt_transcribe.diarization import SpeakerDiarizer

        # SpeakerDiarizer should no longer check for ffmpeg - that's done at CLI startup
        with patch.dict("os.environ", {"HF_TOKEN": "test_token"}):
            # This should NOT raise since the check was moved to main.py
            diarizer = SpeakerDiarizer(hf_token="test_token")  # noqa: S106
            assert diarizer is not None
