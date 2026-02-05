"""Tests for stdin/stdout mode functionality."""

import io
from unittest.mock import MagicMock, patch

import pytest

from vtt_transcribe.main import main


class TestStdinDetection:
    """Tests for stdin detection logic."""

    def test_stdin_mode_activated_when_stdin_is_not_tty(self, mock_stdin_tty: MagicMock) -> None:
        """Test that stdin mode activates when stdin is piped (not a TTY)."""
        with (
            patch("vtt_transcribe.main.sys.stdin") as mock_stdin,
            patch("sys.argv", ["vtt", "-k", "test-key"]),
            patch("vtt_transcribe.main.handle_standard_transcription", return_value="Test transcript"),
            patch("sys.stdout", new_callable=io.StringIO) as mock_stdout,
        ):
            mock_stdin.isatty.return_value = False
            mock_stdin.buffer.read.return_value = b"fake audio data"

            # Should detect stdin mode and complete successfully
            main()

            # Should have written to stdout
            assert "Test transcript" in mock_stdout.getvalue()

    def test_stdin_mode_not_activated_when_stdin_is_tty(self, mock_stdin_tty: MagicMock) -> None:
        """Test that stdin mode is NOT activated when stdin is a terminal."""
        with (
            patch("sys.stdin") as mock_stdin,
            patch("sys.argv", ["vtt"]),
        ):
            mock_stdin.isatty.return_value = True

            # Should fail with missing arguments error, not stdin mode
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 2


class TestStdinTempFileHandling:
    """Tests for temporary file handling in stdin mode."""

    def test_stdin_data_written_to_temp_file(self, mock_stdin_tty: MagicMock) -> None:
        """Test that stdin binary data is written to a temporary file."""
        fake_audio = b"FAKE_AUDIO_DATA_12345"

        with (
            patch("vtt_transcribe.main.sys.stdin") as mock_stdin,
            patch("sys.argv", ["vtt", "-k", "test-key"]),
            patch("vtt_transcribe.main.handle_standard_transcription", return_value="Transcript") as mock_transcribe,
            patch("sys.stdout", new_callable=io.StringIO),
        ):
            mock_stdin.isatty.return_value = False
            mock_stdin.buffer.read.return_value = fake_audio

            # Should create temp file and call transcriber with it
            main()

            # Check that transcriber was called and input_file was set
            assert mock_transcribe.called

    def test_stdin_temp_file_cleaned_up_after_processing(self, mock_stdin_tty: MagicMock) -> None:
        """Test that temporary file is removed after transcription."""
        with (
            patch("vtt_transcribe.main.sys.stdin") as mock_stdin,
            patch("sys.argv", ["vtt", "-k", "test-key"]),
            patch("vtt_transcribe.main.handle_standard_transcription", return_value="Transcript"),
            patch("sys.stdout", new_callable=io.StringIO),
            patch("tempfile.NamedTemporaryFile") as mock_tempfile,
            patch("pathlib.Path.unlink") as mock_unlink,
            patch("pathlib.Path.exists", return_value=True),
        ):
            # Setup mocks
            mock_temp_instance = MagicMock()
            mock_temp_instance.name = "/tmp/test.mp3"  # noqa: S108
            mock_temp_instance.__enter__.return_value = mock_temp_instance
            mock_temp_instance.__exit__.return_value = False
            mock_tempfile.return_value = mock_temp_instance

            mock_stdin.isatty.return_value = False
            mock_stdin.buffer.read.return_value = b"audio"

            # Should clean up temp file after processing
            main()

            # Verify cleanup was called
            mock_unlink.assert_called_once()

    def test_stdin_preserves_file_extension_from_arg(self, mock_stdin_tty: MagicMock) -> None:
        """Test that temp file uses extension from optional filename arg."""
        with (
            patch("vtt_transcribe.main.sys.stdin") as mock_stdin,
            patch("sys.argv", ["vtt", "input.m4a", "-k", "test-key"]),
            patch("vtt_transcribe.main.handle_standard_transcription", return_value="Transcript"),
            patch("sys.stdout", new_callable=io.StringIO),
            patch("tempfile.NamedTemporaryFile") as mock_tempfile,
        ):
            mock_temp_instance = MagicMock()
            mock_temp_instance.name = "/tmp/test.m4a"  # noqa: S108
            mock_temp_instance.__enter__.return_value = mock_temp_instance
            mock_temp_instance.__exit__.return_value = False
            mock_tempfile.return_value = mock_temp_instance

            mock_stdin.isatty.return_value = False
            mock_stdin.buffer.read.return_value = b"audio"

            # Should create temp file with .m4a extension
            main()

            # Verify temp file was created with correct extension
            mock_tempfile.assert_called_once()
            call_kwargs = mock_tempfile.call_args[1]
            assert call_kwargs["suffix"] == ".m4a"


class TestStdinStdoutRedirection:
    """Tests for stdout-only output in stdin mode."""

    def test_transcript_written_to_stdout_in_stdin_mode(self, mock_stdin_tty: MagicMock) -> None:
        """Test that transcript is written to stdout, not printed."""
        with (
            patch("vtt_transcribe.main.sys.stdin") as mock_stdin,
            patch("sys.stdout", new_callable=io.StringIO) as mock_stdout,
            patch("sys.argv", ["vtt", "-k", "test-key"]),
            patch("vtt_transcribe.main.handle_standard_transcription", return_value="[00:00 - 00:05] Test transcript"),
        ):
            mock_stdin.isatty.return_value = False
            mock_stdin.buffer.read.return_value = b"audio"

            # Should write to stdout
            main()

            output = mock_stdout.getvalue()
            assert "[00:00 - 00:05] Test transcript" in output

    def test_no_display_formatting_in_stdin_mode(self, mock_stdin_tty: MagicMock) -> None:
        """Test that display_result formatting is suppressed in stdin mode."""
        with (
            patch("vtt_transcribe.main.sys.stdin") as mock_stdin,
            patch("sys.stdout", new_callable=io.StringIO) as mock_stdout,
            patch("sys.argv", ["vtt", "-k", "test-key"]),
            patch("vtt_transcribe.main.handle_standard_transcription", return_value="Plain transcript"),
        ):
            mock_stdin.isatty.return_value = False
            mock_stdin.buffer.read.return_value = b"audio"

            # Should NOT include formatting headers
            main()

            output = mock_stdout.getvalue()
            assert "=" * 50 not in output
            assert "Transcription Result:" not in output
            assert "Plain transcript" in output


class TestStdinIncompatibleFlags:
    """Tests for flag validation in stdin mode."""

    def test_stdin_mode_rejects_save_transcript_flag(self, mock_stdin_tty: MagicMock) -> None:
        """Test that -s/--save-transcript is incompatible with stdin mode."""
        with (
            patch("vtt_transcribe.main.sys.stdin") as mock_stdin,
            patch("sys.argv", ["vtt", "-s", "output.txt", "-k", "test-key"]),
        ):
            mock_stdin.isatty.return_value = False

            # Should raise error about incompatible flag
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 2

    def test_stdin_mode_rejects_output_audio_flag(self, mock_stdin_tty: MagicMock) -> None:
        """Test that -o/--output-audio is incompatible with stdin mode."""
        with (
            patch("vtt_transcribe.main.sys.stdin") as mock_stdin,
            patch("sys.argv", ["vtt", "-o", "output.mp3", "-k", "test-key"]),
        ):
            mock_stdin.isatty.return_value = False

            # Should raise error about incompatible flag
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 2

    def test_stdin_mode_rejects_apply_diarization_flag(self, mock_stdin_tty: MagicMock) -> None:
        """Test that --apply-diarization is incompatible with stdin mode."""
        with (
            patch("vtt_transcribe.main.sys.stdin") as mock_stdin,
            patch("sys.argv", ["vtt", "--apply-diarization", "transcript.txt", "-k", "test-key"]),
        ):
            mock_stdin.isatty.return_value = False

            # Should raise error about incompatible flag (needs 2 files)
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 2

    def test_stdin_mode_rejects_scan_chunks_flag(self, mock_stdin_tty: MagicMock) -> None:
        """Test that --scan-chunks is incompatible with stdin mode."""
        with (
            patch("vtt_transcribe.main.sys.stdin") as mock_stdin,
            patch("sys.argv", ["vtt", "--scan-chunks", "-k", "test-key"]),
        ):
            mock_stdin.isatty.return_value = False

            # Should raise error about incompatible flag (needs multiple files)
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 2


class TestStdinIntegration:
    """Integration tests for full stdin workflows."""

    def test_stdin_mode_end_to_end_basic_transcription(self, mock_stdin_tty: MagicMock) -> None:
        """Test complete stdin workflow for basic transcription."""
        fake_audio = b"RIFF....WAVEfmt " + b"x" * 100

        with (
            patch("vtt_transcribe.main.sys.stdin") as mock_stdin,
            patch("sys.stdout", new_callable=io.StringIO) as mock_stdout,
            patch("sys.argv", ["vtt", "-k", "test-key"]),
            patch("vtt_transcribe.main.handle_standard_transcription", return_value="[00:00 - 00:05] Hello world"),
        ):
            mock_stdin.isatty.return_value = False
            mock_stdin.buffer.read.return_value = fake_audio

            # Should process and output to stdout
            main()

            output = mock_stdout.getvalue()
            assert "[00:00 - 00:05] Hello world" in output

    def test_stdin_mode_with_diarization_flag(self, mock_stdin_tty: MagicMock) -> None:
        """Test stdin mode works with --diarize flag."""
        with (
            patch("vtt_transcribe.main.sys.stdin") as mock_stdin,
            patch("sys.stdout", new_callable=io.StringIO) as mock_stdout,
            patch("sys.argv", ["vtt", "--diarize", "--no-review-speakers", "-k", "test-key", "--hf-token", "token"]),
            patch("vtt_transcribe.main.handle_standard_transcription", return_value="[00:00 - 00:05] SPEAKER_00: Hello"),
        ):
            mock_stdin.isatty.return_value = False
            mock_stdin.buffer.read.return_value = b"audio"

            # Should support diarization with stdin
            main()

            output = mock_stdout.getvalue()
            assert "SPEAKER_00: Hello" in output

    def test_stdin_mode_output_ends_with_newline(self, mock_stdin_tty: MagicMock) -> None:
        """Test that stdin mode output always ends with a newline."""
        fake_audio = b"RIFF....WAVEfmt " + b"x" * 100

        with (
            patch("vtt_transcribe.main.sys.stdin") as mock_stdin,
            patch("sys.stdout", new_callable=io.StringIO) as mock_stdout,
            patch("sys.argv", ["vtt", "-k", "test-key"]),
            patch("vtt_transcribe.main.handle_standard_transcription", return_value="[00:00 - 00:05] Hello world"),
        ):
            mock_stdin.isatty.return_value = False
            mock_stdin.buffer.read.return_value = fake_audio

            # Should process and output to stdout
            main()

            output = mock_stdout.getvalue()
            # Output should end with a newline to prevent prompt on same line
            assert output.endswith("\n"), "stdout output should end with a newline"

    def test_stdin_mode_without_filename_defaults_to_mp3(self, mock_stdin_tty: MagicMock) -> None:
        """Test that stdin without filename argument creates temp file with .mp3 extension."""
        fake_video_data = b"video data"

        with (
            patch("vtt_transcribe.main.sys.stdin") as mock_stdin,
            patch("sys.stdout", new_callable=io.StringIO),
            patch("sys.argv", ["vtt", "-k", "test-key"]),  # No filename arg
            patch("vtt_transcribe.main.handle_standard_transcription", return_value="transcript"),
            patch("tempfile.NamedTemporaryFile") as mock_tempfile,
        ):
            # Setup temp file mock
            mock_temp_instance = MagicMock()
            mock_temp_instance.name = "/tmp/tempXYZ.mp3"  # noqa: S108
            mock_temp_instance.__enter__.return_value = mock_temp_instance
            mock_temp_instance.__exit__.return_value = False
            mock_tempfile.return_value = mock_temp_instance

            mock_stdin.isatty.return_value = False
            mock_stdin.buffer.read.return_value = fake_video_data

            # Should create temp file with .mp3 extension by default
            main()

            # Verify temp file was created with .mp3 suffix
            mock_tempfile.assert_called_once()
            call_kwargs = mock_tempfile.call_args[1]
            assert call_kwargs["suffix"] == ".mp3", "Default suffix should be .mp3 when no filename provided"
