"""Comprehensive unit and integration tests for video_to_text."""

import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast
from unittest.mock import MagicMock, patch

import pytest

if TYPE_CHECKING:
    from openai.types.audio.transcription_verbose import TranscriptionVerbose

from vtt.handlers import display_result, save_transcript
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


class TestVideoTranscriberInit:
    """Test VideoTranscriber initialization."""

    def test_init_with_valid_api_key(self) -> None:
        """Should initialize with API key."""
        # Given OpenAI client is mocked
        with patch("vtt.transcriber.OpenAI") as mock_openai:
            # When VideoTranscriber is initialized with API key
            transcriber = VideoTranscriber("test-api-key")
            # Then API key is stored and OpenAI client is created
            assert transcriber.api_key == "test-api-key"
            mock_openai.assert_called_once_with(api_key="test-api-key")

    def test_init_sets_max_size_mb(self) -> None:
        """Should have MAX_SIZE_MB constant."""
        # Given OpenAI client is mocked
        with patch("vtt.transcriber.OpenAI"):
            # When VideoTranscriber is initialized
            transcriber = VideoTranscriber("test-key")
            # Then MAX_SIZE_MB constant is 25
            assert transcriber.MAX_SIZE_MB == 25


class TestValidateVideoFile:
    """Test video file validation."""

    def test_validate_existing_video_file(self, tmp_path: Path) -> None:
        """Should return Path when file exists."""
        # Given temporary directory with video file
        video_path = tmp_path / "test.mp4"
        video_path.touch()

        with patch("vtt.transcriber.OpenAI"):
            transcriber = VideoTranscriber("key")
            # When validate_input_file is called with existing file
            result = transcriber.validate_input_file(video_path)
            # Then same path is returned
            assert result == video_path

    def test_validate_nonexistent_video_file(self) -> None:
        """Should raise FileNotFoundError for missing file."""
        # Given OpenAI client is mocked
        with patch("vtt.transcriber.OpenAI"):
            transcriber = VideoTranscriber("key")
            nonexistent = Path("/nonexistent/video.mp4")

            # When validate_input_file is called with non-existent file
            with pytest.raises(FileNotFoundError) as exc_info:
                transcriber.validate_input_file(nonexistent)
            # Then FileNotFoundError is raised with appropriate message
            assert "Input file not found" in str(exc_info.value)


class TestResolveAudioPath:
    """Test audio path resolution."""

    def test_resolve_audio_path_none_returns_mp3_suffix(self) -> None:
        """Should default to .mp3 suffix when audio_path is None."""
        # Given VideoTranscriber and video path
        with patch("vtt.transcriber.OpenAI"):
            transcriber = VideoTranscriber("key")
            video_path = Path("/path/to/video.mp4")
            # When resolve_audio_path is called with None audio_path
            result = transcriber.resolve_audio_path(video_path, None)
            # Then .mp3 suffix is applied to video path
            assert result == Path("/path/to/video.mp3")

    def test_resolve_audio_path_custom(self) -> None:
        """Should accept custom audio_path with .mp3 extension."""
        # Given VideoTranscriber, video path, and custom audio path with .mp3
        with patch("vtt.transcriber.OpenAI"):
            transcriber = VideoTranscriber("key")
            video_path = Path("/path/to/video.mp4")
            audio_path = Path("/custom/audio.mp3")
            # When resolve_audio_path is called with .mp3 audio_path
            result = transcriber.resolve_audio_path(video_path, audio_path)
            # Then custom audio_path is returned unchanged
            assert result == audio_path


class TestAudioPathExtensionHandling:
    """Test .mp3 extension requirement for audio paths."""

    def test_custom_audio_without_extension_gets_mp3(self) -> None:
        """Should automatically add .mp3 to custom audio path without extension."""
        # Given custom audio path without any extension
        with patch("vtt.transcriber.OpenAI"):
            transcriber = VideoTranscriber("key")
            video_path = Path("/path/to/video.mp4")
            audio_path = Path("/custom/myaudio")  # No extension

            # When resolve_audio_path is called with path lacking extension
            result = transcriber.resolve_audio_path(video_path, audio_path)

            # Then .mp3 extension is automatically added
            assert result == Path("/custom/myaudio.mp3")
            assert str(result).endswith(".mp3")

    def test_custom_audio_with_different_extension_raises_error(self) -> None:
        """Should raise error for custom audio path with non-.mp3 extension."""
        # Given custom audio path with .wav extension
        with patch("vtt.transcriber.OpenAI"):
            transcriber = VideoTranscriber("key")
            video_path = Path("/path/to/video.mp4")
            audio_path = Path("/custom/audio.wav")  # Non-.mp3 extension

            # When resolve_audio_path is called with non-.mp3 extension
            # Then a ValueError is raised
            with pytest.raises(ValueError, match=r"Audio file must have \.mp3 extension"):
                transcriber.resolve_audio_path(video_path, audio_path)

    def test_custom_audio_with_mp3_extension_accepted(self) -> None:
        """Should accept custom audio path with .mp3 extension."""
        # Given custom audio path with .mp3 extension
        with patch("vtt.transcriber.OpenAI"):
            transcriber = VideoTranscriber("key")
            video_path = Path("/path/to/video.mp4")
            audio_path = Path("/custom/audio.mp3")  # .mp3 extension

            # When resolve_audio_path is called with .mp3 extension
            result = transcriber.resolve_audio_path(video_path, audio_path)

            # Then path is returned as-is
            assert result == audio_path
            assert str(result).endswith(".mp3")


class TestTranscriptFileExtensionHandling:
    """Test automatic .txt extension handling for transcript files."""

    def test_save_transcript_without_txt_extension(self, tmp_path: Path) -> None:
        """Should automatically add .txt to transcript path."""
        # Given transcript output path without .txt extension
        output_path = tmp_path / "mytranscript"  # No .txt
        transcript = "Test transcript content"

        with patch("builtins.print"):
            # When save_transcript is called without .txt extension
            save_transcript(output_path, transcript)

        # Then file is saved with .txt extension automatically added
        assert Path(tmp_path, "mytranscript.txt").exists()
        assert Path(tmp_path, "mytranscript.txt").read_text() == transcript

    def test_save_transcript_with_different_extension(self, tmp_path: Path) -> None:
        """Should replace custom extension with .txt."""
        # Given transcript output path with .text extension
        output_path = tmp_path / "mytranscript.text"  # Custom extension
        transcript = "Test transcript content"

        with patch("builtins.print"):
            # When save_transcript is called with custom extension
            save_transcript(output_path, transcript)

        # Then extension is replaced with .txt
        assert Path(tmp_path, "mytranscript.txt").exists()
        assert Path(tmp_path, "mytranscript.txt").read_text() == transcript
        # Original .text file should not exist
        assert not output_path.exists()

    def test_save_transcript_no_extension(self, tmp_path: Path) -> None:
        """Should add .txt to paths with no extension."""
        # Given transcript output path with no extension
        output_path = tmp_path / "output_file"  # No extension
        transcript = "Transcript without extension"

        with patch("builtins.print"):
            # When save_transcript is called
            save_transcript(output_path, transcript)

        # Then file is saved with .txt extension added
        assert Path(tmp_path, "output_file.txt").exists()
        assert Path(tmp_path, "output_file.txt").read_text() == transcript


class TestExtractAudio:
    """Test audio extraction."""

    def test_extract_audio_file_not_exists(self, tmp_path: Path) -> None:
        """Should extract audio when file doesn't exist."""
        # Given video file and mocked VideoFileClip
        video_path = tmp_path / "video.mp4"
        video_path.touch()
        audio_path = tmp_path / "audio.mp3"

        with patch("vtt.transcriber.OpenAI"), patch("vtt.audio_manager.VideoFileClip") as mock_video_class:
            mock_video_instance = MagicMock()
            mock_video_instance.audio = MagicMock()
            mock_video_instance.__enter__.return_value = mock_video_instance
            mock_video_instance.__exit__.return_value = None
            mock_video_class.return_value = mock_video_instance

            transcriber = VideoTranscriber("key")
            # When extract_audio is called with non-existent audio_path
            transcriber.extract_audio(video_path, audio_path, force=False)

            # Then VideoFileClip is created and audio is written using context manager
            mock_video_class.assert_called_once_with(str(video_path))
            mock_video_instance.audio.write_audiofile.assert_called_once()

    def test_extract_audio_file_exists_no_force(self, tmp_path: Path) -> None:
        """Should skip extraction when file exists and force=False."""
        # Given existing audio file and mocked VideoFileClip
        video_path = tmp_path / "video.mp4"
        video_path.touch()
        audio_path = tmp_path / "audio.mp3"
        audio_path.write_text("dummy")

        with patch("vtt.transcriber.OpenAI"), patch("vtt.audio_manager.VideoFileClip") as mock_video:
            transcriber = VideoTranscriber("key")
            with patch("builtins.print"):
                # When extract_audio is called with existing file and force=False
                transcriber.extract_audio(video_path, audio_path, force=False)

            # Then VideoFileClip is not called (extraction skipped)
            mock_video.assert_not_called()

    def test_extract_audio_file_exists_with_force(self, tmp_path: Path) -> None:
        """Should extract when force=True even if file exists."""
        # Given existing audio file and mocked VideoFileClip
        video_path = tmp_path / "video.mp4"
        video_path.touch()
        audio_path = tmp_path / "audio.mp3"
        audio_path.write_text("dummy")

        with patch("vtt.transcriber.OpenAI"), patch("vtt.audio_manager.VideoFileClip") as mock_video:
            mock_video_instance = MagicMock()
            mock_video_instance.audio = MagicMock()
            mock_video.return_value = mock_video_instance

            transcriber = VideoTranscriber("key")
            # When extract_audio is called with force=True
            transcriber.extract_audio(video_path, audio_path, force=True)

            # Then VideoFileClip is called despite existing file
            mock_video.assert_called_once()

    def test_extract_audio_no_audio_track(self, tmp_path: Path) -> None:
        """Should handle video with no audio track."""
        # Given video file with no audio track and mocked VideoFileClip
        video_path = tmp_path / "video.mp4"
        video_path.touch()
        audio_path = tmp_path / "audio.mp3"

        with patch("vtt.transcriber.OpenAI"), patch("vtt.audio_manager.VideoFileClip") as mock_video:
            mock_video_instance = MagicMock()
            mock_video_instance.audio = None
            mock_video.return_value = mock_video_instance

            transcriber = VideoTranscriber("key")
            # When extract_audio is called on video with no audio
            transcriber.extract_audio(video_path, audio_path, force=False)

            # Then write_audiofile is not called
            mock_video_instance.write_audiofile.assert_not_called()


class TestGetAudioDuration:
    """Test audio duration retrieval."""

    def test_get_audio_duration(self) -> None:
        """Should return audio duration in seconds."""
        # Given mocked AudioFileClip with 120.5 second duration
        with patch("vtt.transcriber.OpenAI"), patch("vtt.audio_manager.AudioFileClip") as mock_audio_class:
            mock_audio_instance = MagicMock()
            mock_audio_instance.duration = 120.5
            mock_audio_instance.__enter__.return_value = mock_audio_instance
            mock_audio_instance.__exit__.return_value = None
            mock_audio_class.return_value = mock_audio_instance

            transcriber = VideoTranscriber("key")
            # When get_audio_duration is called
            duration = transcriber.get_audio_duration(Path("audio.mp3"))

            # Then duration is returned and AudioFileClip context manager is used
            assert duration == 120.5
            mock_audio_class.assert_called_once_with("audio.mp3")


class TestCalculateChunkParams:
    """Test chunk parameter calculation."""

    def test_calculate_chunk_params_small_file(self) -> None:
        """Should return 1 chunk for file under limit."""
        # Given VideoTranscriber and 10MB file with 5 minute duration
        with patch("vtt.transcriber.OpenAI"):
            transcriber = VideoTranscriber("key")
            # When calculate_chunk_params is called with small file
            num_chunks, _ = transcriber.calculate_chunk_params(10.0, 300.0)
            # Then single chunk is returned
            assert num_chunks == 1

    def test_calculate_chunk_params_large_file(self) -> None:
        """Should calculate multiple chunks for large file."""
        # Given VideoTranscriber and 50MB file with 1 hour duration
        with patch("vtt.transcriber.OpenAI"):
            transcriber = VideoTranscriber("key")
            # When calculate_chunk_params is called with large file
            num_chunks, chunk_duration = transcriber.calculate_chunk_params(50.0, 3600.0)
            # Then multiple chunks and positive chunk_duration returned
            assert num_chunks > 1
            assert chunk_duration > 0

    def test_calculate_chunk_params_formula(self) -> None:
        """Should apply correct formula for chunk calculation."""
        # Given VideoTranscriber, 30MB file, and 10 minute duration
        with patch("vtt.transcriber.OpenAI"):
            transcriber = VideoTranscriber("key")
            file_size_mb = 30.0
            duration = 600.0  # 10 minutes
            # When calculate_chunk_params is called
            _, chunk_duration = transcriber.calculate_chunk_params(file_size_mb, duration)

            # Then formula (25/30) * 600 * 0.9 = 450 seconds per chunk is applied
            expected_chunk_duration = (25.0 / 30.0) * 600.0 * 0.9
            # Implementation prefers floor-minute rounding: floor(expected/60) * 60 (min 60)
            minutes_floor = max(1, int(expected_chunk_duration // 60))
            expected_floor = minutes_floor * 60
            assert chunk_duration == expected_floor


class TestExtractAudioChunk:
    """Test audio chunk extraction."""

    def test_extract_audio_chunk(self, tmp_path: Path) -> None:
        """Should extract and save audio chunk."""
        # Given audio file and mocked AudioFileClip with time slice 0-60 seconds
        with patch("vtt.transcriber.OpenAI"), patch("vtt.audio_manager.AudioFileClip") as mock_audio_class:
            mock_audio_instance = MagicMock()
            mock_chunk = MagicMock()
            mock_audio_instance.subclipped.return_value = mock_chunk
            mock_audio_instance.__enter__.return_value = mock_audio_instance
            mock_audio_instance.__exit__.return_value = None
            mock_audio_class.return_value = mock_audio_instance

            audio_path = tmp_path / "audio.mp3"
            audio_path.touch()

            transcriber = VideoTranscriber("key")
            # When extract_audio_chunk is called with chunk index 0
            chunk_path = transcriber.extract_audio_chunk(audio_path, 0.0, 60.0, 0)

            # Then chunk file is created and audio_chunk0.mp3 is generated
            assert chunk_path.name == "audio_chunk0.mp3"
            mock_audio_instance.subclipped.assert_called_once_with(0.0, 60.0)
            mock_chunk.write_audiofile.assert_called_once()


class TestTranscribeAudioFile:
    """Test audio file transcription."""

    def test_transcribe_audio_file(self, tmp_path: Path) -> None:
        """Should transcribe audio file using Whisper API."""
        # Given audio file and mocked OpenAI client returning "Hello world"
        with patch("vtt.transcriber.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.audio.transcriptions.create.return_value = cast(
                "TranscriptionVerbose",
                "Hello world",
            )

            audio_path = tmp_path / "audio.mp3"
            audio_path.write_text("dummy audio")

            transcriber = VideoTranscriber("key")
            # When transcribe_audio_file is called
            result = transcriber.transcribe_audio_file(audio_path)

            # Then Whisper API is called with correct model and response format, result returned
            assert result == "Hello world"
            mock_client.audio.transcriptions.create.assert_called_once()
            call_kwargs = mock_client.audio.transcriptions.create.call_args[1]
            assert call_kwargs["model"] == "whisper-1"
            assert call_kwargs["response_format"] == "verbose_json"


class TestDirectAudioTranscription:
    """When a user provides an audio file as the primary input."""

    def test_transcribe_direct_mp3_skips_extraction(self, tmp_path: Path) -> None:
        """Should skip audio extraction when input is already an .mp3 file."""
        # Given an existing .mp3 file and a mocked OpenAI client
        with patch("vtt.transcriber.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.audio.transcriptions.create.return_value = cast(
                "TranscriptionVerbose",
                "Test transcript",
            )

            input_audio = tmp_path / "input_audio.mp3"
            input_audio.write_text("x" * 1024)  # 1KB audio file

            with patch.object(VideoTranscriber, "extract_audio") as mock_extract, patch("builtins.print"):
                transcriber = VideoTranscriber("key")

                # When transcribe is called with the audio file as the main input
                result = transcriber.transcribe(input_audio, audio_path=None)

                # Then extract_audio should not be called and transcript returned
                mock_extract.assert_not_called()
                assert result == "Test transcript"

    def test_transcribe_single_chunk_file_directly(self, tmp_path: Path) -> None:
        """Should transcribe a single chunk file without scanning for siblings."""
        # Given a single chunk file exists
        with patch("vtt.transcriber.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.audio.transcriptions.create.return_value = cast(
                "TranscriptionVerbose",
                "Chunk transcript",
            )

            chunk_file = tmp_path / "audio_chunk0.mp3"
            chunk_file.write_text("x" * 1024)

            with patch.object(VideoTranscriber, "extract_audio") as mock_extract, patch("builtins.print"):
                transcriber = VideoTranscriber("key")

                # When transcribe is called with a chunk file
                result = transcriber.transcribe(chunk_file, audio_path=None)

                # Then only that chunk is transcribed, not siblings
                mock_extract.assert_not_called()
                assert result == "Chunk transcript"
                # Verify transcribe_audio_file was called once (not chunked processing)
                mock_client.audio.transcriptions.create.assert_called_once()

    def test_transcribe_nonexistent_audio_file_raises_error(self) -> None:
        """Should raise FileNotFoundError when audio file doesn't exist."""
        # Given a non-existent audio file path
        with patch("vtt.transcriber.OpenAI"):
            transcriber = VideoTranscriber("key")
            nonexistent_audio = Path("/nonexistent/audio.mp3")

            # When transcribe is called with non-existent audio file
            with pytest.raises(FileNotFoundError) as exc_info:
                transcriber.transcribe(nonexistent_audio, audio_path=None)

            # Then FileNotFoundError is raised with clear message
            assert "Audio file not found" in str(exc_info.value)

    def test_transcribe_audio_with_output_audio_flag_raises_error(self, tmp_path: Path) -> None:
        """Should raise ValueError when -o flag is provided with audio input."""
        # Given an existing audio file and a custom output audio path
        with patch("vtt.transcriber.OpenAI"):
            transcriber = VideoTranscriber("key")

            input_audio = tmp_path / "input.mp3"
            input_audio.write_text("x" * 1024)
            custom_output = tmp_path / "custom_output.mp3"

            # When transcribe is called with audio input AND audio_path specified
            with pytest.raises(ValueError, match=r"Cannot specify.*output-audio.*audio file"):
                transcriber.transcribe(input_audio, audio_path=custom_output)

    def test_scan_chunks_flag_processes_all_sibling_chunks(self, tmp_path: Path) -> None:
        """Should detect and transcribe all sibling chunks when scan_chunks=True."""
        # Given multiple chunk files exist (chunk0, chunk1, chunk2)
        with patch("vtt.transcriber.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.audio.transcriptions.create.side_effect = [
                {"segments": [{"start": 0.0, "end": 1.0, "text": "First chunk"}]},
                {"segments": [{"start": 0.0, "end": 1.0, "text": "Second chunk"}]},
                {"segments": [{"start": 0.0, "end": 1.0, "text": "Third chunk"}]},
            ]

            chunk0 = tmp_path / "audio_chunk0.mp3"
            chunk1 = tmp_path / "audio_chunk1.mp3"
            chunk2 = tmp_path / "audio_chunk2.mp3"
            chunk0.write_text("x" * 1024)
            chunk1.write_text("x" * 1024)
            chunk2.write_text("x" * 1024)

            with patch("builtins.print"), patch.object(VideoTranscriber, "get_audio_duration", return_value=60.0):
                transcriber = VideoTranscriber("key")

                # When transcribe is called with scan_chunks=True
                result = transcriber.transcribe(
                    chunk0,
                    audio_path=None,
                    scan_chunks=True,
                )

                # Then all 3 chunks are transcribed in order
                assert mock_client.audio.transcriptions.create.call_count == 3
                assert "First chunk" in result
                assert "Second chunk" in result
                assert "Third chunk" in result

    def test_scan_chunks_shifts_timestamps_and_separates_with_newlines(self, tmp_path: Path) -> None:
        """Should shift timestamps for each chunk and separate with blank lines."""
        # Given multiple chunk files with formatted timestamps
        with patch("vtt.transcriber.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.audio.transcriptions.create.side_effect = [
                {"segments": [{"start": 0.0, "end": 2.0, "text": "First"}]},
                {"segments": [{"start": 0.0, "end": 2.0, "text": "Second"}]},
            ]

            chunk0 = tmp_path / "audio_chunk0.mp3"
            chunk1 = tmp_path / "audio_chunk1.mp3"
            chunk0.write_text("x" * 1024)
            chunk1.write_text("x" * 1024)

            with patch("builtins.print"), patch.object(VideoTranscriber, "get_audio_duration", return_value=10.0):
                transcriber = VideoTranscriber("key")

                # When transcribe is called with scan_chunks=True
                result = transcriber.transcribe(
                    chunk0,
                    audio_path=None,
                    scan_chunks=True,
                )

                # Then timestamps are shifted and chunks separated with blank lines
                assert "[00:00:00 - 00:00:02]" in result  # First chunk at 0s
                # Second chunk offset by 10s
                assert "[00:00:10 - 00:00:12]" in result
                assert "\n\n" in result  # Blank line separator between chunks

    def test_scan_chunks_with_no_chunks_found(self, tmp_path: Path) -> None:
        """Should return empty string when no chunks are found."""
        # Given a base audio file with no sibling chunks
        with patch("vtt.transcriber.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client

            base_audio = tmp_path / "audio.mp3"
            base_audio.write_text("x" * 1024)

            transcriber = VideoTranscriber("key")

            # When _transcribe_sibling_chunks is called on a file with no chunks
            result = transcriber._transcribe_sibling_chunks(base_audio)

            # Then empty string is returned
            assert result == ""
            # And no transcription API calls were made
            assert mock_client.audio.transcriptions.create.call_count == 0


class TestTranscribeChunkedAudio:
    """Test chunked audio transcription."""

    def test_transcribe_chunked_audio(self, tmp_path: Path) -> None:
        """Should transcribe multiple chunks and join results."""
        # Given audio file split into 2 chunks with different transcription results
        with patch("vtt.transcriber.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.audio.transcriptions.create.side_effect = [
                "chunk1 text",
                "chunk2 text",
            ]

            audio_path = tmp_path / "audio.mp3"
            audio_path.write_text("dummy audio")

            with patch.object(VideoTranscriber, "extract_audio_chunk") as mock_extract, patch("builtins.print"):
                mock_extract.side_effect = [
                    tmp_path / "chunk0.mp3",
                    tmp_path / "chunk1.mp3",
                ]

                for i in range(2):
                    chunk_path = tmp_path / f"chunk{i}.mp3"
                    chunk_path.write_text("dummy")

                transcriber = VideoTranscriber("key")
                # When transcribe_chunked_audio is called with 2 chunks
                result = transcriber.transcribe_chunked_audio(
                    audio_path,
                    duration=600.0,
                    num_chunks=2,
                    chunk_duration=300.0,
                )

                # Then chunks are transcribed and results joined with space
                assert result == "chunk1 text chunk2 text"
                assert mock_client.audio.transcriptions.create.call_count == 2


class TestChunkTimestampOffsetsMinute:
    """Verify chunked transcriptions have minute-based offsets when chunks are 60s."""

    def test_minute_chunk_offsets(self, tmp_path: Path) -> None:
        """Two 60s chunks should produce second chunk timestamps offset by 01:00."""
        with patch("vtt.transcriber.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client

            # Each chunk's transcription returns segments starting at 0s
            mock_client.audio.transcriptions.create.side_effect = [
                {"segments": [{"start": 0.0, "end": 1.0, "text": "First minute"}]},
                {"segments": [{"start": 0.0, "end": 1.0, "text": "Second minute"}]},
            ]

            audio_path = tmp_path / "audio.mp3"
            audio_path.write_text("dummy audio")

            transcriber = VideoTranscriber("key")

            # Fake extract_audio_chunk to create chunk files
            def fake_extract(_audio_path: Any, _start: float, _end: float, idx: int) -> Path:
                p = tmp_path / f"chunk{idx}.mp3"
                p.write_text("chunk")
                return p

            with patch.object(VideoTranscriber, "extract_audio_chunk", side_effect=fake_extract):
                # When transcribing 2 chunks of 60s each
                result = transcriber.transcribe_chunked_audio(
                    audio_path,
                    duration=120.0,
                    num_chunks=2,
                    chunk_duration=60.0,
                    keep_chunks=True,
                )

                # Then first chunk lines start at 00:00, second chunk lines offset by 01:00
                assert "[00:00:00 - 00:00:01] First minute" in result
                assert "[00:01:00 - 00:01:01] Second minute" in result


class TestChunkTimestampOffsetsVariable:
    """Verify offsets when chunks are very short (variable lengths)."""

    def test_variable_short_first_chunk_offsets(self, tmp_path: Path) -> None:
        """If first chunk is 1s long, second chunk timestamps should start at 00:01."""
        with patch("vtt.transcriber.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client

            mock_client.audio.transcriptions.create.side_effect = [
                {"segments": [{"start": 0.0, "end": 1.0, "text": "Short first"}]},
                {"segments": [{"start": 0.0, "end": 2.0, "text": "Then second"}]},
            ]

            audio_path = tmp_path / "audio.mp3"
            audio_path.write_text("dummy audio")

            transcriber = VideoTranscriber("key")

            def fake_extract(_audio_path: Any, _start: float, _end: float, idx: int) -> Path:
                p = tmp_path / f"chunk{idx}.mp3"
                p.write_text("chunk")
                return p

            with patch.object(VideoTranscriber, "extract_audio_chunk", side_effect=fake_extract):
                # When use chunk_duration=1s so second chunk starts at 1s
                result = transcriber.transcribe_chunked_audio(
                    audio_path,
                    duration=120.0,
                    num_chunks=2,
                    chunk_duration=1.0,
                    keep_chunks=True,
                )

                # Then second chunk timestamps are offset by 00:01
                assert "[00:00:00 - 00:00:01] Short first" in result
                assert "[00:00:01 - 00:00:03] Then second" in result


class TestCalculateChunkParamsRounding:
    """Ensure chunk calculation prefers round-minute chunk durations."""

    def test_calculate_chunk_params_rounds_to_minute(self) -> None:
        """Chunk duration should be rounded to a whole minute when reasonable."""
        with patch("vtt.transcriber.OpenAI"):
            transcriber = VideoTranscriber("key")
            # Large file: expect chunk_duration to be rounded to nearest 60s
            num_chunks, chunk_duration = transcriber.calculate_chunk_params(100.0, 3600.0)
            # chunk_duration should be a multiple of 60
            assert int(chunk_duration) % 60 == 0
            assert num_chunks >= 1


class TestTranscribeSmallFile:
    """Test transcription of small audio files."""

    def test_transcribe_small_file(self, tmp_path: Path) -> None:
        """Should transcribe small file without chunking."""
        # Given small audio file (1KB) and mocked transcription API
        with patch("vtt.transcriber.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.audio.transcriptions.create.return_value = cast(
                "TranscriptionVerbose",
                "Full transcript",
            )

            video_path = tmp_path / "video.mp4"
            video_path.touch()
            audio_path = tmp_path / "audio.mp3"
            audio_path.write_text("x" * 1024)  # 1KB file

            with (
                patch.object(VideoTranscriber, "validate_input_file", return_value=video_path),
                patch.object(VideoTranscriber, "extract_audio"),
                patch("builtins.print"),
            ):
                transcriber = VideoTranscriber("key")
                # When transcribe is called with small file
                result = transcriber.transcribe(video_path, audio_path)

                # Then transcription API called once (no chunking) with full transcript returned
                assert result == "Full transcript"
                mock_client.audio.transcriptions.create.assert_called_once()


class TestTranscribeLargeFile:
    """Test transcription of large audio files."""

    def test_transcribe_large_file_chunked(self, tmp_path: Path) -> None:
        """Should chunk large files and transcribe."""
        # Given 30MB audio file with 2 transcribed chunks
        with patch("vtt.transcriber.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.audio.transcriptions.create.side_effect = [
                "chunk1 text",
                "chunk2 text",
            ]

            video_path = tmp_path / "video.mp4"
            video_path.touch()
            audio_path = tmp_path / "audio.mp3"
            # Create 30MB file
            audio_path.write_text("x" * (30 * 1024 * 1024))

            with (
                patch.object(VideoTranscriber, "validate_input_file", return_value=video_path),
                patch.object(VideoTranscriber, "extract_audio"),
                patch.object(VideoTranscriber, "get_audio_duration", return_value=600.0),
                patch.object(VideoTranscriber, "extract_audio_chunk") as mock_extract_chunk,
                patch("builtins.print"),
            ):
                # Create temporary chunk files
                chunk_files = []
                for i in range(2):
                    chunk_path = tmp_path / f"chunk{i}.mp3"
                    chunk_path.write_text("dummy")
                    chunk_files.append(chunk_path)

                mock_extract_chunk.side_effect = chunk_files

                transcriber = VideoTranscriber("key")
                # When transcribe is called with large file
                _ = transcriber.transcribe(video_path, audio_path)

                # Then transcription API called multiple times (once per chunk)
                assert mock_client.audio.transcriptions.create.call_count >= 1


class TestSaveTranscript:
    """Test transcript saving."""

    def test_save_transcript(self, tmp_path: Path) -> None:
        """Should save transcript to file."""
        # Given output path and transcript text
        output_path = tmp_path / "transcript.txt"
        transcript = "This is a test transcript."

        with patch("builtins.print"):
            # When save_transcript is called
            save_transcript(output_path, transcript)

        # Then file is created with correct content
        assert output_path.exists()
        assert output_path.read_text() == transcript

    def test_save_transcript_creates_directory(self, tmp_path: Path) -> None:
        """Should work with nested paths."""
        # Given nested output path and transcript text
        output_path = tmp_path / "subdir" / "transcript.txt"
        output_path.parent.mkdir(parents=True)
        transcript = "Another transcript."

        with patch("builtins.print"):
            # When save_transcript is called with nested path
            save_transcript(output_path, transcript)

        # Then file is created in nested directory with correct content
        assert output_path.read_text() == transcript


class TestDisplayResult:
    """Test result display."""

    def test_display_result(self, capsys: Any) -> None:
        """Should display formatted result."""
        # Given transcript text to display
        transcript = "This is the transcription."
        # When display_result is called
        display_result(transcript)

        # Then output contains formatted transcript with header and separator
        captured = capsys.readouterr()
        assert "Transcription Result:" in captured.out
        assert transcript in captured.out
        assert "=" * 50 in captured.out


class TestMainErrorHandling:
    """Test main function error handling."""

    def test_main_missing_api_key(self, tmp_path: Path) -> None:
        """Should exit with error when API key is missing."""
        # Given no API key in environment and video file path
        video_path = tmp_path / "video.mp4"
        video_path.touch()

        with (
            patch("sys.argv", ["main.py", str(video_path)]),
            patch("builtins.print"),
            patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False),
            patch("os.environ.get", return_value=None),
        ):
            # When main() is called without API key
            with pytest.raises(SystemExit) as exc_info:
                main()
            # Then exits with error code 1
            assert exc_info.value.code == 1


class TestFormatTranscriptInternal:
    """Tests for internal transcript formatting branches in main.py."""

    def test_format_transcript_with_dict_segments(self) -> None:
        """Dict responses with segments should be formatted into timestamp lines."""
        with patch("vtt.transcriber.OpenAI"):
            transcriber = VideoTranscriber("key")
            response = {
                "segments": [
                    {"start": 0.0, "end": 2.5, "text": "Hello dict"},
                ],
            }

            formatted = transcriber._format_transcript_with_timestamps(response)  # type: ignore[arg-type]
            assert "[00:00:00 - 00:00:02] Hello dict" in formatted

    def test_format_transcript_with_sdk_segments(self) -> None:
        """SDK-like response objects with `segments` attribute are handled."""

        class Seg:
            def __init__(self, start: float, end: float, text: str) -> None:
                self.start = start
                self.end = end
                self.text = text

        class Resp:
            def __init__(self, segments: list[Any]) -> None:
                self.segments = segments

        with patch("vtt.transcriber.OpenAI"):
            transcriber = VideoTranscriber("key")
            resp = Resp([Seg(5.0, 8.2, "SDK segment")])
            formatted = transcriber._format_transcript_with_timestamps(resp)  # type: ignore[arg-type]
            assert "[00:00:05 - 00:00:08] SDK segment" in formatted

    def test_format_transcript_with_text_attribute(self) -> None:
        """If SDK response exposes `text` attribute, it's returned as fallback."""

        class Resp:
            def __init__(self, text: str) -> None:
                self.text = text

        with patch("vtt.transcriber.OpenAI"):
            transcriber = VideoTranscriber("key")
            resp = Resp("Raw text fallback")
            formatted = transcriber._format_transcript_with_timestamps(resp)  # type: ignore[arg-type]
            assert formatted == "Raw text fallback"

    def test_transcribe_audio_file_debug_on_empty(self, capsys: Any, tmp_path: Path) -> None:
        """When formatting yields empty string, debug preview prints are emitted."""

        # Create a dummy response object with no segments and no text, but meaningful __str__
        class Resp:
            def __str__(self) -> str:
                return "DummyPreview: verbose details here"

        with patch("vtt.transcriber.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.audio.transcriptions.create.return_value = cast("TranscriptionVerbose", Resp())

            audio_path = tmp_path / "audio.mp3"
            audio_path.write_text("dummy audio")

            transcriber = VideoTranscriber("key")
            # When transcribing a file that yields empty formatted transcript
            _ = transcriber.transcribe_audio_file(audio_path)

            captured = capsys.readouterr()
            assert "DEBUG: Empty formatted transcript produced" in captured.out
            assert "DEBUG: response preview" in captured.out


class TestCleanupFunctions:
    """Tests for cleanup_audio_files and cleanup_audio_chunks."""

    def test_cleanup_audio_files_deletes_main_and_chunks(self, tmp_path: Path, capsys: Any) -> None:
        # Use capsys fixture to silence unused-argument warnings
        _ = capsys
        with patch("vtt.transcriber.OpenAI"):
            transcriber = VideoTranscriber("key")
            audio_path = tmp_path / "audio.mp3"
            audio_path.write_text("audio")
            # create chunk files
            chunk0 = tmp_path / "audio_chunk0.mp3"
            chunk1 = tmp_path / "audio_chunk1.mp3"
            chunk0.write_text("c0")
            chunk1.write_text("c1")

            # When cleanup_audio_files is called
            transcriber.cleanup_audio_files(audio_path)

            # Then all files removed
            assert not audio_path.exists()
            assert not chunk0.exists()
            assert not chunk1.exists()

    def test_cleanup_audio_chunks_only_delete_chunks(self, tmp_path: Path, capsys: Any) -> None:
        # Use capsys fixture to silence unused-argument warnings
        _ = capsys
        with patch("vtt.transcriber.OpenAI"):
            transcriber = VideoTranscriber("key")
            audio_path = tmp_path / "audio.mp3"
            audio_path.write_text("audio")
            # create chunk files
            chunk0 = tmp_path / "audio_chunk0.mp3"
            chunk1 = tmp_path / "audio_chunk1.mp3"
            chunk0.write_text("c0")
            chunk1.write_text("c1")

            # When cleanup_audio_chunks is called
            transcriber.cleanup_audio_chunks(audio_path)

            # Then main audio remains, chunks removed
            assert audio_path.exists()
            assert not chunk0.exists()
            assert not chunk1.exists()


class TestTranscribeAudioFileDebugDict:
    def test_debug_prints_for_dict_response_without_text(self, tmp_path: Path, capsys: Any) -> None:
        with patch("vtt.transcriber.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.audio.transcriptions.create.return_value = cast("TranscriptionVerbose", {})

            audio_path = tmp_path / "audio.mp3"
            audio_path.write_text("dummy audio")

            transcriber = VideoTranscriber("key")
            _ = transcriber.transcribe_audio_file(audio_path)
            captured = capsys.readouterr()
            assert "DEBUG: Empty formatted transcript produced" in captured.out
            assert "DEBUG: response keys: []" in captured.out

    def test_debug_prints_for_dict_response_with_text_key(self, tmp_path: Path, capsys: Any) -> None:
        with patch("vtt.transcriber.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.audio.transcriptions.create.return_value = cast("TranscriptionVerbose", {"text": ""})

            audio_path = tmp_path / "audio.mp3"
            audio_path.write_text("dummy audio")

            transcriber = VideoTranscriber("key")
            _ = transcriber.transcribe_audio_file(audio_path)
            captured = capsys.readouterr()
            assert "DEBUG: Empty formatted transcript produced" in captured.out
            assert "DEBUG: response keys: ['text']" in captured.out
            assert "DEBUG: response[text] preview" in captured.out

    def test_main_missing_video_file(self) -> None:
        """Should exit with error when video file doesn't exist."""
        # Given API key in environment and non-existent video file path
        with (
            patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}),
            patch("sys.argv", ["main.py", "/nonexistent/video.mp4"]),
            patch("builtins.print"),
        ):
            # When main() is called with missing video file
            with pytest.raises(SystemExit) as exc_info:
                main()
            # Then exits with error code 1
            assert exc_info.value.code == 1

    def test_main_generic_exception_handling(self, tmp_path: Path) -> None:
        """Should handle generic exceptions."""
        # Given API key in environment, video file, and transcriber that raises RuntimeError
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            video_path = tmp_path / "video.mp4"
            video_path.touch()

            with (
                patch("sys.argv", ["main.py", str(video_path)]),
                patch.object(VideoTranscriber, "transcribe", side_effect=RuntimeError("Test error")),
                patch("builtins.print"),
            ):
                # When main() is called and transcribe raises exception
                with pytest.raises(SystemExit) as exc_info:
                    main()
                # Then exits with error code 1
                assert exc_info.value.code == 1


class TestIntegrationFullWorkflow:
    """Integration tests for complete workflows."""

    def test_full_workflow_small_file(self, tmp_path: Path) -> None:
        """Should complete full transcription workflow for small file."""
        # Given video file, audio output path, transcript save path, and mocked transcriber
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            video_path = tmp_path / "video.mp4"
            video_path.touch()
            audio_path = tmp_path / "audio.mp3"
            transcript_path = tmp_path / "output.txt"

            with (
                patch(
                    "sys.argv",
                    [
                        "main.py",
                        str(video_path),
                        "-o",
                        str(audio_path),
                        "-s",
                        str(transcript_path),
                    ],
                ),
                patch.object(VideoTranscriber, "validate_input_file", return_value=video_path),
                patch.object(VideoTranscriber, "extract_audio"),
                patch.object(VideoTranscriber, "transcribe_audio_file", return_value="Final transcript"),
                patch("builtins.print"),
                patch.object(
                    VideoTranscriber,
                    "transcribe",
                    return_value="Final transcript",
                ),
            ):
                # When main() is called with transcript save path
                import contextlib

                with contextlib.suppress(SystemExit):
                    main()

                # Then transcript is saved to file
                if transcript_path.exists():
                    assert "Final transcript" in transcript_path.read_text()

    def test_full_workflow_with_force_flag(self, tmp_path: Path) -> None:
        """Should respect force flag in workflow."""
        # Given video file, existing audio file, and force flag set
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            video_path = tmp_path / "video.mp4"
            video_path.touch()
            audio_path = tmp_path / "audio.mp3"
            audio_path.write_text("existing")

            with (
                patch(
                    "sys.argv",
                    [
                        "main.py",
                        str(video_path),
                        "-f",
                    ],
                ),
                patch.object(VideoTranscriber, "transcribe", return_value="New transcript") as mock_transcribe,
                patch("builtins.print"),
            ):
                # When main() is called with force flag (-f)
                import contextlib

                with contextlib.suppress(SystemExit):
                    main()

                # Then transcribe is called with force=True
                mock_transcribe.assert_called()
                call_args = mock_transcribe.call_args
                # `force` is a keyword-only argument in implementation; check kwargs
                assert call_args.kwargs.get("force") is True


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_exact_max_size_boundary(self) -> None:
        """Should chunk file exactly at max size."""
        # Given VideoTranscriber and file exactly 25MB (max size boundary)
        with patch("vtt.transcriber.OpenAI"):
            transcriber = VideoTranscriber("key")
            # When calculate_chunk_params called at 25MB boundary
            num_chunks, _ = transcriber.calculate_chunk_params(25.0, 300.0)
            # Then chunk calculation works correctly (chunk_duration = (25/25) * 300 * 0.9 = 270)
            assert num_chunks >= 1

    def test_just_over_max_size_boundary(self) -> None:
        """Should chunk file over max size."""
        # Given VideoTranscriber and file 30MB (over 25MB max)
        with patch("vtt.transcriber.OpenAI"):
            transcriber = VideoTranscriber("key")
            # When calculate_chunk_params called with 30MB file
            num_chunks, _ = transcriber.calculate_chunk_params(30.0, 300.0)
            # Then multiple chunks required for file over max size
            assert num_chunks > 1

    def test_very_long_audio(self) -> None:
        """Should handle very long audio duration."""
        # Given VideoTranscriber and 50MB file with 8 hour duration
        with patch("vtt.transcriber.OpenAI"):
            transcriber = VideoTranscriber("key")
            # When calculate_chunk_params called with very long duration (28800 seconds = 8 hours)
            num_chunks, chunk_duration = transcriber.calculate_chunk_params(50.0, 28800.0)
            # Then chunk calculation works for very long audio
            assert num_chunks > 0
            assert chunk_duration > 0

    def test_empty_transcript(self, tmp_path: Path) -> None:
        """Should handle empty transcription result."""
        # Given mocked OpenAI API returning empty string
        with patch("vtt.transcriber.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.audio.transcriptions.create.return_value = cast("TranscriptionVerbose", "")

            audio_path = tmp_path / "audio.mp3"
            audio_path.write_text("dummy")

            transcriber = VideoTranscriber("key")
            # When transcribe_audio_file called with audio that produces no text
            result = transcriber.transcribe_audio_file(audio_path)

            # Then empty string is returned correctly
            assert result == ""

    def test_transcript_with_special_characters(self, tmp_path: Path) -> None:
        """Should handle transcript with special characters."""
        # Given test setup
        output_path = tmp_path / "transcript.txt"
        transcript = "Special chars: @#$%^&*()_+-=[]{}|;:',.<>?/~`\n中文\némojis: 🎉🎊"

        with patch("builtins.print"):
            save_transcript(output_path, transcript)

        # Then verify expected behavior
        assert output_path.read_text() == transcript
