import contextlib
from pathlib import Path
from typing import TYPE_CHECKING

from openai import OpenAI

from vtt_transcribe.audio_chunker import AudioChunker
from vtt_transcribe.audio_manager import AudioFileManager
from vtt_transcribe.transcript_formatter import TranscriptFormatter

if TYPE_CHECKING:
    from openai.types.audio.transcription_verbose import TranscriptionVerbose

# Constants
MAX_FILE_SIZE_MB = 25
AUDIO_EXTENSION = ".mp3"


class VideoTranscriber:
    """Transcribe video audio using OpenAI's Whisper model."""

    MAX_SIZE_MB = MAX_FILE_SIZE_MB
    SUPPORTED_AUDIO_FORMATS = (".mp3", ".wav", ".ogg", ".m4a")

    def __init__(self, api_key: str) -> None:
        """Initialize transcriber with API key."""
        self.api_key: str = api_key
        self.client = OpenAI(api_key=api_key)

    def validate_input_file(self, input_path: Path) -> Path:
        """Validate and return video file path."""
        if not input_path.exists():
            msg = f"Input file not found: {input_path}"
            raise FileNotFoundError(msg)
        return input_path

    def resolve_audio_path(self, input_path: Path, audio_path: Path | None) -> Path:
        """Resolve audio file path, ensuring .mp3 extension."""
        if audio_path is None:
            return input_path.with_suffix(AUDIO_EXTENSION)
        # Custom audio path handling
        if audio_path.suffix.lower() == ".mp3":
            # Already has .mp3 extension, accept as-is
            return audio_path
        if audio_path.suffix == "":
            # No extension, add .mp3
            return audio_path.with_suffix(AUDIO_EXTENSION)
        # Different extension, raise error
        msg = f"Audio file must have .mp3 extension, got: {audio_path}"
        raise ValueError(msg)

    def extract_audio(self, input_path: Path, audio_path: Path, *, force: bool = False) -> None:
        """Extract audio from video file (delegates to AudioFileManager)."""
        if audio_path.exists() and not force:
            file_size_mb = audio_path.stat().st_size / (1024 * 1024)
            print(f"Using existing audio file: {audio_path} ({file_size_mb:.1f}MB)")
            return
        AudioFileManager.extract_from_video(input_path, audio_path, force=force)

    def get_audio_duration(self, audio_path: Path) -> float:
        """Get audio file duration (delegates to AudioFileManager)."""
        return AudioFileManager.get_duration(audio_path)

    def find_existing_chunks(self, audio_path: Path) -> list[Path]:
        """Find all chunk files (delegates to AudioFileManager)."""
        return AudioFileManager.find_chunks(audio_path)

    def cleanup_audio_files(self, audio_path: Path) -> None:
        """Delete audio file and chunks (delegates to AudioFileManager)."""
        # Find chunks before deleting
        chunks = AudioFileManager.find_chunks(audio_path)

        # Delete everything
        AudioFileManager.cleanup_files(audio_path)

        # Report what was deleted
        print(f"Deleted audio file: {audio_path}")
        for chunk in chunks:
            print(f"Deleted chunk file: {chunk}")

    def cleanup_audio_chunks(self, audio_path: Path) -> None:
        """Delete only chunk files (delegates to AudioFileManager)."""
        chunks = AudioFileManager.find_chunks(audio_path)
        AudioFileManager.cleanup_chunks_only(audio_path)
        if chunks:
            print(f"Deleted {len(chunks)} chunk files")

    def calculate_chunk_params(self, file_size_mb: float, duration: float) -> tuple[int, float]:
        """Calculate chunk parameters (delegates to AudioChunker)."""
        return AudioChunker.calculate_chunk_params(file_size_mb, duration)

    def extract_audio_chunk(self, audio_path: Path, start_time: float, end_time: float, chunk_index: int) -> Path:
        """Extract audio chunk (delegates to AudioFileManager)."""
        return AudioFileManager.extract_chunk(audio_path, start_time, end_time, chunk_index)

    def transcribe_audio_file(self, audio_path: Path) -> str:
        """Transcribe a single audio file using Whisper API with timestamps."""
        with open(audio_path, "rb") as audio_file:
            response: TranscriptionVerbose = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json",
            )

        formatted = self._format_transcript_with_timestamps(response)

        # Diagnostic: if we got an empty transcript, print response details
        if not formatted or not formatted.strip():
            try:
                print("DEBUG: Empty formatted transcript produced")
                print(f"DEBUG: response type: {type(response)!r}")
                # If it's a dict-like response, show top-level keys
                if isinstance(response, dict):
                    print(f"DEBUG: response keys: {list(response.keys())}")
                    # If there is raw text, print a preview
                    if "text" in response:
                        preview = (response.get("text") or "")[:200]
                        print(f"DEBUG: response[text] preview: {preview!r}")
                else:
                    preview = str(response)[:400]
                    print(f"DEBUG: response preview: {preview!r}")
            except Exception as e:
                msg = f"DEBUG: error while printing response: {e}"
                print(msg)

        return formatted

    def _format_transcript_with_timestamps(self, response: "TranscriptionVerbose") -> str:
        """Format transcript with timestamps (delegates to TranscriptFormatter)."""
        lines = TranscriptFormatter.format(response, include_timestamps=True)
        return "\n".join(lines)

    def _format_timestamp(self, seconds: float) -> str:
        """Format timestamp (delegates to TranscriptFormatter)."""
        return TranscriptFormatter.format_timestamp(seconds)

    def transcribe_chunked_audio(
        self,
        audio_path: Path,
        duration: float,
        num_chunks: int,
        chunk_duration: float,
        *,
        keep_chunks: bool = False,
    ) -> str:
        """Transcribe audio by splitting into chunks.

        This method will reuse existing chunk files when they already exist and
        match the expected number of chunks. The actual transcription and
        per-chunk cleanup logic is delegated to `_transcribe_chunk_files` to
        reduce cyclomatic complexity.
        """
        print(f"Splitting into {num_chunks} chunks ({chunk_duration:.1f}s each)...")

        # Determine chunk file list: reuse existing or create new ones
        existing_chunks = self.find_existing_chunks(audio_path)
        if existing_chunks and len(existing_chunks) == num_chunks:
            chunk_files = existing_chunks
        else:
            chunk_files = []
            for i in range(num_chunks):
                start_time: float = i * chunk_duration
                end_time: float = min((i + 1) * chunk_duration, duration)

                # Extract chunk file
                chunk_path: Path = self.extract_audio_chunk(audio_path, start_time, end_time, i)
                chunk_files.append(chunk_path)

        transcripts = self._transcribe_chunk_files(chunk_files, chunk_duration, keep_chunks=keep_chunks)

        if keep_chunks and chunk_files:
            print(f"Kept {len(chunk_files)} chunk files for reference")

        return " ".join(transcripts)

    def _transcribe_chunk_files(self, chunk_files: list[Path], chunk_duration: float, *, keep_chunks: bool) -> list[str]:
        """Transcribe provided chunk files and optionally remove them.

        Using `contextlib.suppress` to ignore unlink errors and keeping this
        logic isolated reduces complexity in the main method.
        """
        transcripts: list[str] = []
        for i, chunk_path in enumerate(chunk_files):
            start_time = i * chunk_duration
            print(f"Transcribing chunk {i + 1}/{len(chunk_files)}...")
            transcript: str = self.transcribe_audio_file(chunk_path)
            if transcript and start_time > 0:
                transcript = self._shift_formatted_timestamps(transcript, start_time)
            transcripts.append(transcript)
            if not keep_chunks:
                with contextlib.suppress(Exception):
                    chunk_path.unlink()

        return transcripts

    def _shift_formatted_timestamps(self, formatted: str, offset_seconds: float) -> str:
        """Shift timestamps in formatted transcript (delegates to TranscriptFormatter)."""
        lines = formatted.split("\n")
        adjusted_lines = TranscriptFormatter.adjust_timestamps(lines, offset_seconds)
        return "\n".join(adjusted_lines)

    def _transcribe_sibling_chunks(self, base_audio_path: Path) -> str:
        """Transcribe all sibling chunks with timestamp shifting."""
        all_chunks = self.find_existing_chunks(base_audio_path)
        if not all_chunks:
            return ""

        print(f"Found {len(all_chunks)} chunk files, processing in order...")
        transcripts = []
        cumulative_start = 0.0
        for chunk_path in all_chunks:
            print(f"Transcribing {chunk_path.name}...")
            transcript = self.transcribe_audio_file(chunk_path)
            # Shift timestamps by cumulative offset for chunks after the first
            if transcript and cumulative_start > 0:
                transcript = self._shift_formatted_timestamps(transcript, cumulative_start)
            transcripts.append(transcript)
            # Update cumulative start by the duration of this chunk
            with contextlib.suppress(Exception):
                cumulative_start += self.get_audio_duration(chunk_path)
        # Separate chunk transcripts with blank lines for readability
        return "\n\n".join(transcripts)

    def transcribe(
        self,
        input_path: Path,
        audio_path: Path | None = None,
        *,
        force: bool = False,
        keep_audio: bool = True,
        scan_chunks: bool = False,
    ) -> str:
        """
        Transcribe video audio using OpenAI's Whisper model.

        Args:
            input_path: Path to the video file or audio file
            audio_path: Optional path for extracted audio file. If not provided, creates one based on video name
            force: If True, re-extract audio even if it exists
            keep_audio: If True, keep audio files after transcription. If False, delete them.
            scan_chunks: If True and input is a chunk file, find and process all sibling chunks in order

        Returns:
            Transcribed text from the video audio
        """
        # Check if input is already an audio file
        is_audio_input = input_path.suffix.lower() in self.SUPPORTED_AUDIO_FORMATS

        if is_audio_input:
            # Validate audio file exists
            if not input_path.exists():
                msg = f"Audio file not found: {input_path}"
                raise FileNotFoundError(msg)

            # Reject -o flag with audio input
            if audio_path is not None:
                msg = "Cannot specify -o/--output-audio when input is already an audio file"
                raise ValueError(msg)

            # Direct audio input: use it directly, no extraction needed
            audio_path = input_path

            # Check if this is a chunk file and scan_chunks is enabled
            if scan_chunks and "_chunk" in audio_path.stem:
                # Extract base name (remove _chunkN suffix)
                base_stem = audio_path.stem.split("_chunk")[0]
                base_audio_path = audio_path.with_stem(base_stem)
                # Find and transcribe all sibling chunks
                result = self._transcribe_sibling_chunks(base_audio_path)
                if result:
                    return result
        else:
            # Validate inputs
            input_path = self.validate_input_file(input_path)
            audio_path = self.resolve_audio_path(input_path, audio_path)

            # Extract audio
            self.extract_audio(input_path, audio_path, force=force)

        # Get file size
        file_size_mb = audio_path.stat().st_size / (1024 * 1024)

        # Transcribe
        if file_size_mb > self.MAX_SIZE_MB:
            print(f"Input file is {file_size_mb:.1f}MB (limit: {self.MAX_SIZE_MB}MB). Chunking...")
            duration = self.get_audio_duration(audio_path)
            num_chunks, chunk_duration = self.calculate_chunk_params(file_size_mb, duration)
            result = self.transcribe_chunked_audio(
                audio_path,
                duration,
                num_chunks,
                chunk_duration,
                keep_chunks=keep_audio,
            )
        else:
            print("Transcribing audio...")
            result = self.transcribe_audio_file(audio_path)

        # Clean up audio files if not keeping them
        if not keep_audio:
            self.cleanup_audio_files(audio_path)

        return result
