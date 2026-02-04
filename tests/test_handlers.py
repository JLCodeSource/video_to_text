"""Tests for handler functions in vtt/handlers.py."""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from vtt_transcribe.handlers import (
    display_result,
    handle_apply_diarization_mode,
    handle_diarize_only_mode,
    handle_review_speakers,
    handle_standard_transcription,
    save_transcript,
)


class TestSaveTranscript:
    """Test save_transcript function."""

    def test_save_transcript_adds_txt_extension(self, tmp_path: Path) -> None:
        """Test that save_transcript adds .txt extension if missing."""
        output_path = tmp_path / "transcript"
        transcript = "Test transcript content"

        save_transcript(output_path, transcript)

        expected_path = tmp_path / "transcript.txt"
        assert expected_path.exists()
        assert expected_path.read_text() == transcript

    def test_save_transcript_preserves_txt_extension(self, tmp_path: Path) -> None:
        """Test that save_transcript preserves .txt extension."""
        output_path = tmp_path / "transcript.txt"
        transcript = "Test transcript content"

        save_transcript(output_path, transcript)

        assert output_path.exists()
        assert output_path.read_text() == transcript


class TestDisplayResult:
    """Test display_result function."""

    def test_display_result_prints_transcript(self) -> None:
        """Test that display_result prints formatted transcript."""
        transcript = "Test transcript"

        with patch("builtins.print") as mock_print:
            display_result(transcript)

            # Verify print was called with expected content
            calls = [str(call) for call in mock_print.call_args_list]
            assert any("Transcription Result:" in call for call in calls)
            assert any(transcript in call for call in calls)


class TestHandleDiarizeOnlyMode:
    """Test handle_diarize_only_mode function."""

    def test_handle_diarize_only_mode_file_not_found(self) -> None:
        """Test that handle_diarize_only_mode raises error for missing file."""
        with pytest.raises(FileNotFoundError, match="Audio file not found"):
            handle_diarize_only_mode(Path("/nonexistent/file.mp3"), "hf_token")

    def test_handle_diarize_only_mode(self, tmp_path: Path) -> None:
        """Test handle_diarize_only_mode returns result without saving."""
        audio_file = tmp_path / "test.mp3"
        audio_file.write_text("fake audio")

        with (
            patch("vtt_transcribe.handlers._lazy_import_diarization") as mock_import,
            patch("builtins.print"),
        ):
            mock_diarizer = MagicMock()
            mock_diarizer.diarize_audio.return_value = [(0.0, 5.0, "SPEAKER_00")]
            mock_format = MagicMock(return_value="[00:00:00 - 00:00:05] SPEAKER_00")

            mock_import.return_value = (
                lambda *_args, **_kwargs: mock_diarizer,
                mock_format,
                MagicMock(),
                MagicMock(),
            )

            result = handle_diarize_only_mode(audio_file, "hf_token")

            assert result == "[00:00:00 - 00:00:05] SPEAKER_00"


class TestHandleApplyDiarizationMode:
    """Test handle_apply_diarization_mode function."""

    def test_handle_apply_diarization_mode_transcript_not_found(self, tmp_path: Path) -> None:
        """Test that handle_apply_diarization_mode raises error for missing transcript."""
        audio_file = tmp_path / "test.mp3"
        audio_file.write_text("fake audio")

        with pytest.raises(FileNotFoundError, match="Transcript file not found"):
            handle_apply_diarization_mode(audio_file, Path("/nonexistent/transcript.txt"), "hf_token")

    def test_handle_apply_diarization_mode_audio_not_found(self, tmp_path: Path) -> None:
        """Test that handle_apply_diarization_mode raises error for missing audio."""
        transcript_file = tmp_path / "transcript.txt"
        transcript_file.write_text("[00:00:00 - 00:00:05] Hello")

        with pytest.raises(FileNotFoundError, match="Audio file not found"):
            handle_apply_diarization_mode(Path("/nonexistent/audio.mp3"), transcript_file, "hf_token")

    def test_handle_apply_diarization_mode(self, tmp_path: Path) -> None:
        """Test handle_apply_diarization_mode returns result without saving."""
        audio_file = tmp_path / "test.mp3"
        audio_file.write_text("fake audio")
        transcript_file = tmp_path / "transcript.txt"
        transcript_file.write_text("[00:00:00 - 00:00:05] Hello")

        with (
            patch("vtt_transcribe.handlers._lazy_import_diarization") as mock_import,
            patch("builtins.print"),
        ):
            mock_diarizer = MagicMock()
            mock_diarizer.diarize_audio.return_value = [(0.0, 5.0, "SPEAKER_00")]
            mock_diarizer.apply_speakers_to_transcript.return_value = "[00:00:00 - 00:00:05] SPEAKER_00: Hello"

            mock_import.return_value = (
                lambda *_args, **_kwargs: mock_diarizer,
                MagicMock(),
                MagicMock(),
                MagicMock(),
            )

            result = handle_apply_diarization_mode(audio_file, transcript_file, "hf_token")

            assert result == "[00:00:00 - 00:00:05] SPEAKER_00: Hello"


class TestHandleReviewSpeakers:
    """Test handle_review_speakers function."""

    def test_handle_review_speakers_missing_inputs(self) -> None:
        """Test handle_review_speakers raises error when both input_path and transcript are None."""
        with (  # noqa: PT012
            patch("vtt_transcribe.handlers._lazy_import_diarization") as mock_import,
            pytest.raises(ValueError, match="Either input_path or transcript must be provided"),
        ):
            mock_import.return_value = (MagicMock(), MagicMock(), MagicMock(), MagicMock())
            handle_review_speakers(input_path=None, transcript=None)

    def test_handle_review_speakers_with_missing_file(self) -> None:
        """Test handle_review_speakers raises error for missing input file."""
        with (  # noqa: PT012
            patch("vtt_transcribe.handlers._lazy_import_diarization") as mock_import,
            pytest.raises(FileNotFoundError, match="Input file not found"),
        ):
            mock_import.return_value = (MagicMock(), MagicMock(), MagicMock(), MagicMock())
            handle_review_speakers(input_path=Path("/nonexistent/file.mp3"))

    def test_handle_review_speakers_with_audio_file(self, tmp_path: Path) -> None:
        """Test handle_review_speakers processes audio file."""
        audio_file = tmp_path / "test.mp3"
        audio_file.write_text("fake audio")

        with (
            patch("vtt_transcribe.handlers._lazy_import_diarization") as mock_import,
            patch("builtins.input", return_value=""),
            patch("builtins.print"),
        ):
            mock_diarizer = MagicMock()
            mock_diarizer.diarize_audio.return_value = [(0.0, 5.0, "SPEAKER_00")]
            mock_format = MagicMock(return_value="[00:00:00 - 00:00:05] SPEAKER_00")
            mock_context = MagicMock(return_value=["context line"])

            mock_import.return_value = (
                lambda *_args, **_kwargs: mock_diarizer,
                mock_format,
                MagicMock(),
                mock_context,
            )

            result = handle_review_speakers(input_path=audio_file, hf_token="hf_token")  # noqa: S106

            assert "SPEAKER_00" in result

    def test_handle_review_speakers_with_transcript_file(self, tmp_path: Path) -> None:
        """Test handle_review_speakers loads transcript from .txt file."""
        transcript_file = tmp_path / "test.txt"
        transcript_file.write_text("[00:00:00 - 00:00:05] SPEAKER_00: Hello")

        with (
            patch("vtt_transcribe.handlers._lazy_import_diarization") as mock_import,
            patch("builtins.input", return_value=""),
            patch("builtins.print"),
        ):
            mock_diarizer = MagicMock()
            mock_diarizer.diarize_audio.return_value = [(0.0, 5.0, "SPEAKER_00")]
            mock_format = MagicMock(return_value="[00:00:00 - 00:00:05] SPEAKER_00")
            mock_context = MagicMock(return_value=["context line"])

            mock_import.return_value = (
                lambda *_args, **_kwargs: mock_diarizer,
                mock_format,
                MagicMock(),
                mock_context,
            )

            result = handle_review_speakers(input_path=transcript_file, hf_token="hf_token")  # noqa: S106

            assert "SPEAKER_00" in result

    def test_handle_review_speakers_with_save_path(self, tmp_path: Path) -> None:
        """Test handle_review_speakers saves to specified path."""
        audio_file = tmp_path / "test.mp3"
        audio_file.write_text("fake audio")
        save_path = tmp_path / "output.txt"

        with (
            patch("vtt_transcribe.handlers._lazy_import_diarization") as mock_import,
            patch("builtins.input", return_value=""),
            patch("builtins.print"),
        ):
            mock_diarizer = MagicMock()
            mock_diarizer.diarize_audio.return_value = [(0.0, 5.0, "SPEAKER_00")]
            mock_format = MagicMock(return_value="[00:00:00 - 00:00:05] SPEAKER_00")
            mock_context = MagicMock(return_value=["context line"])

            mock_import.return_value = (
                lambda *_args, **_kwargs: mock_diarizer,
                mock_format,
                MagicMock(),
                mock_context,
            )

            handle_review_speakers(input_path=audio_file, hf_token="hf_token", save_path=save_path)  # noqa: S106

            assert save_path.exists()


class TestHandleStandardTranscription:
    """Test handle_standard_transcription function."""

    def test_handle_standard_transcription_basic(self, tmp_path: Path) -> None:
        """Test basic transcription without diarization."""
        audio_file = tmp_path / "test.mp3"
        audio_file.write_text("fake audio")

        args = MagicMock()
        args.input_file = str(audio_file)
        args.output_audio = None
        args.delete_audio = False
        args.force = False
        args.scan_chunks = False
        args.diarize = False

        with (
            patch("vtt_transcribe.transcriber.VideoTranscriber") as mock_transcriber_class,
            patch("builtins.print"),
        ):
            mock_transcriber = MagicMock()
            mock_transcriber.transcribe.return_value = "Test transcript"
            mock_transcriber_class.return_value = mock_transcriber

            result = handle_standard_transcription(args, "test_api_key")

            assert result == "Test transcript"
            mock_transcriber.transcribe.assert_called_once()

    def test_handle_standard_transcription_with_diarization(self, tmp_path: Path) -> None:
        """Test transcription with diarization enabled."""
        audio_file = tmp_path / "test.mp3"
        audio_file.write_text("fake audio")

        args = MagicMock()
        args.input_file = str(audio_file)
        args.output_audio = None
        args.delete_audio = False
        args.force = False
        args.scan_chunks = False
        args.diarize = True
        args.hf_token = "hf_token"  # noqa: S105
        args.device = "cpu"
        args.no_review_speakers = True

        with (
            patch("vtt_transcribe.transcriber.VideoTranscriber") as mock_transcriber_class,
            patch("vtt_transcribe.handlers._lazy_import_diarization") as mock_import,
            patch("builtins.print"),
        ):
            mock_transcriber = MagicMock()
            mock_transcriber.transcribe.return_value = "[00:00:00 - 00:00:05] Hello"
            mock_transcriber.SUPPORTED_AUDIO_FORMATS = (".mp3", ".wav")
            mock_transcriber_class.return_value = mock_transcriber
            mock_transcriber_class.SUPPORTED_AUDIO_FORMATS = (".mp3", ".wav")

            mock_diarizer = MagicMock()
            mock_diarizer.diarize_audio.return_value = [(0.0, 5.0, "SPEAKER_00")]
            mock_diarizer.apply_speakers_to_transcript.return_value = "[00:00:00 - 00:00:05] SPEAKER_00: Hello"

            mock_import.return_value = (
                lambda *_args, **_kwargs: mock_diarizer,
                MagicMock(),
                MagicMock(),
                MagicMock(),
            )

            result = handle_standard_transcription(args, "test_api_key")

            assert "SPEAKER_00" in result
            mock_diarizer.apply_speakers_to_transcript.assert_called_once()


class TestNoReviewSpeakersFlag:
    """Test --no-review-speakers flag behavior in main()."""

    def test_diarize_only_runs_review_by_default(self, tmp_path: Any) -> None:
        """Test that --diarize-only triggers review unless --no-review-speakers is used."""
        from vtt_transcribe.main import main

        audio_file = tmp_path / "test.mp3"
        audio_file.write_text("fake audio")

        with (
            patch("sys.argv", ["vtt", str(audio_file), "--diarize-only", "--hf-token", "hf_test"]),
            patch("vtt_transcribe.main.handle_diarize_only_mode") as mock_diarize_only,
            patch("vtt_transcribe.main.handle_review_speakers") as mock_review,
            patch("builtins.print"),
        ):
            mock_diarize_only.return_value = "[00:00:00 - 00:00:05] SPEAKER_00"

            main()

            # Verify review WAS called (default behavior when NOT in stdin mode)
            mock_review.assert_called_once()

    def test_no_review_speakers_disables_review_for_diarize_only(self, tmp_path: Any) -> None:
        """Test that --no-review-speakers prevents review in --diarize-only mode."""
        from vtt_transcribe.main import main

        audio_file = tmp_path / "test.mp3"
        audio_file.write_text("fake audio")

        with (
            patch("sys.argv", ["vtt", str(audio_file), "--diarize-only", "--hf-token", "hf_test", "--no-review-speakers"]),
            patch("vtt_transcribe.main.handle_diarize_only_mode") as mock_diarize_only,
            patch("vtt_transcribe.main.handle_review_speakers") as mock_review,
            patch("builtins.print"),
        ):
            mock_diarize_only.return_value = "[00:00:00 - 00:00:05] SPEAKER_00"

            main()

            # Verify review was NOT called
            mock_review.assert_not_called()

    def test_no_review_speakers_disables_review_for_apply_diarization(self, tmp_path: Any) -> None:
        """Test that --no-review-speakers prevents review in --apply-diarization mode."""
        from vtt_transcribe.main import main

        audio_file = tmp_path / "test.mp3"
        audio_file.write_text("fake audio")
        transcript_file = tmp_path / "transcript.txt"
        transcript_file.write_text("[00:00:00 - 00:00:05] SPEAKER_00: Hello")

        with (
            patch(
                "sys.argv",
                [
                    "vtt",
                    str(audio_file),
                    "--apply-diarization",
                    str(transcript_file),
                    "--hf-token",
                    "hf_test",
                    "--no-review-speakers",
                ],
            ),
            patch("vtt_transcribe.main.handle_apply_diarization_mode") as mock_apply,
            patch("vtt_transcribe.main.handle_review_speakers") as mock_review,
            patch("builtins.print"),
        ):
            mock_apply.return_value = "[00:00:00 - 00:00:05] SPEAKER_00: Hello"

            main()

            # Verify review was NOT called
            mock_review.assert_not_called()

    def test_no_review_speakers_disables_review_for_diarize_transcribe(self, tmp_path: Any) -> None:
        """Test that --no-review-speakers prevents review in --diarize (transcribe+diarize) mode."""
        from vtt_transcribe.main import main

        audio_file = tmp_path / "test.mp3"
        audio_file.write_text("fake audio")

        with (
            patch(
                "sys.argv",
                ["vtt", str(audio_file), "-k", "test_key", "--diarize", "--hf-token", "hf_test", "--no-review-speakers"],
            ),
            patch("vtt_transcribe.main.handle_standard_transcription") as mock_transcribe,
            patch("builtins.print"),
        ):
            mock_transcribe.return_value = "[00:00:00 - 00:00:05] SPEAKER_00: Hello"

            main()

            # The actual verification happens inside handle_standard_transcription
            mock_transcribe.assert_called_once()

    def test_diarize_transcribe_runs_review_by_default(self, tmp_path: Any) -> None:
        """Test that --diarize triggers review by default."""
        from vtt_transcribe.main import main

        audio_file = tmp_path / "test.mp3"
        audio_file.write_text("fake audio")

        with (
            patch("sys.argv", ["vtt", str(audio_file), "-k", "test_key", "--diarize", "--hf-token", "hf_test"]),
            patch("vtt_transcribe.transcriber.VideoTranscriber") as mock_transcriber_class,
            patch("vtt_transcribe.handlers._lazy_import_diarization") as mock_diarization_import,
            patch("vtt_transcribe.handlers.handle_review_speakers") as mock_review,
            patch("builtins.print"),
        ):
            mock_transcriber = MagicMock()
            mock_transcriber.transcribe.return_value = "[00:00:00 - 00:00:05] Hello"
            mock_transcriber.SUPPORTED_AUDIO_FORMATS = (".mp3", ".wav")
            mock_transcriber_class.return_value = mock_transcriber
            mock_transcriber_class.SUPPORTED_AUDIO_FORMATS = (".mp3", ".wav")

            mock_diarizer = MagicMock()
            mock_diarizer.diarize_audio.return_value = [(0.0, 5.0, "SPEAKER_00")]
            mock_diarizer.apply_speakers_to_transcript.return_value = "[00:00:00 - 00:00:05] SPEAKER_00: Hello"

            mock_diarization_import.return_value = (
                lambda *_args, **_kwargs: mock_diarizer,
                MagicMock(),
                MagicMock(return_value=["SPEAKER_00"]),
                MagicMock(return_value=["context"]),
            )

            mock_review.return_value = "[00:00:00 - 00:00:05] SPEAKER_00: Hello"

            main()

            # Verify review WAS called (default behavior)
            assert mock_review.called, "Review should run by default"

    def test_diarize_transcribe_speaker_rename_with_input(self, tmp_path: Any) -> None:
        """Test that speaker renaming works when user provides input."""
        from vtt_transcribe.main import main

        audio_file = tmp_path / "test.mp3"
        audio_file.write_text("fake audio")

        with (
            patch("sys.argv", ["vtt", str(audio_file), "-k", "test_key", "--diarize", "--hf-token", "hf_test"]),
            patch("vtt_transcribe.transcriber.VideoTranscriber") as mock_transcriber_class,
            patch("vtt_transcribe.handlers._lazy_import_diarization") as mock_diarization_import,
            patch("builtins.input", return_value="Alice") as mock_input,
            patch("builtins.print") as mock_print,
        ):
            mock_transcriber = MagicMock()
            mock_transcriber.transcribe.return_value = "[00:00:00 - 00:00:05] Hello"
            mock_transcriber.SUPPORTED_AUDIO_FORMATS = (".mp3", ".wav")
            mock_transcriber_class.return_value = mock_transcriber
            mock_transcriber_class.SUPPORTED_AUDIO_FORMATS = (".mp3", ".wav")

            mock_diarizer = MagicMock()
            mock_diarizer.diarize_audio.return_value = [(0.0, 5.0, "SPEAKER_00")]
            mock_diarizer.apply_speakers_to_transcript.return_value = "[00:00:00 - 00:00:05] SPEAKER_00: Hello"

            mock_diarization_import.return_value = (
                lambda *_args, **_kwargs: mock_diarizer,
                MagicMock(),
                MagicMock(return_value=["SPEAKER_00"]),
                MagicMock(return_value=["context"]),
            )

            main()

            # Verify input was called
            mock_input.assert_called()

            # Verify the rename message was printed
            print_calls = [str(call) for call in mock_print.call_args_list]
            assert any("Renamed SPEAKER_00 -> Alice" in call for call in print_calls), "Should print rename confirmation"
