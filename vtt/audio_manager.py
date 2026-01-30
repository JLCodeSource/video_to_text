"""Audio file management utilities for video transcription."""

from pathlib import Path

from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.io.VideoFileClip import VideoFileClip

# Constants
AUDIO_EXTENSION = ".mp3"


class AudioFileManager:
    """Manage audio file operations including extraction and cleanup."""

    @staticmethod
    def extract_from_video(video_path: Path, audio_path: Path, *, force: bool = False) -> None:
        """Extract audio from video file.

        Args:
            video_path: Path to input video file.
            audio_path: Path where audio file will be saved.
            force: If True, overwrite existing audio file.
        """
        if audio_path.exists() and not force:
            print(f"Audio file already exists: {audio_path}")
            return

        with VideoFileClip(str(video_path)) as video_clip:
            if video_clip.audio is None:
                print(f"Warning: No audio track found in {video_path}")
                return

            print(f"Extracting audio from {video_path} to {audio_path}...")
            video_clip.audio.write_audiofile(str(audio_path), codec="libmp3lame", logger=None)

    @staticmethod
    def get_duration(audio_path: Path) -> float:
        """Get duration of audio file in seconds.

        Args:
            audio_path: Path to audio file.

        Returns:
            Duration in seconds.
        """
        with AudioFileClip(str(audio_path)) as audio_clip:
            return float(audio_clip.duration)

    @staticmethod
    def extract_chunk(audio_path: Path, start_time: float, end_time: float, chunk_index: int) -> Path:
        """Extract a chunk from audio file.

        Args:
            audio_path: Path to source audio file.
            start_time: Start time in seconds.
            end_time: End time in seconds.
            chunk_index: Index number for the chunk.

        Returns:
            Path to the extracted chunk file.
        """
        chunk_path = audio_path.parent / f"{audio_path.stem}_chunk{chunk_index}{AUDIO_EXTENSION}"

        with AudioFileClip(str(audio_path)) as audio_clip:
            chunk = audio_clip.subclipped(start_time, end_time)
            chunk.write_audiofile(str(chunk_path), codec="libmp3lame", logger=None)

        return chunk_path

    @staticmethod
    def find_chunks(audio_path: Path) -> list[Path]:
        """Find all chunk files for given audio file.

        Args:
            audio_path: Path to main audio file.

        Returns:
            List of chunk file paths, sorted by chunk index.
        """
        if not audio_path.parent.exists():
            return []

        pattern = f"{audio_path.stem}_chunk*{AUDIO_EXTENSION}"
        return sorted(audio_path.parent.glob(pattern))

    @staticmethod
    def cleanup_files(audio_path: Path) -> None:
        """Delete audio file and all its chunks.

        Args:
            audio_path: Path to main audio file.
        """
        # Delete main audio file
        if audio_path.exists():
            audio_path.unlink()

        # Delete all chunks
        for chunk in AudioFileManager.find_chunks(audio_path):
            if chunk.exists():
                chunk.unlink()

    @staticmethod
    def cleanup_chunks_only(audio_path: Path) -> None:
        """Delete only chunk files, keeping main audio file.

        Args:
            audio_path: Path to main audio file.
        """
        for chunk in AudioFileManager.find_chunks(audio_path):
            if chunk.exists():
                chunk.unlink()
