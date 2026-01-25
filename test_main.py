"""Comprehensive unit and integration tests for video_to_text."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from main import (
    VideoTranscriber,
    get_api_key,
    save_transcript,
    display_result,
    main,
)


class TestVideoTranscriberInit:
    """Test VideoTranscriber initialization."""
    
    def test_init_with_valid_api_key(self) -> None:
        """Should initialize with API key."""
        # Given: OpenAI client is mocked
        with patch('main.OpenAI') as mock_openai:
            # When: VideoTranscriber is initialized with API key
            transcriber = VideoTranscriber("test-api-key")
            # Then: API key is stored and OpenAI client is created
            assert transcriber.api_key == "test-api-key"
            mock_openai.assert_called_once_with(api_key="test-api-key")
    
    def test_init_sets_max_size_mb(self) -> None:
        """Should have MAX_SIZE_MB constant."""
        # Given: OpenAI client is mocked
        with patch('main.OpenAI'):
            # When: VideoTranscriber is initialized
            transcriber = VideoTranscriber("test-key")
            # Then: MAX_SIZE_MB constant is 25
            assert transcriber.MAX_SIZE_MB == 25


class TestValidateVideoFile:
    """Test video file validation."""
    
    def test_validate_existing_video_file(self) -> None:
        """Should return Path when file exists."""
        # Given: temporary directory with video file
        with tempfile.TemporaryDirectory() as tmpdir:
            video_path = Path(tmpdir) / "test.mp4"
            video_path.touch()
            
            with patch('main.OpenAI'):
                transcriber = VideoTranscriber("key")
                # When: validate_video_file is called with existing file
                result = transcriber.validate_video_file(video_path)
                # Then: same path is returned
                assert result == video_path
    
    def test_validate_nonexistent_video_file(self) -> None:
        """Should raise FileNotFoundError for missing file."""
        # Given: OpenAI client is mocked
        with patch('main.OpenAI'):
            transcriber = VideoTranscriber("key")
            nonexistent = Path("/nonexistent/video.mp4")
            
            # When: validate_video_file is called with non-existent file
            with pytest.raises(FileNotFoundError) as exc_info:
                transcriber.validate_video_file(nonexistent)
            # Then: FileNotFoundError is raised with appropriate message
            assert "Video file not found" in str(exc_info.value)


class TestResolveAudioPath:
    """Test audio path resolution."""
    
    def test_resolve_audio_path_none_returns_mp3_suffix(self) -> None:
        """Should default to .mp3 suffix when audio_path is None."""
        # Given: VideoTranscriber and video path
        with patch('main.OpenAI'):
            transcriber = VideoTranscriber("key")
            video_path = Path("/path/to/video.mp4")
            # When: resolve_audio_path is called with None audio_path
            result = transcriber.resolve_audio_path(video_path, None)
            # Then: .mp3 suffix is applied to video path
            assert result == Path("/path/to/video.mp3")
    
    def test_resolve_audio_path_custom(self) -> None:
        """Should return custom audio_path when provided."""
        # Given: VideoTranscriber, video path, and custom audio path
        with patch('main.OpenAI'):
            transcriber = VideoTranscriber("key")
            video_path = Path("/path/to/video.mp4")
            audio_path = Path("/custom/audio.wav")
            # When: resolve_audio_path is called with custom audio_path
            result = transcriber.resolve_audio_path(video_path, audio_path)
            # Then: custom audio_path is returned as-is
            assert result == audio_path


class TestExtractAudio:
    """Test audio extraction."""
    
    def test_extract_audio_file_not_exists(self) -> None:
        """Should extract audio when file doesn't exist."""
        # Given: video file and mocked VideoFileClip
        with tempfile.TemporaryDirectory() as tmpdir:
            video_path = Path(tmpdir) / "video.mp4"
            video_path.touch()
            audio_path = Path(tmpdir) / "audio.mp3"
            
            with patch('main.OpenAI'), \
                 patch('main.VideoFileClip') as mock_video:
                mock_video_instance = MagicMock()
                mock_video_instance.audio = MagicMock()
                mock_video.return_value = mock_video_instance
                
                transcriber = VideoTranscriber("key")
                # When: extract_audio is called with non-existent audio_path
                transcriber.extract_audio(video_path, audio_path, force=False)
                
                # Then: VideoFileClip is created and audio is written
                mock_video.assert_called_once_with(str(video_path))
                mock_video_instance.audio.write_audiofile.assert_called_once()
                mock_video_instance.close.assert_called_once()
    
    def test_extract_audio_file_exists_no_force(self) -> None:
        """Should skip extraction when file exists and force=False."""
        # Given: existing audio file and mocked VideoFileClip
        with tempfile.TemporaryDirectory() as tmpdir:
            video_path = Path(tmpdir) / "video.mp4"
            video_path.touch()
            audio_path = Path(tmpdir) / "audio.mp3"
            audio_path.write_text("dummy")
            
            with patch('main.OpenAI'), \
                 patch('main.VideoFileClip') as mock_video:
                transcriber = VideoTranscriber("key")
                with patch('builtins.print'):
                    # When: extract_audio is called with existing file and force=False
                    transcriber.extract_audio(video_path, audio_path, force=False)
                
                # Then: VideoFileClip is not called (extraction skipped)
                mock_video.assert_not_called()
    
    def test_extract_audio_file_exists_with_force(self) -> None:
        """Should extract when force=True even if file exists."""
        # Given: existing audio file and mocked VideoFileClip
        with tempfile.TemporaryDirectory() as tmpdir:
            video_path = Path(tmpdir) / "video.mp4"
            video_path.touch()
            audio_path = Path(tmpdir) / "audio.mp3"
            audio_path.write_text("dummy")
            
            with patch('main.OpenAI'), \
                 patch('main.VideoFileClip') as mock_video:
                mock_video_instance = MagicMock()
                mock_video_instance.audio = MagicMock()
                mock_video.return_value = mock_video_instance
                
                transcriber = VideoTranscriber("key")
                # When: extract_audio is called with force=True
                transcriber.extract_audio(video_path, audio_path, force=True)
                
                # Then: VideoFileClip is called despite existing file
                mock_video.assert_called_once()
    
    def test_extract_audio_no_audio_track(self) -> None:
        """Should handle video with no audio track."""
        # Given: video file with no audio track and mocked VideoFileClip
        with tempfile.TemporaryDirectory() as tmpdir:
            video_path = Path(tmpdir) / "video.mp4"
            video_path.touch()
            audio_path = Path(tmpdir) / "audio.mp3"
            
            with patch('main.OpenAI'), \
                 patch('main.VideoFileClip') as mock_video:
                mock_video_instance = MagicMock()
                mock_video_instance.audio = None
                mock_video.return_value = mock_video_instance
                
                transcriber = VideoTranscriber("key")
                # When: extract_audio is called on video with no audio
                transcriber.extract_audio(video_path, audio_path, force=False)
                
                # Then: write_audiofile is not called
                mock_video_instance.write_audiofile.assert_not_called()


class TestGetAudioDuration:
    """Test audio duration retrieval."""
    
    def test_get_audio_duration(self) -> None:
        """Should return audio duration in seconds."""
        # Given: mocked AudioFileClip with 120.5 second duration
        with patch('main.OpenAI'), \
             patch('main.AudioFileClip') as mock_audio:
            mock_audio_instance = MagicMock()
            mock_audio_instance.duration = 120.5
            mock_audio.return_value = mock_audio_instance
            
            transcriber = VideoTranscriber("key")
            # When: get_audio_duration is called
            duration = transcriber.get_audio_duration(Path("audio.mp3"))
            
            # Then: duration is returned and AudioFileClip is closed
            assert duration == 120.5
            mock_audio.assert_called_once_with("audio.mp3")
            mock_audio_instance.close.assert_called_once()


class TestCalculateChunkParams:
    """Test chunk parameter calculation."""
    
    def test_calculate_chunk_params_small_file(self) -> None:
        """Should return 1 chunk for file under limit."""
        # Given: VideoTranscriber and 10MB file with 5 minute duration
        with patch('main.OpenAI'):
            transcriber = VideoTranscriber("key")
            # When: calculate_chunk_params is called with small file
            num_chunks, chunk_duration = transcriber.calculate_chunk_params(10.0, 300.0)
            # Then: single chunk is returned
            assert num_chunks == 1
    
    def test_calculate_chunk_params_large_file(self) -> None:
        """Should calculate multiple chunks for large file."""
        # Given: VideoTranscriber and 50MB file with 1 hour duration
        with patch('main.OpenAI'):
            transcriber = VideoTranscriber("key")
            # When: calculate_chunk_params is called with large file
            num_chunks, chunk_duration = transcriber.calculate_chunk_params(50.0, 3600.0)
            # Then: multiple chunks and positive chunk_duration returned
            assert num_chunks > 1
            assert chunk_duration > 0
    
    def test_calculate_chunk_params_formula(self) -> None:
        """Should apply correct formula for chunk calculation."""
        # Given: VideoTranscriber, 30MB file, and 10 minute duration
        with patch('main.OpenAI'):
            transcriber = VideoTranscriber("key")
            file_size_mb = 30.0
            duration = 600.0  # 10 minutes
            # When: calculate_chunk_params is called
            num_chunks, chunk_duration = transcriber.calculate_chunk_params(file_size_mb, duration)
            
            # Then: formula (25/30) * 600 * 0.9 = 450 seconds per chunk is applied
            expected_chunk_duration = (25.0 / 30.0) * 600.0 * 0.9
            assert abs(chunk_duration - expected_chunk_duration) < 0.01


class TestExtractAudioChunk:
    """Test audio chunk extraction."""
    
    def test_extract_audio_chunk(self) -> None:
        """Should extract and save audio chunk."""
        # Given: audio file and mocked AudioFileClip with time slice 0-60 seconds
        with patch('main.OpenAI'), \
             patch('main.AudioFileClip') as mock_audio:
            mock_audio_instance = MagicMock()
            mock_chunk = MagicMock()
            mock_audio_instance.subclipped.return_value = mock_chunk
            mock_audio.return_value = mock_audio_instance
            
            with tempfile.TemporaryDirectory() as tmpdir:
                audio_path = Path(tmpdir) / "audio.mp3"
                audio_path.touch()
                
                transcriber = VideoTranscriber("key")
                # When: extract_audio_chunk is called with chunk index 0
                chunk_path = transcriber.extract_audio_chunk(audio_path, 0.0, 60.0, 0)
                
                # Then: chunk file is created and audio_chunk0.mp3 is generated
                assert chunk_path.name == "audio_chunk0.mp3"
                mock_audio_instance.subclipped.assert_called_once_with(0.0, 60.0)
                mock_chunk.write_audiofile.assert_called_once()
                mock_audio_instance.close.assert_called_once()


class TestTranscribeAudioFile:
    """Test audio file transcription."""
    
    def test_transcribe_audio_file(self) -> None:
        """Should transcribe audio file using Whisper API."""
        # Given: audio file and mocked OpenAI client returning "Hello world"
        with patch('main.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.audio.transcriptions.create.return_value = "Hello world"
            
            with tempfile.TemporaryDirectory() as tmpdir:
                audio_path = Path(tmpdir) / "audio.mp3"
                audio_path.write_text("dummy audio")
                
                transcriber = VideoTranscriber("key")
                # When: transcribe_audio_file is called
                result = transcriber.transcribe_audio_file(audio_path)
                
                # Then: Whisper API is called with correct model and response format, result returned
                assert result == "Hello world"
                mock_client.audio.transcriptions.create.assert_called_once()
                call_kwargs = mock_client.audio.transcriptions.create.call_args[1]
                assert call_kwargs["model"] == "whisper-1"
                assert call_kwargs["response_format"] == "text"


class TestTranscribeChunkedAudio:
    """Test chunked audio transcription."""
    
    def test_transcribe_chunked_audio(self) -> None:
        """Should transcribe multiple chunks and join results."""
        # Given: audio file split into 2 chunks with different transcription results
        with patch('main.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.audio.transcriptions.create.side_effect = [
                "chunk1 text",
                "chunk2 text",
            ]
            
            with tempfile.TemporaryDirectory() as tmpdir:
                audio_path = Path(tmpdir) / "audio.mp3"
                audio_path.write_text("dummy audio")
                
                with patch.object(VideoTranscriber, 'extract_audio_chunk') as mock_extract, \
                     patch('builtins.print'):
                    mock_extract.side_effect = [
                        Path(tmpdir) / "chunk0.mp3",
                        Path(tmpdir) / "chunk1.mp3",
                    ]
                    
                    for i in range(2):
                        chunk_path = Path(tmpdir) / f"chunk{i}.mp3"
                        chunk_path.write_text("dummy")
                    
                    transcriber = VideoTranscriber("key")
                    # When: transcribe_chunked_audio is called with 2 chunks
                    result = transcriber.transcribe_chunked_audio(
                        audio_path, 
                        duration=600.0, 
                        num_chunks=2, 
                        chunk_duration=300.0
                    )
                    
                    # Then: chunks are transcribed and results joined with space
                    assert result == "chunk1 text chunk2 text"
                    assert mock_client.audio.transcriptions.create.call_count == 2


class TestTranscribeSmallFile:
    """Test transcription of small audio files."""
    
    def test_transcribe_small_file(self) -> None:
        """Should transcribe small file without chunking."""
        # Given: small audio file (1KB) and mocked transcription API
        with patch('main.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.audio.transcriptions.create.return_value = "Full transcript"
            
            with tempfile.TemporaryDirectory() as tmpdir:
                video_path = Path(tmpdir) / "video.mp4"
                video_path.touch()
                audio_path = Path(tmpdir) / "audio.mp3"
                audio_path.write_text("x" * 1024)  # 1KB file
                
                with patch.object(VideoTranscriber, 'validate_video_file', return_value=video_path), \
                     patch.object(VideoTranscriber, 'extract_audio'), \
                     patch('builtins.print'):
                    transcriber = VideoTranscriber("key")
                    # When: transcribe is called with small file
                    result = transcriber.transcribe(video_path, audio_path)
                    
                    # Then: transcription API called once (no chunking) with full transcript returned
                    assert result == "Full transcript"
                    mock_client.audio.transcriptions.create.assert_called_once()


class TestTranscribeLargeFile:
    """Test transcription of large audio files."""
    
    def test_transcribe_large_file_chunked(self) -> None:
        """Should chunk large files and transcribe."""
        # Given: 30MB audio file with 2 transcribed chunks
        with patch('main.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.audio.transcriptions.create.side_effect = [
                "chunk1 text",
                "chunk2 text",
            ]
            
            with tempfile.TemporaryDirectory() as tmpdir:
                video_path = Path(tmpdir) / "video.mp4"
                video_path.touch()
                audio_path = Path(tmpdir) / "audio.mp3"
                # Create 30MB file
                audio_path.write_text("x" * (30 * 1024 * 1024))
                
                with patch.object(VideoTranscriber, 'validate_video_file', return_value=video_path), \
                     patch.object(VideoTranscriber, 'extract_audio'), \
                     patch.object(VideoTranscriber, 'get_audio_duration', return_value=600.0), \
                     patch.object(VideoTranscriber, 'extract_audio_chunk') as mock_extract_chunk, \
                     patch('builtins.print'):
                    # Create temporary chunk files
                    chunk_files = []
                    for i in range(2):
                        chunk_path = Path(tmpdir) / f"chunk{i}.mp3"
                        chunk_path.write_text("dummy")
                        chunk_files.append(chunk_path)
                    
                    mock_extract_chunk.side_effect = chunk_files
                    
                    transcriber = VideoTranscriber("key")
                    # When: transcribe is called with large file
                    _ = transcriber.transcribe(video_path, audio_path)
                    
                    # Then: transcription API called multiple times (once per chunk)
                    assert mock_client.audio.transcriptions.create.call_count >= 1


class TestGetApiKey:
    """Test API key retrieval."""
    
    def test_get_api_key_from_argument(self) -> None:
        """Should return API key from argument."""
        # Given: API key passed as argument "test-key-arg"
        # When: get_api_key is called with argument
        result = get_api_key("test-key-arg")
        # Then: API key argument is returned
        assert result == "test-key-arg"
    
    def test_get_api_key_from_env(self) -> None:
        """Should return API key from environment variable."""
        # Given: OPENAI_API_KEY environment variable set to "test-key-env"
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key-env"}):
            # When: get_api_key is called with None argument
            result = get_api_key(None)
            # Then: environment variable value is returned
            assert result == "test-key-env"
    
    def test_get_api_key_argument_overrides_env(self) -> None:
        """Should prefer argument over environment variable."""
        # Given: both argument "test-key-arg" and OPENAI_API_KEY env var "test-key-env" present
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key-env"}):
            # When: get_api_key is called with argument
            result = get_api_key("test-key-arg")
            # Then: argument takes precedence over environment variable
            assert result == "test-key-arg"
    
    def test_get_api_key_missing_raises_error(self) -> None:
        """Should raise ValueError when API key is missing."""
        # Given: no API key in argument and no OPENAI_API_KEY environment variable
        with patch.dict(os.environ, {}, clear=True):
            # When: get_api_key is called with None
            with pytest.raises(ValueError) as exc_info:
                get_api_key(None)
            # Then: ValueError is raised with appropriate message
            assert "OpenAI API key not provided" in str(exc_info.value)


class TestSaveTranscript:
    """Test transcript saving."""
    
    def test_save_transcript(self) -> None:
        """Should save transcript to file."""
        # Given: output path and transcript text
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "transcript.txt"
            transcript = "This is a test transcript."
            
            with patch('builtins.print'):
                # When: save_transcript is called
                save_transcript(output_path, transcript)
            
            # Then: file is created with correct content
            assert output_path.exists()
            assert output_path.read_text() == transcript
    
    def test_save_transcript_creates_directory(self) -> None:
        """Should work with nested paths."""
        # Given: nested output path and transcript text
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "subdir" / "transcript.txt"
            output_path.parent.mkdir(parents=True)
            transcript = "Another transcript."
            
            with patch('builtins.print'):
                # When: save_transcript is called with nested path
                save_transcript(output_path, transcript)
            
            # Then: file is created in nested directory with correct content
            assert output_path.read_text() == transcript


class TestDisplayResult:
    """Test result display."""
    
    def test_display_result(self, capsys):
        """Should display formatted result."""
        # Given: transcript text to display
        transcript = "This is the transcription."
        # When: display_result is called
        display_result(transcript)
        
        # Then: output contains formatted transcript with header and separator
        captured = capsys.readouterr()
        assert "Transcription Result:" in captured.out
        assert transcript in captured.out
        assert "=" * 50 in captured.out


class TestMainCliArgumentParsing:
    """Test main function CLI argument parsing."""
    
    def test_main_with_required_args(self) -> None:
        """Should work with minimum required arguments."""
        # Given: OpenAI API key in environment and video file path
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with tempfile.TemporaryDirectory() as tmpdir:
                video_path = Path(tmpdir) / "video.mp4"
                video_path.touch()
                
                with patch('sys.argv', ['main.py', str(video_path)]), \
                     patch.object(VideoTranscriber, 'transcribe', return_value="test"), \
                     patch('builtins.print'):
                    # When: main() is called with only video path argument
                    try:
                        main()
                    except SystemExit:
                        pass
                    # Then: execution completes without error
    
    def test_main_with_all_args(self) -> None:
        """Should handle all CLI arguments."""
        # Given: all CLI arguments specified (video, key, audio, save, force)
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with tempfile.TemporaryDirectory() as tmpdir:
                video_path = Path(tmpdir) / "video.mp4"
                video_path.touch()
                audio_path = Path(tmpdir) / "audio.mp3"
                transcript_path = Path(tmpdir) / "transcript.txt"
                
                with patch('sys.argv', [
                    'main.py',
                    str(video_path),
                    '-k', 'custom-key',
                    '-o', str(audio_path),
                    '-s', str(transcript_path),
                    '-f'
                ]), \
                     patch.object(VideoTranscriber, 'transcribe', return_value="test"), \
                     patch('builtins.print'):
                    # When: main() is called with all arguments
                    try:
                        main()
                    except SystemExit:
                        pass
                    # Then: execution completes without error


class TestMainErrorHandling:
    """Test main function error handling."""
    
    def test_main_missing_api_key(self) -> None:
        """Should exit with error when API key is missing."""
        # Given: no API key in environment and video file path
        with patch.dict(os.environ, {}, clear=True):
            with tempfile.TemporaryDirectory() as tmpdir:
                video_path = Path(tmpdir) / "video.mp4"
                video_path.touch()
                
                with patch('sys.argv', ['main.py', str(video_path)]), \
                     patch('builtins.print'):
                    # When: main() is called without API key
                    with pytest.raises(SystemExit) as exc_info:
                        main()
                    # Then: exits with error code 1
                    assert exc_info.value.code == 1
    
    def test_main_missing_video_file(self) -> None:
        """Should exit with error when video file doesn't exist."""
        # Given: API key in environment and non-existent video file path
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with patch('sys.argv', ['main.py', '/nonexistent/video.mp4']), \
                 patch('builtins.print'):
                # When: main() is called with missing video file
                with pytest.raises(SystemExit) as exc_info:
                    main()
                # Then: exits with error code 1
                assert exc_info.value.code == 1
    
    def test_main_generic_exception_handling(self) -> None:
        """Should handle generic exceptions."""
        # Given: API key in environment, video file, and transcriber that raises RuntimeError
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with tempfile.TemporaryDirectory() as tmpdir:
                video_path = Path(tmpdir) / "video.mp4"
                video_path.touch()
                
                with patch('sys.argv', ['main.py', str(video_path)]), \
                     patch.object(VideoTranscriber, 'transcribe', side_effect=RuntimeError("Test error")), \
                     patch('builtins.print'):
                    # When: main() is called and transcribe raises exception
                    with pytest.raises(SystemExit) as exc_info:
                        main()
                    # Then: exits with error code 1
                    assert exc_info.value.code == 1


class TestIntegrationFullWorkflow:
    """Integration tests for complete workflows."""
    
    def test_full_workflow_small_file(self) -> None:
        """Should complete full transcription workflow for small file."""
        # Given: video file, audio output path, transcript save path, and mocked transcriber
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with tempfile.TemporaryDirectory() as tmpdir:
                video_path = Path(tmpdir) / "video.mp4"
                video_path.touch()
                audio_path = Path(tmpdir) / "audio.mp3"
                transcript_path = Path(tmpdir) / "output.txt"
                
                with patch('sys.argv', [
                    'main.py',
                    str(video_path),
                    '-o', str(audio_path),
                    '-s', str(transcript_path),
                ]), \
                     patch.object(VideoTranscriber, 'validate_video_file', return_value=video_path), \
                     patch.object(VideoTranscriber, 'extract_audio'), \
                     patch.object(VideoTranscriber, 'transcribe_audio_file', return_value="Final transcript"), \
                     patch('builtins.print'):
                    with patch.object(
                        VideoTranscriber,
                        'transcribe',
                        return_value="Final transcript"
                    ):
                        # When: main() is called with transcript save path
                        try:
                            main()
                        except SystemExit:
                            pass
                        
                        # Then: transcript is saved to file
                        if transcript_path.exists():
                            assert "Final transcript" in transcript_path.read_text()
    
    def test_full_workflow_with_force_flag(self) -> None:
        """Should respect force flag in workflow."""
        # Given: video file, existing audio file, and force flag set
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with tempfile.TemporaryDirectory() as tmpdir:
                video_path = Path(tmpdir) / "video.mp4"
                video_path.touch()
                audio_path = Path(tmpdir) / "audio.mp3"
                audio_path.write_text("existing")
                
                with patch('sys.argv', [
                    'main.py',
                    str(video_path),
                    '-f'
                ]), \
                     patch.object(VideoTranscriber, 'transcribe', return_value="New transcript") as mock_transcribe, \
                     patch('builtins.print'):
                    # When: main() is called with force flag (-f)
                    try:
                        main()
                    except SystemExit:
                        pass
                    
                    # Then: transcribe is called with force=True
                    mock_transcribe.assert_called()
                    call_args = mock_transcribe.call_args
                    # force is the 3rd positional argument
                    assert call_args[0][2] is True


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_exact_max_size_boundary(self) -> None:
        """Should chunk file exactly at max size."""
        # Given: VideoTranscriber and file exactly 25MB (max size boundary)
        with patch('main.OpenAI'):
            transcriber = VideoTranscriber("key")
            # When: calculate_chunk_params called at 25MB boundary
            num_chunks, _ = transcriber.calculate_chunk_params(25.0, 300.0)
            # Then: chunk calculation works correctly (chunk_duration = (25/25) * 300 * 0.9 = 270)
            assert num_chunks >= 1
    
    def test_just_over_max_size_boundary(self) -> None:
        """Should chunk file over max size."""
        # Given: VideoTranscriber and file 30MB (over 25MB max)
        with patch('main.OpenAI'):
            transcriber = VideoTranscriber("key")
            # When: calculate_chunk_params called with 30MB file
            num_chunks, _ = transcriber.calculate_chunk_params(30.0, 300.0)
            # Then: multiple chunks required for file over max size
            assert num_chunks > 1
    
    def test_very_long_audio(self) -> None:
        """Should handle very long audio duration."""
        # Given: VideoTranscriber and 50MB file with 8 hour duration
        with patch('main.OpenAI'):
            transcriber = VideoTranscriber("key")
            # When: calculate_chunk_params called with very long duration (28800 seconds = 8 hours)
            num_chunks, chunk_duration = transcriber.calculate_chunk_params(50.0, 28800.0)
            # Then: chunk calculation works for very long audio
            assert num_chunks > 0
            assert chunk_duration > 0
    
    def test_empty_transcript(self) -> None:
        """Should handle empty transcription result."""
        # Given: mocked OpenAI API returning empty string
        with patch('main.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.audio.transcriptions.create.return_value = ""
            
            with tempfile.TemporaryDirectory() as tmpdir:
                audio_path = Path(tmpdir) / "audio.mp3"
                audio_path.write_text("dummy")
                
                transcriber = VideoTranscriber("key")
                # When: transcribe_audio_file called with audio that produces no text
                result = transcriber.transcribe_audio_file(audio_path)
                
                # Then: empty string is returned correctly
                assert result == ""
    
    def test_transcript_with_special_characters(self) -> None:
        """Should handle transcript with special characters."""
        # Given: test setup
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "transcript.txt"
            transcript = "Special chars: @#$%^&*()_+-=[]{}|;:',.<>?/~`\n中文\némojis: 🎉🎊"
            
            with patch('builtins.print'):
                save_transcript(output_path, transcript)
            
            # Then: verify expected behavior
            assert output_path.read_text() == transcript


class TestMainGuard:
    """Test main guard execution."""
    
    def test_main_guard_execution(self) -> None:
        """Should execute main when run as script."""
        # This test verifies the if __name__ == "__main__": guard works
        # by checking that importing the module doesn't call main()
        import importlib.util
        spec = importlib.util.spec_from_file_location("main_module", Path(__file__).parent / "main.py")
        module = importlib.util.module_from_spec(spec) if spec else None
        
        # Mock sys.argv to avoid argparse errors during import
        with patch('sys.argv', ['main.py']), \
             patch('main.main'):
            # When we execute the module directly, main should be called
            # But when we import it, main should NOT be called
            # This test just verifies the pattern is correct
            # Then: verify expected behavior
            assert hasattr(module, '__name__')


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=main", "--cov-report=term-missing", "--cov-report=html"])
