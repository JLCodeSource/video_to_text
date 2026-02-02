"""Tests for CLI argument parsing."""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from vtt_transcribe.cli import create_parser
from vtt_transcribe.main import get_api_key, main
from vtt_transcribe.transcriber import VideoTranscriber


class TestGetApiKey:
    """Test API key retrieval."""

    def test_get_api_key_from_argument(self) -> None:
        """Should return API key from argument."""
        result = get_api_key("test-key-arg")
        assert result == "test-key-arg"

    def test_get_api_key_from_env(self) -> None:
        """Should return API key from environment variable."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key-env"}):
            result = get_api_key(None)
            assert result == "test-key-env"

    def test_get_api_key_argument_overrides_env(self) -> None:
        """Should prefer argument over environment variable."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key-env"}):
            result = get_api_key("test-key-arg")
            assert result == "test-key-arg"

    def test_get_api_key_missing_raises_error(self) -> None:
        """Should raise ValueError when API key is missing."""
        with (
            patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False),
            patch("os.environ.get", return_value=None),
            pytest.raises(ValueError, match="OpenAI API key not provided"),
        ):
            get_api_key(None)


class TestCreateParser:
    """Test argument parser creation."""

    def test_create_parser_returns_parser(self) -> None:
        """Should return an ArgumentParser instance."""
        parser = create_parser()
        assert parser is not None
        assert hasattr(parser, "parse_args")

    def test_parser_accepts_input_file(self) -> None:
        """Should accept input file as positional argument."""
        parser = create_parser()
        args = parser.parse_args(["video.mp4"])
        assert args.input_file == "video.mp4"

    def test_parser_accepts_api_key_flag(self) -> None:
        """Should accept -k/--api-key flag."""
        parser = create_parser()
        args = parser.parse_args(["video.mp4", "-k", "test-key"])
        assert args.api_key == "test-key"

        args = parser.parse_args(["video.mp4", "--api-key", "test-key"])
        assert args.api_key == "test-key"

    def test_parser_accepts_output_audio_flag(self) -> None:
        """Should accept -o/--output-audio flag."""
        parser = create_parser()
        args = parser.parse_args(["video.mp4", "-o", "audio.mp3"])
        assert args.output_audio == "audio.mp3"

        args = parser.parse_args(["video.mp4", "--output-audio", "audio.mp3"])
        assert args.output_audio == "audio.mp3"

    def test_parser_accepts_save_transcript_flag(self) -> None:
        """Should accept -s/--save-transcript flag."""
        parser = create_parser()
        args = parser.parse_args(["video.mp4", "-s", "transcript.txt"])
        assert args.save_transcript == "transcript.txt"

        args = parser.parse_args(["video.mp4", "--save-transcript", "transcript.txt"])
        assert args.save_transcript == "transcript.txt"

    def test_parser_accepts_force_flag(self) -> None:
        """Should accept -f/--force flag."""
        parser = create_parser()
        args = parser.parse_args(["video.mp4", "-f"])
        assert args.force is True

        args = parser.parse_args(["video.mp4", "--force"])
        assert args.force is True

    def test_parser_accepts_delete_audio_flag(self) -> None:
        """Should accept --delete-audio flag."""
        parser = create_parser()
        args = parser.parse_args(["video.mp4", "--delete-audio"])
        assert args.delete_audio is True

    def test_parser_accepts_scan_chunks_flag(self) -> None:
        """Should accept --scan-chunks flag."""
        parser = create_parser()
        args = parser.parse_args(["video.mp4", "--scan-chunks"])
        assert args.scan_chunks is True

    def test_parser_accepts_diarize_flag(self) -> None:
        """Should accept --diarize flag."""
        parser = create_parser()
        args = parser.parse_args(["video.mp4", "--diarize"])
        assert args.diarize is True

    def test_parser_accepts_device_flag(self) -> None:
        """Should accept --device flag with valid choices."""
        parser = create_parser()

        args = parser.parse_args(["video.mp4", "--device", "auto"])
        assert args.device == "auto"

        args = parser.parse_args(["video.mp4", "--device", "cuda"])
        assert args.device == "cuda"

        args = parser.parse_args(["video.mp4", "--device", "gpu"])
        assert args.device == "gpu"

        args = parser.parse_args(["video.mp4", "--device", "cpu"])
        assert args.device == "cpu"

    def test_parser_accepts_diarize_only_flag(self) -> None:
        """Should accept --diarize-only flag."""
        parser = create_parser()
        args = parser.parse_args(["audio.mp3", "--diarize-only"])
        assert args.diarize_only is True

    def test_parser_accepts_apply_diarization_flag(self) -> None:
        """Should accept --apply-diarization flag."""
        parser = create_parser()
        args = parser.parse_args(["audio.mp3", "--apply-diarization", "transcript.txt"])
        assert args.apply_diarization == "transcript.txt"

    def test_parser_accepts_no_review_speakers_flag(self) -> None:
        """Should accept --no-review-speakers flag."""
        parser = create_parser()
        args = parser.parse_args(["audio.mp3", "--no-review-speakers"])
        assert args.no_review_speakers is True

    def test_parser_accepts_hf_token_flag(self) -> None:
        """Should accept --hf-token flag."""
        parser = create_parser()
        args = parser.parse_args(["audio.mp3", "--hf-token", "test-token"])
        assert args.hf_token == "test-token"  # noqa: S105

    def test_parser_accepts_version_flag(self) -> None:
        """Should accept --version flag and exit."""
        parser = create_parser()
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["--version"])
        assert exc_info.value.code == 0


class TestApiKeyHandling:
    """Test API key handling in main()."""

    def test_main_with_env_api_key(self, tmp_path: Path) -> None:
        """Test that main() reads API key from environment."""
        video_path = tmp_path / "test.mp4"
        video_path.touch()

        with (
            patch.dict(os.environ, {"OPENAI_API_KEY": "test_key_from_env"}),
            patch("sys.argv", ["vtt", str(video_path)]),
            patch("vtt_transcribe.main.handle_standard_transcription", return_value="Test transcript") as mock_transcribe,
            patch("builtins.print"),
        ):
            main()

            # Verify the API key was passed
            mock_transcribe.assert_called_once()
            call_args = mock_transcribe.call_args
            assert call_args[0][1] == "test_key_from_env"  # api_key is second arg

    def test_main_with_diarize_requires_api_key(self, tmp_path: Path) -> None:
        """Test that main() with --diarize still requires API key for transcription."""
        audio_file = tmp_path / "test.mp3"
        audio_file.touch()

        with (
            patch.dict(os.environ, {"OPENAI_API_KEY": "test_key_for_diarize"}),
            patch("sys.argv", ["vtt", str(audio_file), "--diarize", "--device", "cpu"]),
            patch("vtt_transcribe.main.handle_standard_transcription", return_value="Test transcript") as mock_transcribe,
            patch("builtins.print"),
        ):
            main()

            # Verify the API key was passed
            mock_transcribe.assert_called_once()
            call_args = mock_transcribe.call_args
            assert call_args[0][1] == "test_key_for_diarize"  # api_key is second arg


class TestMainCliArgumentParsing:
    """Test main function CLI argument parsing."""

    def test_main_with_required_args(self, tmp_path: Path) -> None:
        """Should work with minimum required arguments."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            video_path = tmp_path / "video.mp4"
            video_path.touch()

            with (
                patch("sys.argv", ["main.py", str(video_path)]),
                patch.object(VideoTranscriber, "transcribe", return_value="test"),
                patch("builtins.print"),
            ):
                import contextlib

                with contextlib.suppress(SystemExit):
                    main()

    def test_main_with_all_args(self, tmp_path: Path) -> None:
        """Should handle all CLI arguments."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            video_path = tmp_path / "video.mp4"
            video_path.touch()
            audio_path = tmp_path / "audio.mp3"
            transcript_path = tmp_path / "transcript.txt"

            with (
                patch(
                    "sys.argv",
                    [
                        "main.py",
                        str(video_path),
                        "-k",
                        "custom-key",
                        "-o",
                        str(audio_path),
                        "-s",
                        str(transcript_path),
                        "-f",
                    ],
                ),
                patch.object(VideoTranscriber, "transcribe", return_value="test"),
                patch("builtins.print"),
            ):
                import contextlib

                with contextlib.suppress(SystemExit):
                    main()

    def test_main_with_scan_chunks_flag(self, tmp_path: Path) -> None:
        """Should pass scan_chunks=True to transcriber when --scan-chunks flag provided."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            chunk_file = tmp_path / "audio_chunk0.mp3"
            chunk_file.write_text("x" * 1024)

            with (
                patch("sys.argv", ["main.py", str(chunk_file), "--scan-chunks"]),
                patch.object(VideoTranscriber, "transcribe", return_value="test") as mock_transcribe,
                patch("builtins.print"),
            ):
                import contextlib

                with contextlib.suppress(SystemExit):
                    main()

                mock_transcribe.assert_called_once()
                call_kwargs = mock_transcribe.call_args.kwargs
                assert call_kwargs.get("scan_chunks") is True

    def test_main_with_diarize_flag(self, tmp_path: Path) -> None:
        """Should apply diarization when --diarize flag is provided."""
        with (
            patch.dict(os.environ, {"OPENAI_API_KEY": "test-key", "HF_TOKEN": "hf-token"}),
        ):
            video_path = tmp_path / "video.mp4"
            video_path.touch()

            with (
                patch("sys.argv", ["main.py", str(video_path), "--diarize", "--no-review-speakers"]),
                patch.object(VideoTranscriber, "transcribe", return_value="[00:00:00 - 00:00:05] Hello"),
                patch("vtt_transcribe.handlers._lazy_import_diarization") as mock_lazy_import,
                patch("builtins.print"),
            ):
                mock_diarizer = MagicMock()
                mock_diarizer.diarize_audio.return_value = [(0.0, 5.0, "SPEAKER_00")]
                mock_diarizer.apply_speakers_to_transcript.return_value = "[00:00:00 - 00:00:05] SPEAKER_00: Hello"
                mock_diarizer_class = MagicMock(return_value=mock_diarizer)
                mock_format = MagicMock()
                mock_get_unique = MagicMock()
                mock_get_context = MagicMock()
                mock_lazy_import.return_value = (mock_diarizer_class, mock_format, mock_get_unique, mock_get_context)

                import contextlib

                with contextlib.suppress(SystemExit):
                    main()

                mock_diarizer_class.assert_called_once_with(hf_token=None, device="auto")
                mock_diarizer.diarize_audio.assert_called_once()
                mock_diarizer.apply_speakers_to_transcript.assert_called_once()

    def test_main_with_device_flag(self, tmp_path: Path) -> None:
        """Should pass device parameter when --device flag is provided."""
        with (
            patch.dict(os.environ, {"OPENAI_API_KEY": "test-key", "HF_TOKEN": "hf-token"}),
        ):
            video_path = tmp_path / "video.mp4"
            video_path.touch()

            with (
                patch("sys.argv", ["main.py", str(video_path), "--diarize", "--device", "cuda", "--no-review-speakers"]),
                patch.object(VideoTranscriber, "transcribe", return_value="[00:00:00 - 00:00:05] Hello"),
                patch("vtt_transcribe.handlers._lazy_import_diarization") as mock_lazy_import,
                patch("builtins.print"),
            ):
                mock_diarizer = MagicMock()
                mock_diarizer.diarize_audio.return_value = [(0.0, 5.0, "SPEAKER_00")]
                mock_diarizer.apply_speakers_to_transcript.return_value = "[00:00:00 - 00:00:05] SPEAKER_00: Hello"
                mock_diarizer_class = MagicMock(return_value=mock_diarizer)
                mock_format = MagicMock()
                mock_get_unique = MagicMock()
                mock_get_context = MagicMock()
                mock_lazy_import.return_value = (mock_diarizer_class, mock_format, mock_get_unique, mock_get_context)

                import contextlib

                with contextlib.suppress(SystemExit):
                    main()

                mock_diarizer_class.assert_called_once_with(hf_token=None, device="cuda")

    def test_main_with_diarize_only_flag(self, tmp_path: Path) -> None:
        """Should run diarization without transcription when --diarize-only flag is provided."""
        with (
            patch.dict(os.environ, {"HF_TOKEN": "hf-token"}),
        ):
            audio_path = tmp_path / "audio.mp3"
            audio_path.touch()

            with (
                patch("sys.argv", ["main.py", str(audio_path), "--diarize-only", "--no-review-speakers"]),
                patch("vtt_transcribe.handlers._lazy_import_diarization") as mock_lazy_import,
                patch("builtins.print"),
            ):
                mock_diarizer = MagicMock()
                mock_diarizer.diarize_audio.return_value = [(0.0, 5.0, "SPEAKER_00")]
                mock_diarizer_class = MagicMock(return_value=mock_diarizer)
                mock_format = MagicMock(return_value="[00:00:00 - 00:00:05] SPEAKER_00")
                mock_get_unique = MagicMock()
                mock_get_context = MagicMock()
                mock_lazy_import.return_value = (mock_diarizer_class, mock_format, mock_get_unique, mock_get_context)

                import contextlib

                with contextlib.suppress(SystemExit):
                    main()

                mock_diarizer_class.assert_called_once_with(hf_token=None, device="auto")
                mock_diarizer.diarize_audio.assert_called_once_with(audio_path)

    def test_main_with_apply_diarization_flag(self, tmp_path: Path) -> None:
        """Should apply diarization to existing transcript when --apply-diarization flag is provided."""
        with (
            patch.dict(os.environ, {"HF_TOKEN": "hf-token"}),
        ):
            audio_path = tmp_path / "audio.mp3"
            audio_path.touch()
            transcript_path = tmp_path / "transcript.txt"
            transcript_path.write_text("[00:00:00 - 00:00:05] Hello world")

            with (
                patch(
                    "sys.argv",
                    ["main.py", str(audio_path), "--apply-diarization", str(transcript_path), "--no-review-speakers"],
                ),
                patch("vtt_transcribe.handlers._lazy_import_diarization") as mock_lazy_import,
                patch("builtins.print"),
            ):
                mock_diarizer = MagicMock()
                mock_diarizer.diarize_audio.return_value = [(0.0, 5.0, "SPEAKER_00")]
                mock_diarizer.apply_speakers_to_transcript.return_value = "[00:00:00 - 00:00:05] SPEAKER_00: Hello world"
                mock_diarizer_class = MagicMock(return_value=mock_diarizer)
                mock_format = MagicMock()
                mock_get_unique = MagicMock()
                mock_get_context = MagicMock()
                mock_lazy_import.return_value = (mock_diarizer_class, mock_format, mock_get_unique, mock_get_context)

                import contextlib

                with contextlib.suppress(SystemExit):
                    main()

                mock_diarizer_class.assert_called_once_with(hf_token=None, device="auto")
                mock_diarizer.diarize_audio.assert_called_once_with(audio_path)
                mock_diarizer.apply_speakers_to_transcript.assert_called_once_with(
                    "[00:00:00 - 00:00:05] Hello world", [(0.0, 5.0, "SPEAKER_00")]
                )
