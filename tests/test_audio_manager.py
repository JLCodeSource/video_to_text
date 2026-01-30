"""Tests for audio_manager module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from vtt.audio_manager import AudioFileManager


class TestAudioFileManager:
    """Test AudioFileManager functionality."""

    def test_extract_from_video_new_file(self, tmp_path: Path) -> None:
        """Should extract audio when file doesn't exist."""
        video_path = tmp_path / "video.mp4"
        audio_path = tmp_path / "audio.mp3"
        video_path.touch()

        with patch("vtt.audio_manager.VideoFileClip") as mock_video:
            mock_instance = MagicMock()
            mock_instance.audio = MagicMock()
            mock_instance.__enter__.return_value = mock_instance
            mock_instance.__exit__.return_value = None
            mock_video.return_value = mock_instance

            AudioFileManager.extract_from_video(video_path, audio_path)

            mock_video.assert_called_once_with(str(video_path))
            mock_instance.audio.write_audiofile.assert_called_once()

    def test_get_duration(self, tmp_path: Path) -> None:
        """Should return audio duration."""
        audio_path = tmp_path / "audio.mp3"
        audio_path.touch()

        with patch("vtt.audio_manager.AudioFileClip") as mock_audio:
            mock_instance = MagicMock()
            mock_instance.duration = 120.5
            mock_instance.__enter__.return_value = mock_instance
            mock_instance.__exit__.return_value = None
            mock_audio.return_value = mock_instance

            duration = AudioFileManager.get_duration(audio_path)

            assert duration == 120.5

    def test_find_chunks(self, tmp_path: Path) -> None:
        """Should find all chunk files."""
        audio_path = tmp_path / "audio.mp3"
        (tmp_path / "audio_chunk0.mp3").touch()
        (tmp_path / "audio_chunk1.mp3").touch()
        (tmp_path / "audio_chunk2.mp3").touch()

        chunks = AudioFileManager.find_chunks(audio_path)

        assert len(chunks) == 3
        assert all(chunk.suffix == ".mp3" for chunk in chunks)

    def test_cleanup_files(self, tmp_path: Path) -> None:
        """Should delete audio and all chunks."""
        audio_path = tmp_path / "audio.mp3"
        audio_path.touch()
        chunk0 = tmp_path / "audio_chunk0.mp3"
        chunk1 = tmp_path / "audio_chunk1.mp3"
        chunk0.touch()
        chunk1.touch()

        AudioFileManager.cleanup_files(audio_path)

        assert not audio_path.exists()
        assert not chunk0.exists()
        assert not chunk1.exists()

    def test_cleanup_chunks_only(self, tmp_path: Path) -> None:
        """Should delete only chunks, keeping main file."""
        audio_path = tmp_path / "audio.mp3"
        audio_path.touch()
        chunk0 = tmp_path / "audio_chunk0.mp3"
        chunk1 = tmp_path / "audio_chunk1.mp3"
        chunk0.touch()
        chunk1.touch()

        AudioFileManager.cleanup_chunks_only(audio_path)

        assert audio_path.exists()
        assert not chunk0.exists()
        assert not chunk1.exists()
