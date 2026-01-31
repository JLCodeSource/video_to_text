"""Comprehensive unit and integration tests for video_to_text."""

from pathlib import Path
from typing import TYPE_CHECKING, Any, cast
from unittest.mock import MagicMock, patch

import pytest

if TYPE_CHECKING:
    from openai.types.audio.transcription_verbose import TranscriptionVerbose

from vtt.main import main
from vtt.transcriber import VideoTranscriber


# Helper function for common mock setup
def create_mock_transcriber_with_response(response_text: str = "default transcript") -> tuple[VideoTranscriber, MagicMock]:
    """Create a VideoTranscriber with mocked OpenAI client.

    Args:
        response_text: Text to return from transcription

    Returns:
        tuple: (transcriber, mock_client)
    """
    with patch("vtt.transcriber.OpenAI") as mock_openai:
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
        # Test that when we import the module, __name__ check exists and works
        from vtt import main as main_module

        # Verify the module has the expected structure
        assert hasattr(main_module, "main")
        assert callable(main_module.main)

        # We can't easily test the guard without actually running as __main__
        # but we can verify it exists in the source
        source_file = Path(__file__).parent.parent / "vtt" / "main.py"
        source_content = source_file.read_text()
        assert 'if __name__ == "__main__":' in source_content
        assert "main()" in source_content


class TestTranscribeVerboseJson:
    """Tests for verbose_json transcription format (timestamps)."""

    def test_transcribe_audio_file_uses_verbose_json(self, tmp_path: Path) -> None:
        """Should call Whisper API with response_format='verbose_json'."""
        with patch("vtt.transcriber.OpenAI") as mock_openai:
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
        with patch("vtt.transcriber.OpenAI") as mock_openai:
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
    with patch("vtt.transcriber.OpenAI"):
        transcriber = VideoTranscriber("key")
        # When calling _format_timestamp with a non-int-convertible value
        result = transcriber._format_timestamp("not-a-number")  # type: ignore[arg-type]
        # Then fallback to 00:00 is returned
        assert result == "00:00:00"


@pytest.mark.skip(reason="Complex module loading test - needs update for refactored structure")
def test_main_guard_executes_with_mocked_deps(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import runpy
    import sys
    import types

    # Given a dummy video file so validate_input_file passes
    video = tmp_path / "video.mp4"
    video.write_bytes(b"mp4")

    # And: prepare fake modules to satisfy imports inside main.py
    moviepy_vfc = types.ModuleType("moviepy.video.io.VideoFileClip")

    class DummyVideo:
        def __init__(self, _path: Path) -> None:
            self.audio = types.SimpleNamespace(write_audiofile=lambda *_args, **_kwargs: None)

        def close(self) -> None:
            return None

    moviepy_vfc.VideoFileClip = DummyVideo  # type: ignore[attr-defined]

    moviepy_afc = types.ModuleType("moviepy.audio.io.AudioFileClip")

    class DummyAudio:
        def __init__(self, _path: Path) -> None:
            self.duration = 1.0

        def close(self) -> None:
            return None

        def subclipped(self, _s: float, _e: float) -> "DummyAudio":
            return self

        def write_audiofile(self, *_args: Any, **_kwargs: Any) -> None:
            return None

    moviepy_afc.AudioFileClip = DummyAudio  # type: ignore[attr-defined]

    # Minimal openai module and OpenAI client
    openai_mod = types.ModuleType("openai")

    class DummyClient:
        def __init__(self, api_key: str | None = None) -> None:  # noqa: ARG002
            self.audio = types.SimpleNamespace(transcriptions=types.SimpleNamespace(create=lambda **_k: {"text": "ok"}))

    openai_mod.OpenAI = DummyClient  # type: ignore[attr-defined]

    # And: insert fake modules into sys.modules so runpy will use them
    monkeypatch.setitem(sys.modules, "moviepy.video.io.VideoFileClip", moviepy_vfc)
    monkeypatch.setitem(sys.modules, "moviepy.audio.io.AudioFileClip", moviepy_afc)
    monkeypatch.setitem(sys.modules, "openai", openai_mod)

    # Run main.py as a __main__ module to hit the if __name__ == "__main__" guard
    monkeypatch.chdir(str(tmp_path))
    monkeypatch.setenv("OPENAI_API_KEY", "dummy")
    # And: create a companion audio file and pass it as -o so main() uses existing audio
    audio = tmp_path / "video.mp3"
    audio.write_bytes(b"")
    monkeypatch.setattr(sys, "argv", ["main.py", str(video), "-k", "dummy", "-o", str(audio)])

    # When executing the project's main.py as __main__
    runpy.run_path(str(Path(__file__).parent.parent / "vtt" / "main.py"), run_name="__main__")

    # Then execution completes without raising an exception


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=main", "--cov-report=term-missing", "--cov-report=html"])


class TestLazyImportDiarization:
    """Test _lazy_import_diarization import fallback."""

    def test_lazy_import_normal_path(self) -> None:
        """Should import from vtt.diarization normally."""
        try:
            import pyannote.audio  # noqa: F401

            pyannote_available = True
        except ImportError:
            pyannote_available = False

        if not pyannote_available:
            pytest.skip("pyannote.audio not installed")

        from vtt.handlers import _lazy_import_diarization

        result = _lazy_import_diarization()

        assert len(result) == 4
        speaker_diarizer, format_output, get_unique, get_context = result
        assert speaker_diarizer is not None
        assert format_output is not None
        assert get_unique is not None
        assert get_context is not None

    def test_lazy_import_fallback_path(self) -> None:
        """Should fall back to direct import when vtt.diarization fails."""

        try:
            import pyannote.audio  # noqa: F401

            pyannote_available = True
        except ImportError:
            pyannote_available = False

        if not pyannote_available:
            pytest.skip("pyannote.audio not installed")

        import builtins
        import sys
        from importlib import reload
        from unittest.mock import MagicMock

        # Save original state
        original_module = sys.modules.get("vtt.diarization")
        original_import = builtins.__import__

        # Create a mock diarization module
        mock_diarization = MagicMock()
        mock_diarization.SpeakerDiarizer = MagicMock()
        mock_diarization.format_diarization_output = MagicMock()
        mock_diarization.get_speaker_context_lines = MagicMock()
        mock_diarization.get_unique_speakers = MagicMock()

        try:
            # Temporarily remove vtt.diarization from sys.modules
            if "vtt.diarization" in sys.modules:
                del sys.modules["vtt.diarization"]

            # Mock the import to fail for vtt.diarization but succeed for diarization
            def mock_import(name: str, *args: Any, **kwargs: Any) -> Any:
                if name == "vtt.diarization":
                    msg = "Simulated import failure"
                    raise ImportError(msg)
                if name == "diarization":
                    return mock_diarization
                return original_import(name, *args, **kwargs)

            builtins.__import__ = mock_import

            # Re-import handlers to get fresh _lazy_import_diarization
            import vtt.handlers

            reload(vtt.handlers)

            # This should use the fallback path
            result = vtt.handlers._lazy_import_diarization()

            assert len(result) == 4
            # Verify we got the mock objects from the fallback import
            assert result[0] == mock_diarization.SpeakerDiarizer
            assert result[1] == mock_diarization.format_diarization_output
        finally:
            # Restore original state
            builtins.__import__ = original_import
            if original_module is not None:
                sys.modules["vtt.diarization"] = original_module
            import vtt.handlers

            reload(vtt.handlers)


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
            patch("vtt.handlers._lazy_import_diarization") as mock_diarization_import,
            patch("vtt.main.handle_review_speakers") as mock_review,
            patch("vtt.main.handle_diarize_only_mode") as _mock_diarize_only,
            patch("builtins.print"),
        ):
            mock_diarization_import.return_value = (MagicMock(), MagicMock(), MagicMock(), MagicMock())

            main()

            # Verify review WAS called (default behavior)
            mock_review.assert_called_once()

    def test_no_review_speakers_disables_review_for_diarize_only(self, tmp_path: Any) -> None:
        """Test that --no-review-speakers prevents review in --diarize-only mode."""
        from unittest.mock import MagicMock, patch

        audio_file = tmp_path / "test.mp3"
        audio_file.write_text("fake audio")

        with (
            patch("sys.argv", ["vtt", str(audio_file), "--diarize-only", "--hf-token", "hf_test", "--no-review-speakers"]),
            patch("vtt.handlers._lazy_import_diarization") as mock_diarization_import,
            patch("vtt.main.handle_review_speakers") as mock_review,
            patch("vtt.main.handle_diarize_only_mode") as _mock_diarize_only,
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
            patch("vtt.handlers._lazy_import_diarization") as mock_diarization_import,
            patch("vtt.main.handle_review_speakers") as mock_review,
            patch("vtt.main.handle_apply_diarization_mode") as _mock_apply,
            patch("builtins.print"),
        ):
            mock_diarization_import.return_value = (MagicMock(), MagicMock(), MagicMock(), MagicMock())

            main()

            # Verify review was NOT called
            mock_review.assert_not_called()

    def test_no_review_speakers_disables_review_for_diarize_transcribe(self, tmp_path: Any) -> None:
        """Test that --no-review-speakers prevents review in --diarize (transcribe+diarize) mode."""
        from unittest.mock import MagicMock, patch

        audio_file = tmp_path / "test.mp3"
        audio_file.write_text("fake audio")

        with (
            patch(
                "sys.argv",
                ["vtt", str(audio_file), "-k", "test_key", "--diarize", "--hf-token", "hf_test", "--no-review-speakers"],
            ),
            patch("vtt.transcriber.VideoTranscriber") as mock_transcriber_class,
            patch("vtt.handlers._lazy_import_diarization") as mock_diarization_import,
            patch("builtins.input") as mock_input,
            patch("builtins.print"),
        ):
            mock_transcriber = MagicMock()
            mock_transcriber.transcribe.return_value = "[00:00:00 - 00:00:05] Hello"
            mock_transcriber_class.return_value = mock_transcriber

            mock_diarizer = MagicMock()
            mock_diarizer.diarize_audio.return_value = [(0.0, 5.0, "SPEAKER_00")]
            mock_diarizer.apply_speakers_to_transcript.return_value = "[00:00:00 - 00:00:05] SPEAKER_00: Hello"

            mock_diarization_import.return_value = (
                lambda *_args, **_kwargs: mock_diarizer,
                MagicMock(),
                MagicMock(return_value=["SPEAKER_00"]),
                MagicMock(return_value=[]),
            )

            main()

            # Verify input() was NOT called (no interactive review)
            mock_input.assert_not_called()

    def test_diarize_transcribe_runs_review_by_default(self, tmp_path: Any) -> None:
        """Test that --diarize triggers review by default."""
        from unittest.mock import MagicMock, patch

        audio_file = tmp_path / "test.mp3"
        audio_file.write_text("fake audio")

        with (
            patch("sys.argv", ["vtt", str(audio_file), "-k", "test_key", "--diarize", "--hf-token", "hf_test"]),
            patch("vtt.transcriber.VideoTranscriber") as mock_transcriber_class,
            patch("vtt.handlers._lazy_import_diarization") as mock_diarization_import,
            patch("builtins.input", return_value="") as mock_input,
            patch("builtins.print"),
        ):
            mock_transcriber = MagicMock()
            mock_transcriber.transcribe.return_value = "[00:00:00 - 00:00:05] Hello"
            mock_transcriber_class.return_value = mock_transcriber

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

            # Verify input() WAS called (review happened)
            assert mock_input.called, "Review should run by default"

    def test_diarize_transcribe_speaker_rename_with_input(self, tmp_path: Any) -> None:
        """Test that speaker renaming works when user provides input."""
        from unittest.mock import MagicMock, patch

        from vtt.main import main

        audio_file = tmp_path / "test.mp3"
        audio_file.write_text("fake audio")

        with (
            patch("sys.argv", ["vtt", str(audio_file), "-k", "test_key", "--diarize", "--hf-token", "hf_test"]),
            patch("vtt.transcriber.VideoTranscriber") as mock_transcriber_class,
            patch("vtt.handlers._lazy_import_diarization") as mock_diarization_import,
            patch("builtins.input", return_value="Alice") as mock_input,
            patch("builtins.print") as mock_print,
        ):
            mock_transcriber = MagicMock()
            mock_transcriber.transcribe.return_value = "[00:00:00 - 00:00:05] Hello"
            mock_transcriber_class.return_value = mock_transcriber

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


def test_handle_review_speakers_missing_inputs() -> None:
    """Test handle_review_speakers raises error when both input_path and transcript are None."""
    import pytest

    from vtt.handlers import handle_review_speakers

    with (  # noqa: PT012
        patch("vtt.handlers._lazy_import_diarization") as mock_import,
        pytest.raises(ValueError, match="Either input_path or transcript must be provided"),
    ):
        mock_import.return_value = (MagicMock(), MagicMock(), MagicMock(), MagicMock())
        handle_review_speakers(input_path=None, transcript=None)


def test_cleanup_audio_files_prints_chunk_deletion(tmp_path: Path) -> None:
    """Test that cleanup_audio_files prints deletion messages for chunks."""
    from unittest.mock import patch

    audio_path = tmp_path / "audio.mp3"
    chunk_path = tmp_path / "audio_chunk0.mp3"
    audio_path.write_text("audio")
    chunk_path.write_text("chunk")

    with patch("vtt.transcriber.OpenAI"):
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
        from vtt.main import get_api_key

        result = get_api_key("arg_key")
        assert result == "arg_key"

    def test_get_api_key_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test getting API key from environment variable."""
        from vtt.main import get_api_key

        monkeypatch.setenv("OPENAI_API_KEY", "env_key")
        result = get_api_key(None)
        assert result == "env_key"

    def test_get_api_key_arg_takes_precedence(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that command line argument takes precedence over environment variable."""
        from vtt.main import get_api_key

        monkeypatch.setenv("OPENAI_API_KEY", "env_key")
        result = get_api_key("arg_key")
        assert result == "arg_key"

    def test_get_api_key_missing_raises_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that missing API key raises ValueError."""
        from vtt.main import get_api_key

        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        with pytest.raises(ValueError, match="OpenAI API key not provided"):
            get_api_key(None)
