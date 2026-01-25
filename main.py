import os
import argparse
import sys
from pathlib import Path
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
from openai import OpenAI


class VideoTranscriber:
    """Transcribe video audio using OpenAI's Whisper model."""
    
    MAX_SIZE_MB = 25
    
    def __init__(self, api_key: str) -> None:
        """Initialize transcriber with API key."""
        self.api_key: str = api_key
        self.client = OpenAI(api_key=api_key)
    
    def validate_video_file(self, video_path: Path) -> Path:
        """Validate and return video file path."""
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        return video_path
    
    def resolve_audio_path(self, video_path: Path, audio_path: Path | None) -> Path:
        """Resolve audio file path."""
        if audio_path is None:
            return video_path.with_suffix(".mp3")
        return audio_path
    
    def extract_audio(self, video_path: Path, audio_path: Path, force: bool = False) -> None:
        """Extract audio from video file if it doesn't exist or force is True."""
        if audio_path.exists() and not force:
            file_size_mb = audio_path.stat().st_size / (1024 * 1024)
            print(f"Using existing audio file: {audio_path} ({file_size_mb:.1f}MB)")
            return
        
        print("Extracting audio from video...")
        video: VideoFileClip = VideoFileClip(str(video_path))
        if video.audio is not None:
            video.audio.write_audiofile(str(audio_path), logger=None)
        video.close()
    
    def get_audio_duration(self, audio_path: Path) -> float:
        """Get duration of audio file in seconds."""
        audio_clip: AudioFileClip = AudioFileClip(str(audio_path))
        duration: float = audio_clip.duration  # type: ignore
        audio_clip.close()
        return duration
    
    def calculate_chunk_params(self, file_size_mb: float, duration: float) -> tuple[int, float]:
        """Calculate number of chunks and duration per chunk."""
        chunk_duration = (self.MAX_SIZE_MB / file_size_mb) * duration * 0.9  # 90% to be safe
        num_chunks = int(duration / chunk_duration) + 1
        return num_chunks, chunk_duration
    
    def extract_audio_chunk(self, audio_path: Path, start_time: float, end_time: float, chunk_index: int) -> Path:
        """Extract a single audio chunk and save to file."""
        audio_clip: AudioFileClip = AudioFileClip(str(audio_path))
        chunk: AudioFileClip = audio_clip.subclipped(start_time, end_time)
        chunk_path: Path = audio_path.with_stem(f"{audio_path.stem}_chunk{chunk_index}")
        chunk.write_audiofile(str(chunk_path), logger="bar")
        audio_clip.close()
        return chunk_path
    
    def transcribe_audio_file(self, audio_path: Path) -> str:
        """Transcribe a single audio file using Whisper API."""
        with open(audio_path, "rb") as audio_file:
            transcript = self.client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file,
                response_format="text"
            )
        return transcript
    
    def transcribe_chunked_audio(self, audio_path: Path, duration: float, num_chunks: int, chunk_duration: float) -> str:
        """Transcribe audio by splitting into chunks."""
        print(f"Splitting into {num_chunks} chunks ({chunk_duration:.1f}s each)...")
        
        transcripts: list[str] = []
        for i in range(num_chunks):
            start_time: float = i * chunk_duration
            end_time: float = min((i + 1) * chunk_duration, duration)
            
            # Extract and transcribe chunk
            chunk_path: Path = self.extract_audio_chunk(audio_path, start_time, end_time, i)
            print(f"Transcribing chunk {i+1}/{num_chunks}...")
            transcript: str = self.transcribe_audio_file(chunk_path)
            transcripts.append(transcript)
            
            # Clean up chunk file
            chunk_path.unlink()
        
        return " ".join(transcripts)
    
    def transcribe(self, video_path: Path, audio_path: Path | None = None, force: bool = False) -> str:
        """
        Transcribe video audio using OpenAI's Whisper model.
        
        Args:
            video_path: Path to the video file
            audio_path: Optional path for extracted audio file. If not provided, creates one based on video name
            force: If True, re-extract audio even if it exists
        
        Returns:
            Transcribed text from the video audio
        """
        # Validate inputs
        video_path = self.validate_video_file(video_path)
        audio_path = self.resolve_audio_path(video_path, audio_path)
        
        # Extract audio
        self.extract_audio(video_path, audio_path, force)
        
        # Get file size
        file_size_mb = audio_path.stat().st_size / (1024 * 1024)
        
        # Transcribe
        if file_size_mb > self.MAX_SIZE_MB:
            print(f"Audio file is {file_size_mb:.1f}MB (limit: {self.MAX_SIZE_MB}MB). Chunking...")
            duration = self.get_audio_duration(audio_path)
            num_chunks, chunk_duration = self.calculate_chunk_params(file_size_mb, duration)
            return self.transcribe_chunked_audio(audio_path, duration, num_chunks, chunk_duration)
        else:
            print("Transcribing audio...")
            return self.transcribe_audio_file(audio_path)


def get_api_key(api_key_arg: str | None) -> str:
    """Get API key from argument or environment variable."""
    api_key = api_key_arg or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OpenAI API key not provided. Use -k/--api-key or set OPENAI_API_KEY environment variable.")
    return api_key


def save_transcript(output_path: Path, transcript: str) -> None:
    """Save transcript to a file."""
    output_path.write_text(transcript)
    print(f"\nTranscript saved to: {output_path}")


def display_result(transcript: str) -> None:
    """Display transcription result."""
    print("\n" + "="*50)
    print("Transcription Result:")
    print("="*50)
    print(transcript)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Transcribe video audio using OpenAI's Whisper model"
    )
    parser.add_argument(
        "video_file",
        help="Path to the video file to transcribe"
    )
    parser.add_argument(
        "-k", "--api-key",
        help="OpenAI API key (defaults to OPENAI_API_KEY environment variable)"
    )
    parser.add_argument(
        "-o", "--output-audio",
        help="Path for extracted audio file (defaults to video name with .mp3 extension)"
    )
    parser.add_argument(
        "-s", "--save-transcript",
        help="Path to save the transcript to a file"
    )
    parser.add_argument(
        "-f", "--force",
        action="store_true",
        help="Re-extract audio even if it already exists"
    )
    
    args = parser.parse_args()
    
    try:
        api_key = get_api_key(args.api_key)
        transcriber = VideoTranscriber(api_key)
        
        video_path = Path(args.video_file)
        audio_path = Path(args.output_audio) if args.output_audio else None
        result = transcriber.transcribe(video_path, audio_path, args.force)
        display_result(result)
        
        if args.save_transcript:
            save_transcript(Path(args.save_transcript), result)
            
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()