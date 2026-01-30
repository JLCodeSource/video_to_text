"""Tests for audio file management: force overwrite, keep/delete functionality."""

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, cast
from unittest.mock import MagicMock, patch

import pytest

from vtt.main import VideoTranscriber

if TYPE_CHECKING:
    from openai.types.audio.transcription_verbose import TranscriptionVerbose


class TestFindExistingChunks:
    """Test finding existing chunk files."""

    def test_find_no_chunks_when_none_exist(self) -> None:
        """Should return empty list when no chunk files exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Given audio path with no chunk files
            audio_path = Path(tmpdir) / "audio.mp3"
            audio_path.write_text("dummy")

            with patch("vtt.main.OpenAI"):
                transcriber = VideoTranscriber("key")
                # When find_existing_chunks is called
                chunks = transcriber.find_existing_chunks(audio_path)

                # Then empty list is returned
                assert chunks == []

    def test_find_existing_chunks(self) -> None:
        """Should return all chunk files in order."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Given audio path with multiple chunk files
            audio_path = Path(tmpdir) / "audio.mp3"
            audio_path.write_text("dummy")
            chunk0 = Path(tmpdir) / "audio_chunk0.mp3"
            chunk1 = Path(tmpdir) / "audio_chunk1.mp3"
            chunk2 = Path(tmpdir) / "audio_chunk2.mp3"
            chunk0.write_text("chunk0")
            chunk1.write_text("chunk1")
            chunk2.write_text("chunk2")

            with patch("vtt.main.OpenAI"):
                transcriber = VideoTranscriber("key")
                # When find_existing_chunks is called
                chunks = transcriber.find_existing_chunks(audio_path)

                # Then all chunks are returned in order
                assert len(chunks) == 3
                assert chunks[0] == chunk0
                assert chunks[1] == chunk1
                assert chunks[2] == chunk2

    def test_find_chunks_sorted_correctly(self) -> None:
        """Should return chunks sorted numerically even if created out of order."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Given audio chunks created in reverse order on filesystem
            audio_path = Path(tmpdir) / "audio.mp3"
            audio_path.write_text("dummy")
            chunk2 = Path(tmpdir) / "audio_chunk2.mp3"
            chunk0 = Path(tmpdir) / "audio_chunk0.mp3"
            chunk1 = Path(tmpdir) / "audio_chunk1.mp3"
            chunk2.write_text("chunk2")
            chunk0.write_text("chunk0")
            chunk1.write_text("chunk1")

            with patch("vtt.main.OpenAI"):
                transcriber = VideoTranscriber("key")
                # When find_existing_chunks is called
                chunks = transcriber.find_existing_chunks(audio_path)

                # Then chunks are returned sorted by numeric index
                assert chunks[0].name == "audio_chunk0.mp3"
                assert chunks[1].name == "audio_chunk1.mp3"
                assert chunks[2].name == "audio_chunk2.mp3"

    def test_find_chunks_parent_directory_not_exists(self) -> None:
        """Should return empty list gracefully when parent directory doesn't exist."""
        # Given audio path with non-existent parent directory
        audio_path = Path("/nonexistent/directory/that/does/not/exist/audio.mp3")

        with patch("vtt.main.OpenAI"):
            transcriber = VideoTranscriber("key")
            # When find_existing_chunks is called
            chunks = transcriber.find_existing_chunks(audio_path)

            # Then empty list is returned gracefully
            assert chunks == []


class TestCleanupAudioFiles:
    """Test cleanup of audio and chunk files."""

    def test_cleanup_removes_main_audio_file(self) -> None:
        """Should delete main audio file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Given main audio file exists
            audio_path = Path(tmpdir) / "audio.mp3"
            audio_path.write_text("audio data")
            assert audio_path.exists()

            with patch("vtt.main.OpenAI"), patch("builtins.print"):
                transcriber = VideoTranscriber("key")
                # When cleanup_audio_files is called
                transcriber.cleanup_audio_files(audio_path)

                # Then main audio file is deleted
                assert not audio_path.exists()

    def test_cleanup_removes_chunk_files(self) -> None:
        """Should delete main audio file and all associated chunk files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Given main audio file and chunk files exist
            audio_path = Path(tmpdir) / "audio.mp3"
            audio_path.write_text("audio")
            chunk0 = Path(tmpdir) / "audio_chunk0.mp3"
            chunk1 = Path(tmpdir) / "audio_chunk1.mp3"
            chunk0.write_text("chunk0")
            chunk1.write_text("chunk1")

            with patch("vtt.main.OpenAI"), patch("builtins.print"):
                transcriber = VideoTranscriber("key")
                # When cleanup_audio_files is called
                transcriber.cleanup_audio_files(audio_path)

                # Then main audio and all chunk files are deleted
                assert not audio_path.exists()
                assert not chunk0.exists()
                assert not chunk1.exists()

    def test_cleanup_handles_missing_files(self) -> None:
        """Should handle missing files gracefully without raising errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Given audio file doesn't exist
            audio_path = Path(tmpdir) / "audio.mp3"

            with patch("vtt.main.OpenAI"), patch("builtins.print"):
                transcriber = VideoTranscriber("key")
                # When cleanup_audio_files is called
                # Then no exception is raised (graceful handling)
                transcriber.cleanup_audio_files(audio_path)


class TestCleanupAudioChunks:
    """Test cleanup of chunk files only."""

    def test_cleanup_removes_only_chunks(self) -> None:
        """Should delete only chunk files, keeping main audio file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Given main audio file and chunk files exist
            audio_path = Path(tmpdir) / "audio.mp3"
            audio_path.write_text("audio")
            chunk0 = Path(tmpdir) / "audio_chunk0.mp3"
            chunk1 = Path(tmpdir) / "audio_chunk1.mp3"
            chunk0.write_text("chunk0")
            chunk1.write_text("chunk1")

            with patch("vtt.main.OpenAI"), patch("builtins.print"):
                transcriber = VideoTranscriber("key")
                # When cleanup_audio_chunks is called
                transcriber.cleanup_audio_chunks(audio_path)

                # Then only chunk files are deleted, main audio file remains
                assert audio_path.exists()
                assert not chunk0.exists()
                assert not chunk1.exists()


class TestTranscribeChunkedAudioKeepChunks:
    """Test keeping chunk files during transcription."""

    def test_keep_chunks_false_deletes_chunks(self) -> None:
        """Should delete chunks after transcription when keep_chunks=False."""
        with patch("vtt.main.OpenAI") as mock_openai:
            # Given mock Whisper API and chunk files
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.audio.transcriptions.create.side_effect = ["chunk1", "chunk2"]

            with tempfile.TemporaryDirectory() as tmpdir:
                audio_path = Path(tmpdir) / "audio.mp3"
                audio_path.write_text("dummy")
                chunk0 = Path(tmpdir) / "audio_chunk0.mp3"
                chunk1 = Path(tmpdir) / "audio_chunk1.mp3"
                chunk0.write_text("c0")
                chunk1.write_text("c1")

                with patch.object(VideoTranscriber, "extract_audio_chunk") as mock_extract:
                    mock_extract.side_effect = [chunk0, chunk1]

                    with patch("builtins.print"):
                        transcriber = VideoTranscriber("key")
                        # When transcribe_chunked_audio is called with keep_chunks=False
                        result = transcriber.transcribe_chunked_audio(
                            audio_path,
                            duration=600.0,
                            num_chunks=2,
                            chunk_duration=300.0,
                            keep_chunks=False,
                        )

                        # Then chunks are deleted after transcription
                        assert result == "chunk1 chunk2"
                        assert not chunk0.exists()
                        assert not chunk1.exists()

    def test_keep_chunks_true_keeps_chunks(self) -> None:
        """Should keep chunks after transcription when keep_chunks=True."""
        with patch("vtt.main.OpenAI") as mock_openai:
            # Given mock Whisper API and chunk files
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.audio.transcriptions.create.side_effect = ["chunk1", "chunk2"]

            with tempfile.TemporaryDirectory() as tmpdir:
                audio_path = Path(tmpdir) / "audio.mp3"
                audio_path.write_text("dummy")
                chunk0 = Path(tmpdir) / "audio_chunk0.mp3"
                chunk1 = Path(tmpdir) / "audio_chunk1.mp3"
                chunk0.write_text("c0")
                chunk1.write_text("c1")

                with patch.object(VideoTranscriber, "extract_audio_chunk") as mock_extract:
                    mock_extract.side_effect = [chunk0, chunk1]

                    with patch("builtins.print"):
                        transcriber = VideoTranscriber("key")
                        # When transcribe_chunked_audio is called with keep_chunks=True
                        result = transcriber.transcribe_chunked_audio(
                            audio_path,
                            duration=600.0,
                            num_chunks=2,
                            chunk_duration=300.0,
                            keep_chunks=True,
                        )

                        # Then chunks are kept after transcription
                        assert result == "chunk1 chunk2"
                        assert chunk0.exists()
                        assert chunk1.exists()


class TestTranscribeWithKeepAudio:
    """Test transcribe method with keep_audio parameter."""

    def test_transcribe_keep_audio_true_keeps_files(self) -> None:
        """Should keep audio file after transcription when keep_audio=True."""
        with patch("vtt.main.OpenAI") as mock_openai:
            # Given mock Whisper API for small file transcription
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.audio.transcriptions.create.return_value = cast("TranscriptionVerbose", "transcript")

            with tempfile.TemporaryDirectory() as tmpdir:
                video_path = Path(tmpdir) / "video.mp4"
                video_path.touch()
                audio_path = Path(tmpdir) / "audio.mp3"
                audio_path.write_text("x" * 1024)

                with (
                    patch.object(VideoTranscriber, "validate_input_file", return_value=video_path),
                    patch.object(VideoTranscriber, "extract_audio"),
                    patch("builtins.print"),
                ):
                    transcriber = VideoTranscriber("key")
                    # When transcribe is called with keep_audio=True
                    result = transcriber.transcribe(video_path, audio_path, keep_audio=True)

                    # Then audio file is kept after transcription
                    assert result == "transcript"
                    assert audio_path.exists()

    def test_transcribe_keep_audio_false_deletes_files(self) -> None:
        """Should delete audio file after transcription when keep_audio=False."""
        with patch("vtt.main.OpenAI") as mock_openai:
            # Given mock Whisper API for small file transcription
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.audio.transcriptions.create.return_value = cast("TranscriptionVerbose", "transcript")

            with tempfile.TemporaryDirectory() as tmpdir:
                video_path = Path(tmpdir) / "video.mp4"
                video_path.touch()
                audio_path = Path(tmpdir) / "audio.mp3"
                audio_path.write_text("x" * 1024)

                with (
                    patch.object(VideoTranscriber, "validate_input_file", return_value=video_path),
                    patch.object(VideoTranscriber, "extract_audio"),
                    patch("builtins.print"),
                ):
                    transcriber = VideoTranscriber("key")
                    # When transcribe is called with keep_audio=False
                    result = transcriber.transcribe(video_path, audio_path, keep_audio=False)

                    # Then audio file is deleted after transcription
                    assert result == "transcript"
                    assert not audio_path.exists()


class TestTranscribeLargeWithKeepAudio:
    """Test transcribe with large files and keep_audio parameter."""

    def test_large_file_keep_audio_true_keeps_chunks(self) -> None:
        """Should keep chunks for large files when keep_audio=True."""
        with patch("vtt.main.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.audio.transcriptions.create.side_effect = ["chunk1", "chunk2"]

            with tempfile.TemporaryDirectory() as tmpdir:
                video_path = Path(tmpdir) / "video.mp4"
                video_path.touch()
                audio_path = Path(tmpdir) / "audio.mp3"
                audio_path.write_text("x" * (30 * 1024 * 1024))

                chunk0 = Path(tmpdir) / "audio_chunk0.mp3"
                chunk1 = Path(tmpdir) / "audio_chunk1.mp3"
                chunk0.write_text("c0")
                chunk1.write_text("c1")

                with (
                    patch.object(VideoTranscriber, "validate_input_file", return_value=video_path),
                    patch.object(VideoTranscriber, "extract_audio"),
                    patch.object(VideoTranscriber, "get_audio_duration", return_value=600.0),
                    patch.object(VideoTranscriber, "extract_audio_chunk") as mock_extract,
                    patch("builtins.print"),
                ):
                    mock_extract.side_effect = [chunk0, chunk1]

                    transcriber = VideoTranscriber("key")
                    _ = transcriber.transcribe(video_path, audio_path, keep_audio=True)

                    # Verify chunks are kept
                    assert chunk0.exists()
                    assert chunk1.exists()

    def test_large_file_keep_audio_false_deletes_chunks(self) -> None:
        """Should delete chunks for large files when keep_audio=False."""
        with patch("vtt.main.OpenAI") as mock_openai:
            # Given mock Whisper API and large audio file requiring chunking
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.audio.transcriptions.create.side_effect = ["chunk1", "chunk2"]

            with tempfile.TemporaryDirectory() as tmpdir:
                video_path = Path(tmpdir) / "video.mp4"
                video_path.touch()
                audio_path = Path(tmpdir) / "audio.mp3"
                audio_path.write_text("x" * (30 * 1024 * 1024))
                chunk0 = Path(tmpdir) / "audio_chunk0.mp3"
                chunk1 = Path(tmpdir) / "audio_chunk1.mp3"
                chunk0.write_text("c0")
                chunk1.write_text("c1")

                with (
                    patch.object(VideoTranscriber, "validate_input_file", return_value=video_path),
                    patch.object(VideoTranscriber, "extract_audio"),
                    patch.object(VideoTranscriber, "get_audio_duration", return_value=600.0),
                    patch.object(VideoTranscriber, "extract_audio_chunk") as mock_extract,
                    patch("builtins.print"),
                ):
                    mock_extract.side_effect = [chunk0, chunk1]
                    transcriber = VideoTranscriber("key")
                    # When transcribe is called with keep_audio=False
                    _ = transcriber.transcribe(video_path, audio_path, keep_audio=False)

                    # Then chunks are deleted after transcription
                    assert not chunk0.exists()
                    assert not chunk1.exists()
                    assert not audio_path.exists()

    class TestUseExistingChunks:
        """Ensure existing chunk files are used instead of re-extraction."""

        def test_transcribe_uses_existing_chunks(self) -> None:
            with patch("vtt.main.OpenAI") as mock_openai:
                mock_client = MagicMock()
                mock_openai.return_value = mock_client
                mock_client.audio.transcriptions.create.side_effect = ["chunk1", "chunk2"]

                with tempfile.TemporaryDirectory() as tmpdir:
                    video_path = Path(tmpdir) / "video.mp4"
                    video_path.touch()
                    audio_path = Path(tmpdir) / "audio.mp3"
                    # make file large enough to trigger chunking
                    audio_path.write_text("x" * (30 * 1024 * 1024))

                    # Create existing chunk files that should be reused
                    chunk0 = Path(tmpdir) / "audio_chunk0.mp3"
                    chunk1 = Path(tmpdir) / "audio_chunk1.mp3"
                    chunk0.write_text("c0")
                    chunk1.write_text("c1")

                    with (
                        patch.object(VideoTranscriber, "validate_input_file", return_value=video_path),
                        patch.object(VideoTranscriber, "extract_audio"),
                        patch.object(VideoTranscriber, "get_audio_duration", return_value=600.0),
                        patch.object(VideoTranscriber, "extract_audio_chunk") as mock_extract,
                        patch("builtins.print"),
                    ):
                        transcriber = VideoTranscriber("key")
                        _ = transcriber.transcribe(video_path, audio_path, keep_audio=True)

                        # extract_audio_chunk should not be called because chunks exist
                        mock_extract.assert_not_called()
                        assert chunk0.exists()
                        assert chunk1.exists()


class TestForceOverwriteWithExistingChunks:
    """Test force overwrite with existing chunk files."""

    def test_force_overwrite_with_existing_chunks(self) -> None:
        """Should pass force flag correctly when re-extracting audio."""
        with patch("vtt.main.OpenAI") as mock_openai:
            # Given existing audio and chunk files
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.audio.transcriptions.create.return_value = cast(
                "TranscriptionVerbose",
                "new_transcript",
            )

            with tempfile.TemporaryDirectory() as tmpdir:
                video_path = Path(tmpdir) / "video.mp4"
                video_path.touch()
                audio_path = Path(tmpdir) / "audio.mp3"
                audio_path.write_text("old audio")
                old_chunk0 = Path(tmpdir) / "audio_chunk0.mp3"
                old_chunk1 = Path(tmpdir) / "audio_chunk1.mp3"
                old_chunk0.write_text("old_chunk0")
                old_chunk1.write_text("old_chunk1")

                with (
                    patch.object(VideoTranscriber, "validate_input_file", return_value=video_path),
                    patch.object(VideoTranscriber, "extract_audio") as mock_extract,
                    patch("builtins.print"),
                ):
                    transcriber = VideoTranscriber("key")
                    # When transcribe is called with force=True
                    transcriber.transcribe(video_path, audio_path, force=True, keep_audio=True)

                    # Then force flag is properly passed to extract_audio
                    mock_extract.assert_called_once()
                    # `force` is a keyword-only argument in implementation; check kwargs
                    assert mock_extract.call_args.kwargs.get("force") is True


class TestExtractAudioChunkWithCustomPath:
    """Test extract_audio_chunk with custom audio output paths."""

    def test_extract_chunk_with_custom_audio_path(self) -> None:
        """Should create chunks with custom audio filename in custom directory."""
        # Given custom audio path in subdirectory and mocked AudioFileClip
        with patch("vtt.main.OpenAI"), patch("vtt.main.AudioFileClip") as mock_audio_class:
            mock_audio_instance = MagicMock()
            mock_chunk = MagicMock()
            mock_audio_instance.subclipped.return_value = mock_chunk
            mock_audio_instance.__enter__.return_value = mock_audio_instance
            mock_audio_instance.__exit__.return_value = None
            mock_audio_class.return_value = mock_audio_instance

            with tempfile.TemporaryDirectory() as tmpdir:
                # Create custom subdirectory
                custom_dir = Path(tmpdir) / "audio_files" / "custom_location"
                custom_dir.mkdir(parents=True, exist_ok=True)

                # Use custom audio filename
                audio_path = custom_dir / "my_custom_audio.mp3"
                audio_path.touch()

                transcriber = VideoTranscriber("key")
                # When extract_audio_chunk is called with custom audio path
                chunk_path = transcriber.extract_audio_chunk(audio_path, 0.0, 60.0, 0)

                # Then chunk is created with custom filename in same directory
                assert chunk_path.parent == custom_dir
                assert chunk_path.name == "my_custom_audio_chunk0.mp3"
                mock_audio_instance.subclipped.assert_called_once_with(0.0, 60.0)
                mock_chunk.write_audiofile.assert_called_once()

    def test_extract_multiple_chunks_with_custom_path(self) -> None:
        """Should create sequentially numbered chunks with custom audio path."""
        # Given custom audio path and multiple chunk extractions
        with patch("vtt.main.OpenAI"), patch("vtt.main.AudioFileClip") as mock_audio:
            mock_audio_instance = MagicMock()
            mock_chunk = MagicMock()
            mock_audio_instance.subclipped.return_value = mock_chunk
            mock_audio.return_value = mock_audio_instance

            with tempfile.TemporaryDirectory() as tmpdir:
                custom_dir = Path(tmpdir) / "my_audio_output"
                custom_dir.mkdir(parents=True, exist_ok=True)

                audio_path = custom_dir / "transcript_audio.mp3"
                audio_path.touch()

                transcriber = VideoTranscriber("key")

                # When multiple chunks are extracted
                chunk0_path = transcriber.extract_audio_chunk(audio_path, 0.0, 60.0, 0)
                chunk1_path = transcriber.extract_audio_chunk(audio_path, 60.0, 120.0, 1)
                chunk2_path = transcriber.extract_audio_chunk(audio_path, 120.0, 180.0, 2)

                # Then all chunks have correct names and are in same directory
                assert chunk0_path.name == "transcript_audio_chunk0.mp3"
                assert chunk1_path.name == "transcript_audio_chunk1.mp3"
                assert chunk2_path.name == "transcript_audio_chunk2.mp3"
                assert chunk0_path.parent == custom_dir
                assert chunk1_path.parent == custom_dir
                assert chunk2_path.parent == custom_dir

    def test_find_chunks_with_custom_path(self) -> None:
        """Should find chunks when using custom audio path."""
        # Given custom audio path with chunk files
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_dir = Path(tmpdir) / "custom_audio_dir"
            custom_dir.mkdir(parents=True)

            audio_path = custom_dir / "my_output.mp3"
            audio_path.write_text("audio")

            # Create chunks with custom filename
            chunk0 = custom_dir / "my_output_chunk0.mp3"
            chunk1 = custom_dir / "my_output_chunk1.mp3"
            chunk2 = custom_dir / "my_output_chunk2.mp3"
            chunk0.write_text("chunk0")
            chunk1.write_text("chunk1")
            chunk2.write_text("chunk2")

            with patch("vtt.main.OpenAI"):
                transcriber = VideoTranscriber("key")
                # When find_existing_chunks is called with custom path
                chunks = transcriber.find_existing_chunks(audio_path)

                # Then all custom-named chunks are found
                assert len(chunks) == 3
                assert chunks[0].name == "my_output_chunk0.mp3"
                assert chunks[1].name == "my_output_chunk1.mp3"
                assert chunks[2].name == "my_output_chunk2.mp3"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=main", "--cov-report=term-missing"])
