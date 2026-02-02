"""Tests for diarization import handling."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from vtt_transcribe.main import main


class TestDiarizationImportHandling:
    """Test handling of missing diarization dependencies."""

    def test_diarize_flag_without_dependencies_shows_error(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        """Should show error when --diarize is used without diarization dependencies."""
        # Create a dummy audio file
        audio_file = tmp_path / "test.mp3"
        audio_file.write_text("dummy audio")

        # Mock the transcription to succeed so we can test diarization import failure
        with (
            patch("vtt_transcribe.transcriber.VideoTranscriber") as mock_transcriber,
            patch.dict(sys.modules, {"vtt_transcribe.diarization": None}),
            patch("sys.argv", ["vtt", str(audio_file), "--diarize"]),
            patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}),
            pytest.raises(SystemExit) as exc_info,
        ):
            # Mock transcription to return a dummy transcript
            mock_transcriber.return_value.transcribe.return_value = "dummy transcript"
            main()

        # Should exit with error
        assert exc_info.value.code == 1

        # Capture stderr to check error message
        captured = capsys.readouterr()
        assert "Diarization dependencies not installed" in captured.err or "Diarization dependencies not installed" in str(exc_info.value)

    def test_diarize_only_without_dependencies_shows_error(self, tmp_path: Path) -> None:
        """Should show error when --diarize-only is used without diarization dependencies."""
        audio_file = tmp_path / "test.mp3"
        audio_file.write_text("dummy audio")

        with (
            patch.dict(sys.modules, {"vtt_transcribe.diarization": None}),
            patch("sys.argv", ["vtt", str(audio_file), "--diarize-only"]),
            pytest.raises(SystemExit) as exc_info,
        ):
            main()

        assert exc_info.value.code == 1

    def test_apply_diarization_without_dependencies_shows_error(self, tmp_path: Path) -> None:
        """Should show error when --apply-diarization is used without diarization dependencies."""
        audio_file = tmp_path / "test.mp3"
        audio_file.write_text("dummy audio")
        transcript_file = tmp_path / "transcript.txt"
        transcript_file.write_text("dummy transcript")

        with (
            patch.dict(sys.modules, {"vtt_transcribe.diarization": None}),
            patch("sys.argv", ["vtt", str(audio_file), "--apply-diarization", str(transcript_file)]),
            pytest.raises(SystemExit) as exc_info,
        ):
            main()

        assert exc_info.value.code == 1
