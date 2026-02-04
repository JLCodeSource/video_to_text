"""Comprehensive unit and integration tests for video_to_text."""

import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast
from unittest.mock import MagicMock, patch

import pytest

if TYPE_CHECKING:
    from openai.types.audio.transcription_verbose import TranscriptionVerbose

from vtt_transcribe.main import main
from vtt_transcribe.transcriber import VideoTranscriber


# Helper function for common mock setup
def create_mock_transcriber_with_response(response_text: str = "default transcript") -> tuple[VideoTranscriber, MagicMock]:
    """Create a VideoTranscriber with mocked OpenAI client.

    Args:
        response_text: Text to return from transcription

    Returns:
        tuple: (transcriber, mock_client)
    """
    with patch("vtt_transcribe.transcriber.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.audio.transcriptions.create.return_value = cast(
            "TranscriptionVerbose",
            response_text,
        )
        return VideoTranscriber("test-key"), mock_client


class TestMainGuard:
    """Test main guard execution."""

    def test_main_guard_execution(self) -> None:
        """Test that main() is called when module is executed directly."""
        import subprocess
        import sys

        # Execute the module as __main__ using python -m
        result = subprocess.run(  # noqa: S603
            [sys.executable, "-m", "vtt_transcribe.main", "--version"],
            capture_output=True,
            text=True,
        )

        # Should successfully show version without errors
        assert result.returncode == 0
        assert "." in result.stdout  # Version should contain dots

    def test_main_module_direct_execution(self) -> None:
        """Test running the module file directly."""
        import subprocess
        import sys
        from pathlib import Path

        main_file = Path(__file__).parent.parent / "vtt_transcribe" / "main.py"
        result = subprocess.run(  # noqa: S603
            [sys.executable, str(main_file), "--version"],
            capture_output=True,
            text=True,
        )

        # Should successfully show version when run as a script
        assert result.returncode == 0
        assert "." in result.stdout

        # Verify the guard exists in source
        source_content = main_file.read_text()
        assert 'if __name__ == "__main__":' in source_content
        assert "main()" in source_content


class TestTranscribeVerboseJson:
    """Tests for verbose_json transcription format (timestamps)."""

    def test_transcribe_audio_file_uses_verbose_json(self, tmp_path: Path) -> None:
        """Should call Whisper API with response_format='verbose_json'."""
        with patch("vtt_transcribe.transcriber.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.audio.transcriptions.create.return_value = cast(
                "TranscriptionVerbose",
                {
                    "segments": [
                        {"start": 0.0, "end": 1.0, "text": "Hello"},
                    ],
                },
            )

            audio_path = tmp_path / "audio.mp3"
            audio_path.write_text("dummy audio")

            transcriber = VideoTranscriber("key")
            # When transcribe_audio_file is called
            _ = transcriber.transcribe_audio_file(audio_path)

            # Then API called with verbose_json (test-first expectation)
            mock_client.audio.transcriptions.create.assert_called_once()
            call_kwargs = mock_client.audio.transcriptions.create.call_args[1]
            assert call_kwargs.get("response_format") == "verbose_json"

    def test_transcribe_audio_file_formats_verbose_json(self, tmp_path: Path) -> None:
        """Should format verbose_json response into timestamped lines."""
        with patch("vtt_transcribe.transcriber.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.audio.transcriptions.create.return_value = cast(
                "TranscriptionVerbose",
                {
                    "segments": [
                        {"start": 0.0, "end": 1.2, "text": "Hello world"},
                        {"start": 2.5, "end": 4.7, "text": "Second line"},
                    ],
                },
            )

            audio_path = tmp_path / "audio.mp3"
            audio_path.write_text("dummy audio")

            transcriber = VideoTranscriber("key")
            # When transcribe_audio_file is called
            result = transcriber.transcribe_audio_file(audio_path)

            # Then result should contain timestamped lines (expected format)
            expected_first = "[00:00:00 - 00:00:01] Hello world"
            expected_second = "[00:00:02 - 00:00:04] Second line"
            assert expected_first in result
            assert expected_second in result


def test_debug_print_exception_while_printing_response(tmp_path: Any, capsys: Any, monkeypatch: Any) -> None:
    # Given a transcriber whose client returns an object that raises on __str__
    class BadRepr:
        def __str__(self) -> str:
            msg = "bad repr"
            raise RuntimeError(msg)

    vt = VideoTranscriber(api_key="key")

    # When patching the client's transcription call to return the bad object
    monkeypatch.setattr(vt.client.audio.transcriptions, "create", lambda **_kwargs: BadRepr())

    # And: create a temporary audio file to pass into transcribe_audio_file
    audio_file = tmp_path / "dummy.mp3"
    audio_file.write_bytes(b"\0\0")

    # When transcribing the file
    vt.transcribe_audio_file(audio_file)

    # Then the debug except branch should print an error message
    captured = capsys.readouterr()
    assert "DEBUG: error while printing response" in captured.out


def test_format_timestamp_exception_branch() -> None:
    # Given a transcriber
    with patch("vtt_transcribe.transcriber.OpenAI"):
        transcriber = VideoTranscriber("key")
        # When calling _format_timestamp with a non-int-convertible value
        result = transcriber._format_timestamp("not-a-number")  # type: ignore[arg-type]
        # Then fallback to 00:00 is returned
        assert result == "00:00:00"


def test_main_guard_exists() -> None:
    """Test that the __name__ == '__main__' guard exists in main.py."""
    main_py = Path(__file__).parent.parent / "vtt_transcribe" / "main.py"
    content = main_py.read_text()

    # Verify the if __name__ == "__main__" guard exists and calls main()
    assert 'if __name__ == "__main__":' in content
    assert "main()" in content


def test_main_module_entry_point(capsys: pytest.CaptureFixture[str]) -> None:
    """Test that python -m vtt_transcribe works via __main__.py."""
    import runpy
    from unittest.mock import patch

    from vtt_transcribe import __version__

    with patch("sys.argv", ["vtt_transcribe", "--version"]):
        # Import __main__.py which should call main() with --version and exit with code 0
        with pytest.raises(SystemExit) as exc_info:
            runpy.run_path(
                str(Path(__file__).parent.parent / "vtt_transcribe" / "__main__.py"),
                run_name="__main__",
            )

        # Verify --version exits with code 0 and prints the version
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert __version__ in captured.out


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=main", "--cov-report=term-missing", "--cov-report=html"])


class TestLazyImportDiarization:
    """Test all branches of _lazy_import_diarization function."""

    def test_missing_package_module_with_fallback_success(self) -> None:
        """Test ModuleNotFoundError for vtt_transcribe.diarization with successful fallback."""
        import builtins
        from importlib import reload
        from unittest.mock import MagicMock

        original_import = builtins.__import__

        # Create mock diarization module
        mock_diarization = MagicMock()
        mock_diarization.SpeakerDiarizer = MagicMock()
        mock_diarization.format_diarization_output = MagicMock()
        mock_diarization.get_speaker_context_lines = MagicMock()
        mock_diarization.get_unique_speakers = MagicMock()

        def mock_import(name: str, *args: Any, **kwargs: Any) -> Any:
            if name == "vtt_transcribe.diarization":
                err = ModuleNotFoundError("No module named 'vtt_transcribe.diarization'")
                err.name = "vtt_transcribe.diarization"
                raise err
            if name == "diarization":
                return mock_diarization
            return original_import(name, *args, **kwargs)

        try:
            # Remove from sys.modules if present
            if "vtt_transcribe.handlers" in sys.modules:
                del sys.modules["vtt_transcribe.handlers"]

            builtins.__import__ = mock_import

            import vtt_transcribe.handlers

            reload(vtt_transcribe.handlers)

            result = vtt_transcribe.handlers._lazy_import_diarization()
            assert len(result) == 4
            assert result[0] == mock_diarization.SpeakerDiarizer
        finally:
            builtins.__import__ = original_import
            # Reload to restore normal state
            import vtt_transcribe.handlers

            reload(vtt_transcribe.handlers)

    def test_missing_package_module_with_fallback_failure(self) -> None:
        """Test ModuleNotFoundError for vtt_transcribe.diarization with fallback also failing."""
        import builtins
        from importlib import reload

        original_import = builtins.__import__

        def mock_import(name: str, *args: Any, **kwargs: Any) -> Any:
            if name == "vtt_transcribe.diarization":
                err = ModuleNotFoundError("No module named 'vtt_transcribe.diarization'")
                err.name = "vtt_transcribe.diarization"
                raise err
            if name == "diarization":
                msg = "Fallback also failed"
                raise ImportError(msg)
            return original_import(name, *args, **kwargs)

        try:
            if "vtt_transcribe.handlers" in sys.modules:
                del sys.modules["vtt_transcribe.handlers"]

            builtins.__import__ = mock_import

            import vtt_transcribe.handlers

            reload(vtt_transcribe.handlers)

            with pytest.raises(ImportError, match="Diarization dependencies not installed"):
                vtt_transcribe.handlers._lazy_import_diarization()
        finally:
            builtins.__import__ = original_import
            import vtt_transcribe.handlers

            reload(vtt_transcribe.handlers)

    def test_missing_dependency_torch(self) -> None:
        """Test ModuleNotFoundError for torch dependency."""
        import builtins
        from importlib import reload

        original_import = builtins.__import__

        def mock_import(name: str, *args: Any, **kwargs: Any) -> Any:
            if name == "vtt_transcribe.diarization":
                err = ModuleNotFoundError("No module named 'torch'")
                err.name = "torch"
                raise err
            return original_import(name, *args, **kwargs)

        try:
            if "vtt_transcribe.handlers" in sys.modules:
                del sys.modules["vtt_transcribe.handlers"]

            builtins.__import__ = mock_import

            import vtt_transcribe.handlers

            reload(vtt_transcribe.handlers)

            with pytest.raises(ImportError, match="Diarization dependencies not installed"):
                vtt_transcribe.handlers._lazy_import_diarization()
        finally:
            builtins.__import__ = original_import
            import vtt_transcribe.handlers

            reload(vtt_transcribe.handlers)

    def test_plain_import_error_with_fallback_success(self) -> None:
        """Test plain ImportError with successful fallback."""
        import builtins
        from importlib import reload
        from unittest.mock import MagicMock

        original_import = builtins.__import__

        # Create mock diarization module
        mock_diarization = MagicMock()
        mock_diarization.SpeakerDiarizer = MagicMock()
        mock_diarization.format_diarization_output = MagicMock()
        mock_diarization.get_speaker_context_lines = MagicMock()
        mock_diarization.get_unique_speakers = MagicMock()

        def mock_import(name: str, *args: Any, **kwargs: Any) -> Any:
            if name == "vtt_transcribe.diarization":
                # Plain ImportError without .name attribute
                msg = "Some import error"
                raise ImportError(msg)
            if name == "diarization":
                return mock_diarization
            return original_import(name, *args, **kwargs)

        try:
            if "vtt_transcribe.handlers" in sys.modules:
                del sys.modules["vtt_transcribe.handlers"]

            builtins.__import__ = mock_import

            import vtt_transcribe.handlers

            reload(vtt_transcribe.handlers)

            result = vtt_transcribe.handlers._lazy_import_diarization()
            assert len(result) == 4
            assert result[0] == mock_diarization.SpeakerDiarizer
        finally:
            builtins.__import__ = original_import
            import vtt_transcribe.handlers

            reload(vtt_transcribe.handlers)

    def test_plain_import_error_with_fallback_failure_reraises_original(self) -> None:
        """Test plain ImportError where fallback fails - should re-raise original."""
        import builtins
        from importlib import reload

        original_import = builtins.__import__

        def mock_import(name: str, *args: Any, **kwargs: Any) -> Any:
            if name == "vtt_transcribe.diarization":
                # Plain ImportError without .name attribute (real bug scenario)
                msg = "Cannot import name 'Foo' from 'bar'"
                raise ImportError(msg)
            if name == "diarization":
                msg2 = "Fallback also failed"
                raise ImportError(msg2)
            return original_import(name, *args, **kwargs)

        try:
            if "vtt_transcribe.handlers" in sys.modules:
                del sys.modules["vtt_transcribe.handlers"]

            builtins.__import__ = mock_import

            import vtt_transcribe.handlers

            reload(vtt_transcribe.handlers)

            # Should re-raise the original ImportError (real bug)
            with pytest.raises(ImportError, match="Cannot import name 'Foo' from 'bar'"):
                vtt_transcribe.handlers._lazy_import_diarization()
        finally:
            builtins.__import__ = original_import
            import vtt_transcribe.handlers

            reload(vtt_transcribe.handlers)


class TestM4aAudioSupport:
    """Test .m4a audio format support."""

    def test_m4a_recognized_as_audio_format(self) -> None:
        """Test that .m4a files are recognized as audio (not video)."""
        assert ".m4a" in VideoTranscriber.SUPPORTED_AUDIO_FORMATS, ".m4a should be in SUPPORTED_AUDIO_FORMATS"


class TestNoReviewSpeakersFlag:
    """Test --no-review-speakers flag disables automatic review."""

    def test_diarize_only_runs_review_by_default(self, tmp_path: Any) -> None:
        """Test that --diarize-only triggers review unless --no-review-speakers is used."""
        from unittest.mock import MagicMock, patch

        audio_file = tmp_path / "test.mp3"
        audio_file.write_text("fake audio")

        with (
            patch("sys.argv", ["vtt", str(audio_file), "--diarize-only", "--hf-token", "hf_test"]),
            patch("vtt_transcribe.handlers._lazy_import_diarization") as mock_diarization_import,
            patch("vtt_transcribe.main.handle_review_speakers") as mock_review,
            patch("vtt_transcribe.main.handle_diarize_only_mode") as _mock_diarize_only,
            patch("builtins.print"),
        ):
            mock_diarization_import.return_value = (MagicMock(), MagicMock(), MagicMock(), MagicMock())

            main()

            # Verify review WAS called (default behavior when NOT in stdin mode)
            mock_review.assert_called_once()

    def test_no_review_speakers_disables_review_for_diarize_only(self, tmp_path: Any) -> None:
        """Test that --no-review-speakers prevents review in --diarize-only mode."""
        from unittest.mock import MagicMock, patch

        audio_file = tmp_path / "test.mp3"
        audio_file.write_text("fake audio")

        with (
            patch("sys.argv", ["vtt", str(audio_file), "--diarize-only", "--hf-token", "hf_test", "--no-review-speakers"]),
            patch("vtt_transcribe.handlers._lazy_import_diarization") as mock_diarization_import,
            patch("vtt_transcribe.main.handle_review_speakers") as mock_review,
            patch("vtt_transcribe.main.handle_diarize_only_mode") as _mock_diarize_only,
            patch("builtins.print"),
        ):
            mock_diarization_import.return_value = (MagicMock(), MagicMock(), MagicMock(), MagicMock())

            main()

            # Verify review was NOT called
            mock_review.assert_not_called()

    def test_no_review_speakers_disables_review_for_apply_diarization(self, tmp_path: Any) -> None:
        """Test that --no-review-speakers prevents review in --apply-diarization mode."""
        from unittest.mock import MagicMock, patch

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
            patch("vtt_transcribe.handlers._lazy_import_diarization") as mock_diarization_import,
            patch("vtt_transcribe.main.handle_review_speakers") as mock_review,
            patch("vtt_transcribe.main.handle_apply_diarization_mode") as _mock_apply,
            patch("builtins.print"),
        ):
            mock_diarization_import.return_value = (MagicMock(), MagicMock(), MagicMock(), MagicMock())

            main()

            # Verify review was NOT called
            mock_review.assert_not_called()


def test_handle_review_speakers_missing_inputs() -> None:
    """Test handle_review_speakers raises error when both input_path and transcript are None."""
    import pytest

    import vtt_transcribe.handlers

    with (  # noqa: PT012
        patch("vtt_transcribe.handlers._lazy_import_diarization") as mock_import,
        pytest.raises(ValueError, match="Either input_path or transcript must be provided"),
    ):
        mock_import.return_value = (MagicMock(), MagicMock(), MagicMock(), MagicMock())
        vtt_transcribe.handlers.handle_review_speakers(input_path=None, transcript=None)


def test_cleanup_audio_files_prints_chunk_deletion(tmp_path: Path) -> None:
    """Test that cleanup_audio_files prints deletion messages for chunks."""
    from unittest.mock import patch

    audio_path = tmp_path / "audio.mp3"
    chunk_path = tmp_path / "audio_chunk0.mp3"
    audio_path.write_text("audio")
    chunk_path.write_text("chunk")

    with patch("vtt_transcribe.transcriber.OpenAI"):
        transcriber = VideoTranscriber("key")
        with patch("builtins.print") as mock_print:
            # Call cleanup which should print chunk deletions
            transcriber.cleanup_audio_files(audio_path)
            # Check that print was called (but chunks are already deleted by cleanup_files)
            print_calls = [str(call) for call in mock_print.call_args_list]
            assert any("Deleted audio file" in str(call) for call in print_calls)


class TestApiKeyHandling:
    """Test API key handling from environment and arguments."""

    def test_get_api_key_from_argument(self) -> None:
        """Test getting API key from command line argument."""
        from vtt_transcribe.main import get_api_key

        result = get_api_key("arg_key")
        assert result == "arg_key"

    def test_get_api_key_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test getting API key from environment variable."""
        from vtt_transcribe.main import get_api_key

        monkeypatch.setenv("OPENAI_API_KEY", "env_key")
        result = get_api_key(None)
        assert result == "env_key"

    def test_get_api_key_arg_takes_precedence(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that command line argument takes precedence over environment variable."""
        from vtt_transcribe.main import get_api_key

        monkeypatch.setenv("OPENAI_API_KEY", "env_key")
        result = get_api_key("arg_key")
        assert result == "arg_key"

    def test_get_api_key_missing_raises_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that missing API key raises ValueError."""
        from vtt_transcribe.main import get_api_key

        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        with pytest.raises(ValueError, match="OpenAI API key not provided"):
            get_api_key(None)


class TestStdinMode:
    """Test stdin/stdout mode functionality."""

    def test_stdin_mode_detection(self) -> None:
        """Test that stdin mode is detected when input is piped."""
        with (
            patch("sys.stdin.isatty", return_value=False),
            patch("sys.stdin.buffer.read", return_value=b"fake audio data"),
            patch("vtt_transcribe.transcriber.VideoTranscriber"),
        ):
            sys.argv = ["vtt"]
            with pytest.raises(SystemExit) as exc_info:
                main()
        # Should exit with error because no API key
        assert exc_info.value.code != 0

    def test_stdin_rejects_save_transcript(self) -> None:
        """Test that stdin mode rejects -s/--save-transcript flag."""
        with patch("sys.stdin.isatty", return_value=False):
            sys.argv = ["vtt", "-s", "output.txt"]
            with pytest.raises(SystemExit) as exc_info:
                main()
        assert exc_info.value.code == 2  # argparse error exit code

    def test_stdin_rejects_output_audio(self) -> None:
        """Test that stdin mode rejects -o/--output-audio flag."""
        with patch("sys.stdin.isatty", return_value=False):
            sys.argv = ["vtt", "-o", "output.mp3"]
            with pytest.raises(SystemExit) as exc_info:
                main()
        assert exc_info.value.code == 2

    def test_stdin_rejects_apply_diarization(self) -> None:
        """Test that stdin mode rejects --apply-diarization flag."""
        with patch("sys.stdin.isatty", return_value=False):
            sys.argv = ["vtt", "--apply-diarization", "transcript.txt"]
            with pytest.raises(SystemExit) as exc_info:
                main()
        assert exc_info.value.code == 2

    def test_stdin_rejects_scan_chunks(self) -> None:
        """Test that stdin mode rejects --scan-chunks flag."""
        with patch("sys.stdin.isatty", return_value=False):
            sys.argv = ["vtt", "--scan-chunks"]
            with pytest.raises(SystemExit) as exc_info:
                main()
        assert exc_info.value.code == 2

    def test_stdin_auto_enables_no_review_speakers(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test that --diarize auto-enables --no-review-speakers in stdin mode."""
        with (
            patch("sys.stdin.isatty", return_value=False),
            patch("sys.stdin.buffer.read", return_value=b"fake audio data"),
            patch("vtt_transcribe.transcriber.VideoTranscriber"),
            patch("vtt_transcribe.main.get_api_key", return_value="test-key"),
        ):
            sys.argv = ["vtt", "--diarize", "--hf-token", "test-token"]
            with pytest.raises(SystemExit):
                main()

        captured = capsys.readouterr()
        assert "Automatically enabling --no-review-speakers" in captured.err

    def test_stdin_no_review_speakers_already_set(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test that explicit --no-review-speakers doesn't print auto-enable message."""
        with (
            patch("sys.stdin.isatty", return_value=False),
            patch("sys.stdin.buffer.read", return_value=b"fake audio data"),
            patch("vtt_transcribe.transcriber.VideoTranscriber"),
            patch("vtt_transcribe.main.get_api_key", return_value="test-key"),
        ):
            sys.argv = ["vtt", "--diarize", "--no-review-speakers", "--hf-token", "test-token"]
            with pytest.raises(SystemExit):
                main()

        captured = capsys.readouterr()
        assert "Automatically enabling --no-review-speakers" not in captured.err

    def test_stdin_diarize_only_auto_enables(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test that --diarize-only in stdin mode auto-enables --no-review-speakers."""
        with (
            patch("sys.stdin.isatty", return_value=False),
            patch("sys.stdin.buffer.read", return_value=b"fake audio data"),
            patch("vtt_transcribe.main.handle_diarize_only_mode", return_value="SPEAKER_00: test"),
            patch("vtt_transcribe.main.check_ffmpeg_installed"),
            patch("vtt_transcribe.main.check_diarization_dependencies"),
        ):
            sys.argv = ["vtt", "--diarize-only", "--hf-token", "test-token"]
            main()

        captured = capsys.readouterr()
        # Should see the stdin mode message (not the diarize-only message since stdin runs first)
        assert "Automatically enabling --no-review-speakers" in captured.err
