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
        # Simulate missing torch dependency (the actual scenario when optional deps not installed)
        with (
            patch("vtt_transcribe.transcriber.VideoTranscriber") as mock_transcriber,
            patch.dict(sys.modules, {"torch": None}),
            patch("sys.argv", ["vtt", str(audio_file), "--diarize"]),
            patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}),
        ):
            # Mock transcription to return a dummy transcript
            mock_transcriber.return_value.transcribe.return_value = "dummy transcript"

            # Should exit with error
            with pytest.raises(SystemExit) as exc_info:
                main()

        assert exc_info.value.code == 1

        # Capture output to check error message (errors print to stdout, not stderr)
        captured = capsys.readouterr()
        assert "Diarization dependencies not installed" in captured.out

    def test_diarize_only_without_dependencies_shows_error(self, tmp_path: Path) -> None:
        """Should show error when --diarize-only is used without diarization dependencies."""
        audio_file = tmp_path / "test.mp3"
        audio_file.write_text("dummy audio")

        # Simulate missing pyannote.audio dependency (the actual scenario)
        with (  # noqa: SIM117
            patch.dict(sys.modules, {"pyannote.audio": None}),
            patch("sys.argv", ["vtt", str(audio_file), "--diarize-only"]),
        ):
            with pytest.raises(SystemExit) as exc_info:
                main()

        assert exc_info.value.code == 1

    def test_apply_diarization_without_dependencies_shows_error(self, tmp_path: Path) -> None:
        """Should show error when --apply-diarization is used without diarization dependencies."""
        audio_file = tmp_path / "test.mp3"
        audio_file.write_text("dummy audio")
        transcript_file = tmp_path / "transcript.txt"
        transcript_file.write_text("dummy transcript")

        # Simulate missing torch dependency (the actual scenario)
        with (  # noqa: SIM117
            patch.dict(sys.modules, {"torch": None}),
            patch("sys.argv", ["vtt", str(audio_file), "--apply-diarization", str(transcript_file)]),
        ):
            with pytest.raises(SystemExit) as exc_info:
                main()

        assert exc_info.value.code == 1
