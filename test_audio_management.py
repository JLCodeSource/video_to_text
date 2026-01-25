"""Tests for audio file management: force overwrite, keep/delete functionality."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from main import VideoTranscriber


class TestFindExistingChunks:
    """Test finding existing chunk files."""
    
    def test_find_no_chunks_when_none_exist(self) -> None:
        """Given: audio path with no chunks, When: find_existing_chunks called, Then: empty list returned."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audio_path = Path(tmpdir) / "audio.mp3"
            audio_path.write_text("dummy")
            
            with patch('main.OpenAI'):
                transcriber = VideoTranscriber("key")
                chunks = transcriber.find_existing_chunks(audio_path)
                
                assert chunks == []
    
    def test_find_existing_chunks(self) -> None:
        """Given: audio path with multiple chunk files, When: find_existing_chunks called, Then: all chunks returned in order."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audio_path = Path(tmpdir) / "audio.mp3"
            audio_path.write_text("dummy")
            
            # Create chunk files
            chunk0 = Path(tmpdir) / "audio_chunk0.mp3"
            chunk1 = Path(tmpdir) / "audio_chunk1.mp3"
            chunk2 = Path(tmpdir) / "audio_chunk2.mp3"
            chunk0.write_text("chunk0")
            chunk1.write_text("chunk1")
            chunk2.write_text("chunk2")
            
            with patch('main.OpenAI'):
                transcriber = VideoTranscriber("key")
                chunks = transcriber.find_existing_chunks(audio_path)
                
                assert len(chunks) == 3
                assert chunks[0] == chunk0
                assert chunks[1] == chunk1
                assert chunks[2] == chunk2
    
    def test_find_chunks_sorted_correctly(self) -> None:
        """Given: audio chunks created out of order, When: find_existing_chunks called, Then: chunks returned in numeric order."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audio_path = Path(tmpdir) / "audio.mp3"
            audio_path.write_text("dummy")
            
            # Create chunks in reverse order
            chunk2 = Path(tmpdir) / "audio_chunk2.mp3"
            chunk0 = Path(tmpdir) / "audio_chunk0.mp3"
            chunk1 = Path(tmpdir) / "audio_chunk1.mp3"
            chunk2.write_text("chunk2")
            chunk0.write_text("chunk0")
            chunk1.write_text("chunk1")
            
            with patch('main.OpenAI'):
                transcriber = VideoTranscriber("key")
                chunks = transcriber.find_existing_chunks(audio_path)
                
                assert chunks[0].name == "audio_chunk0.mp3"
                assert chunks[1].name == "audio_chunk1.mp3"
                assert chunks[2].name == "audio_chunk2.mp3"


class TestCleanupAudioFiles:
    """Test cleanup of audio and chunk files."""
    
    def test_cleanup_removes_main_audio_file(self) -> None:
        """Given: main audio file exists, When: cleanup_audio_files called, Then: main file deleted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audio_path = Path(tmpdir) / "audio.mp3"
            audio_path.write_text("audio data")
            
            assert audio_path.exists()
            
            with patch('main.OpenAI'), patch('builtins.print'):
                transcriber = VideoTranscriber("key")
                transcriber.cleanup_audio_files(audio_path)
                
                assert not audio_path.exists()
    
    def test_cleanup_removes_chunk_files(self) -> None:
        """Given: main audio and chunk files exist, When: cleanup_audio_files called, Then: all files deleted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audio_path = Path(tmpdir) / "audio.mp3"
            audio_path.write_text("audio")
            chunk0 = Path(tmpdir) / "audio_chunk0.mp3"
            chunk1 = Path(tmpdir) / "audio_chunk1.mp3"
            chunk0.write_text("chunk0")
            chunk1.write_text("chunk1")
            
            with patch('main.OpenAI'), patch('builtins.print'):
                transcriber = VideoTranscriber("key")
                transcriber.cleanup_audio_files(audio_path)
                
                assert not audio_path.exists()
                assert not chunk0.exists()
                assert not chunk1.exists()
    
    def test_cleanup_handles_missing_files(self) -> None:
        """Given: audio file doesn't exist, When: cleanup_audio_files called, Then: no error raised."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audio_path = Path(tmpdir) / "audio.mp3"
            
            with patch('main.OpenAI'), patch('builtins.print'):
                transcriber = VideoTranscriber("key")
                # Should not raise an exception
                transcriber.cleanup_audio_files(audio_path)


class TestCleanupAudioChunks:
    """Test cleanup of chunk files only."""
    
    def test_cleanup_removes_only_chunks(self) -> None:
        """Given: main audio and chunk files exist, When: cleanup_audio_chunks called, Then: only chunks deleted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audio_path = Path(tmpdir) / "audio.mp3"
            audio_path.write_text("audio")
            chunk0 = Path(tmpdir) / "audio_chunk0.mp3"
            chunk1 = Path(tmpdir) / "audio_chunk1.mp3"
            chunk0.write_text("chunk0")
            chunk1.write_text("chunk1")
            
            with patch('main.OpenAI'), patch('builtins.print'):
                transcriber = VideoTranscriber("key")
                transcriber.cleanup_audio_chunks(audio_path)
                
                assert audio_path.exists()  # Main file still exists
                assert not chunk0.exists()   # Chunks deleted
                assert not chunk1.exists()


class TestTranscribeChunkedAudioKeepChunks:
    """Test keeping chunk files during transcription."""
    
    def test_keep_chunks_false_deletes_chunks(self) -> None:
        """Given: large audio file, When: transcribe_chunked_audio with keep_chunks=False, Then: chunks deleted after transcription."""
        with patch('main.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.audio.transcriptions.create.side_effect = ["chunk1", "chunk2"]
            
            with tempfile.TemporaryDirectory() as tmpdir:
                audio_path = Path(tmpdir) / "audio.mp3"
                audio_path.write_text("dummy")
                
                # Create temporary chunk files
                chunk0 = Path(tmpdir) / "audio_chunk0.mp3"
                chunk1 = Path(tmpdir) / "audio_chunk1.mp3"
                chunk0.write_text("c0")
                chunk1.write_text("c1")
                
                with patch.object(VideoTranscriber, 'extract_audio_chunk') as mock_extract:
                    mock_extract.side_effect = [chunk0, chunk1]
                    
                    with patch('builtins.print'):
                        transcriber = VideoTranscriber("key")
                        result = transcriber.transcribe_chunked_audio(
                            audio_path, 
                            duration=600.0,
                            num_chunks=2,
                            chunk_duration=300.0,
                            keep_chunks=False
                        )
                        
                        assert result == "chunk1 chunk2"
                        # Verify chunks were deleted
                        assert not chunk0.exists()
                        assert not chunk1.exists()
    
    def test_keep_chunks_true_keeps_chunks(self) -> None:
        """Given: large audio file, When: transcribe_chunked_audio with keep_chunks=True, Then: chunks kept after transcription."""
        with patch('main.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.audio.transcriptions.create.side_effect = ["chunk1", "chunk2"]
            
            with tempfile.TemporaryDirectory() as tmpdir:
                audio_path = Path(tmpdir) / "audio.mp3"
                audio_path.write_text("dummy")
                
                # Create temporary chunk files
                chunk0 = Path(tmpdir) / "audio_chunk0.mp3"
                chunk1 = Path(tmpdir) / "audio_chunk1.mp3"
                chunk0.write_text("c0")
                chunk1.write_text("c1")
                
                with patch.object(VideoTranscriber, 'extract_audio_chunk') as mock_extract:
                    mock_extract.side_effect = [chunk0, chunk1]
                    
                    with patch('builtins.print'):
                        transcriber = VideoTranscriber("key")
                        result = transcriber.transcribe_chunked_audio(
                            audio_path,
                            duration=600.0,
                            num_chunks=2,
                            chunk_duration=300.0,
                            keep_chunks=True
                        )
                        
                        assert result == "chunk1 chunk2"
                        # Verify chunks were NOT deleted
                        assert chunk0.exists()
                        assert chunk1.exists()


class TestTranscribeWithKeepAudio:
    """Test transcribe method with keep_audio parameter."""
    
    def test_transcribe_keep_audio_true_keeps_files(self) -> None:
        """Given: small video file, When: transcribe with keep_audio=True, Then: audio file kept."""
        with patch('main.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.audio.transcriptions.create.return_value = "transcript"
            
            with tempfile.TemporaryDirectory() as tmpdir:
                video_path = Path(tmpdir) / "video.mp4"
                video_path.touch()
                audio_path = Path(tmpdir) / "audio.mp3"
                audio_path.write_text("x" * 1024)
                
                with patch.object(VideoTranscriber, 'validate_video_file', return_value=video_path), \
                     patch.object(VideoTranscriber, 'extract_audio'), \
                     patch('builtins.print'):
                    transcriber = VideoTranscriber("key")
                    result = transcriber.transcribe(video_path, audio_path, keep_audio=True)
                    
                    assert result == "transcript"
                    assert audio_path.exists()  # File kept
    
    def test_transcribe_keep_audio_false_deletes_files(self) -> None:
        """Given: small video file, When: transcribe with keep_audio=False, Then: audio file deleted."""
        with patch('main.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.audio.transcriptions.create.return_value = "transcript"
            
            with tempfile.TemporaryDirectory() as tmpdir:
                video_path = Path(tmpdir) / "video.mp4"
                video_path.touch()
                audio_path = Path(tmpdir) / "audio.mp3"
                audio_path.write_text("x" * 1024)
                
                with patch.object(VideoTranscriber, 'validate_video_file', return_value=video_path), \
                     patch.object(VideoTranscriber, 'extract_audio'), \
                     patch('builtins.print'):
                    transcriber = VideoTranscriber("key")
                    result = transcriber.transcribe(video_path, audio_path, keep_audio=False)
                    
                    assert result == "transcript"
                    assert not audio_path.exists()  # File deleted


class TestTranscribeLargeWithKeepAudio:
    """Test transcribe with large files and keep_audio parameter."""
    
    def test_large_file_keep_audio_true_keeps_chunks(self) -> None:
        """Given: large video file, When: transcribe with keep_audio=True, When: chunks kept after transcription."""
        with patch('main.OpenAI') as mock_openai:
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
                
                with patch.object(VideoTranscriber, 'validate_video_file', return_value=video_path), \
                     patch.object(VideoTranscriber, 'extract_audio'), \
                     patch.object(VideoTranscriber, 'get_audio_duration', return_value=600.0), \
                     patch.object(VideoTranscriber, 'extract_audio_chunk') as mock_extract, \
                     patch('builtins.print'):
                    mock_extract.side_effect = [chunk0, chunk1]
                    
                    transcriber = VideoTranscriber("key")
                    _ = transcriber.transcribe(video_path, audio_path, keep_audio=True)
                    
                    # Verify chunks are kept
                    assert chunk0.exists()
                    assert chunk1.exists()
    
    def test_large_file_keep_audio_false_deletes_chunks(self) -> None:
        """Given: large video file, When: transcribe with keep_audio=False, Then: chunks deleted after transcription."""
        with patch('main.OpenAI') as mock_openai:
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
                
                with patch.object(VideoTranscriber, 'validate_video_file', return_value=video_path), \
                     patch.object(VideoTranscriber, 'extract_audio'), \
                     patch.object(VideoTranscriber, 'get_audio_duration', return_value=600.0), \
                     patch.object(VideoTranscriber, 'extract_audio_chunk') as mock_extract, \
                     patch('builtins.print'):
                    mock_extract.side_effect = [chunk0, chunk1]
                    
                    transcriber = VideoTranscriber("key")
                    _ = transcriber.transcribe(video_path, audio_path, keep_audio=False)
                    
                    # Verify chunks are deleted
                    assert not chunk0.exists()
                    assert not chunk1.exists()
                    # Main audio file also deleted when keep_audio=False
                    assert not audio_path.exists()


class TestForceOverwriteWithExistingChunks:
    """Test force overwrite with existing chunk files."""
    
    def test_force_overwrite_with_existing_chunks(self) -> None:
        """Given: existing audio and chunk files, When: transcribe with force=True, Then: all files recreated."""
        with patch('main.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.audio.transcriptions.create.return_value = "new_transcript"
            
            with tempfile.TemporaryDirectory() as tmpdir:
                video_path = Path(tmpdir) / "video.mp4"
                video_path.touch()
                audio_path = Path(tmpdir) / "audio.mp3"
                audio_path.write_text("old audio")
                
                # Create old chunk files
                old_chunk0 = Path(tmpdir) / "audio_chunk0.mp3"
                old_chunk1 = Path(tmpdir) / "audio_chunk1.mp3"
                old_chunk0.write_text("old_chunk0")
                old_chunk1.write_text("old_chunk1")
                
                with patch.object(VideoTranscriber, 'validate_video_file', return_value=video_path), \
                     patch.object(VideoTranscriber, 'extract_audio') as mock_extract, \
                     patch('builtins.print'):
                    transcriber = VideoTranscriber("key")
                    transcriber.transcribe(video_path, audio_path, force=True, keep_audio=True)
                    
                    # Verify force=True was passed to extract_audio
                    mock_extract.assert_called_once()
                    # extract_audio is called with (video_path, audio_path, force)
                    assert mock_extract.call_args[0][2] is True  # Third positional argument


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=main", "--cov-report=term-missing"])
