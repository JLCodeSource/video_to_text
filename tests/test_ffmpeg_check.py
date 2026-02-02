"""Tests for ffmpeg installation check."""

from unittest.mock import MagicMock, patch

import pytest


def test_check_ffmpeg_installed_when_available() -> None:
    """Test check_ffmpeg_installed() passes when ffmpeg is available."""
    # Mock torch import to avoid dependency
    with patch.dict("sys.modules", {"torch": MagicMock(), "pyannote.audio": MagicMock()}):
        from vtt_transcribe.diarization import check_ffmpeg_installed

        # Simulate ffmpeg being installed by mocking shutil.which to return a path
        with patch("vtt_transcribe.diarization.shutil.which", return_value="/usr/bin/ffmpeg"):
            # This should not raise
            check_ffmpeg_installed()


def test_check_ffmpeg_installed_when_missing() -> None:
    """Test check_ffmpeg_installed() exits with helpful message when ffmpeg missing."""
    # Mock torch import to avoid dependency
    with patch.dict("sys.modules", {"torch": MagicMock(), "pyannote.audio": MagicMock()}):
        from vtt_transcribe.diarization import check_ffmpeg_installed

        with patch("vtt_transcribe.diarization.shutil.which", return_value=None):
            with pytest.raises(SystemExit) as exc_info:
                check_ffmpeg_installed()

            assert exc_info.value.code == 1


def test_speaker_diarizer_checks_ffmpeg() -> None:
    """Test SpeakerDiarizer.__init__() checks for ffmpeg."""
    # Mock torch import to avoid dependency
    with patch.dict("sys.modules", {"torch": MagicMock(), "pyannote.audio": MagicMock()}):
        from vtt_transcribe.diarization import SpeakerDiarizer

        with (
            patch("vtt_transcribe.diarization.shutil.which", return_value=None),
            patch.dict("os.environ", {"HF_TOKEN": "test_token"}),
            pytest.raises(SystemExit) as exc_info,
        ):
            SpeakerDiarizer(hf_token="test_token")  # noqa: S106

        assert exc_info.value.code == 1
