"""Speaker diarization using pyannote.audio.

Timestamp Format:
    The primary timestamp format used throughout this module is HH:MM:SS (hours:minutes:seconds).
    This aligns with the TranscriptFormatter output format. Some functions maintain backward
    compatibility with the legacy MM:SS format for parsing existing transcripts.
"""

import logging
import os
import re
import shutil
import sys
import warnings
from pathlib import Path

import torch
from pyannote.audio import Pipeline

logger = logging.getLogger(__name__)


def check_ffmpeg_installed() -> None:
    """Check if ffmpeg is installed and available in PATH.

    Raises:
        SystemExit: If ffmpeg is not found, with installation instructions.
    """
    if shutil.which("ffmpeg") is None:
        print("\nError: ffmpeg is not installed or not in PATH.", file=sys.stderr)
        print("\nSpeaker diarization requires ffmpeg to be installed.", file=sys.stderr)
        print("\nInstallation instructions:", file=sys.stderr)
        print("  • Ubuntu/Debian: sudo apt-get install ffmpeg", file=sys.stderr)
        print("  • macOS (Homebrew): brew install ffmpeg", file=sys.stderr)
        print("  • Windows (Chocolatey): choco install ffmpeg", file=sys.stderr)
        print("  • Windows (Scoop): scoop install ffmpeg", file=sys.stderr)
        print("  • Or download from: https://ffmpeg.org/download.html\n", file=sys.stderr)
        sys.exit(1)


# Constants
DEFAULT_DIARIZATION_MODEL = "pyannote/speaker-diarization-3.1"
# Default sample rate used by pyannote.audio v3.x
PYANNOTE_DEFAULT_SAMPLE_RATE = 44100


def resolve_device(device: str) -> str:
    """Resolve device string to actual device (cuda or cpu).

    Args:
        device: Device specification ("auto", "cuda", "gpu", or "cpu").

    Returns:
        Resolved device string ("cuda" or "cpu").

    Note:
        If DISABLE_GPU environment variable is set, always returns "cpu".
    """
    # Check if GPU is disabled via env var
    if os.environ.get("DISABLE_GPU"):
        return "cpu"

    # Map "gpu" alias to "cuda"
    if device == "gpu":
        device = "cuda"

    if device == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"
    return device


class SpeakerDiarizer:
    """Speaker diarization using pyannote.audio."""

    def __init__(self, hf_token: str | None = None, device: str = "auto") -> None:
        """Initialize diarizer with Hugging Face token.

        Args:
            hf_token: Hugging Face token for model access. If None, uses HF_TOKEN env var.
            device: Device to use ("auto", "cuda", or "cpu"). Default is "auto".

        Raises:
            ValueError: If no token is provided and HF_TOKEN env var is not set.
            SystemExit: If ffmpeg is not installed.
        """
        # Check ffmpeg is available before proceeding
        check_ffmpeg_installed()

        self.hf_token = hf_token or os.environ.get("HF_TOKEN")
        if not self.hf_token:
            msg = "Hugging Face token not provided. Use --hf-token or set HF_TOKEN environment variable."
            raise ValueError(msg)
        self.device = device
        self.pipeline: Pipeline | None = None

    def _load_pipeline(self) -> Pipeline:
        """Lazy load the diarization pipeline and move to device."""
        if self.pipeline is None:
            # Suppress TF32 reproducibility warning from pyannote
            # TF32 is disabled by pyannote for accuracy/reproducibility
            warnings.filterwarnings(
                "ignore",
                category=UserWarning,
                module="pyannote.audio.utils.reproducibility",
                message=".*TF32.*",
            )

            self.pipeline = Pipeline.from_pretrained(
                DEFAULT_DIARIZATION_MODEL,
                token=self.hf_token,
            )
            # Resolve and set device
            resolved_device = resolve_device(self.device)
            device = torch.device(resolved_device)

            logger.info("Loading diarization pipeline on device: %s", resolved_device)

            # Move pipeline to device using its .to() method
            try:
                assert self.pipeline is not None
                self.pipeline.to(device)
                logger.info("Successfully moved diarization pipeline to %s", resolved_device)

                # Verify device placement by checking if GPU memory was allocated
                if resolved_device == "cuda" and torch.cuda.is_available():
                    mem_allocated = torch.cuda.memory_allocated(0) / 1024**2
                    logger.info("GPU memory allocated: %.2f MB", mem_allocated)
                    if mem_allocated < 1.0:
                        logger.warning(
                            "GPU memory allocation is very low (%.2f MB). Pipeline may still be on CPU.",
                            mem_allocated,
                        )
            except Exception as e:
                # Fallback to CPU if device move fails
                logger.warning("Failed to move pipeline to %s: %s. Using CPU.", resolved_device, e)
        assert self.pipeline is not None
        return self.pipeline

    def diarize_audio(self, audio_path: Path) -> list[tuple[float, float, str]]:
        """Run speaker diarization on an audio file.

        Args:
            audio_path: Path to the audio file.

        Returns:
            List of (start_time, end_time, speaker_label) tuples in seconds.

        Raises:
            ValueError: If audio file is too short (less than 10 seconds required).

        Note:
            The pyannote.audio model requires audio files to be at least 10 seconds long.
            For shorter audio files, consider padding with silence or using a different model.
        """
        pipeline = self._load_pipeline()

        # Suppress the torch pooling warning about degrees of freedom
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message=".*degrees of freedom.*", category=UserWarning)
            try:
                diarization = pipeline(str(audio_path))
            except ValueError as e:
                error_str = str(e)
                # Check if it's a sample mismatch error from pyannote
                if "requested chunk" in error_str and "samples" in error_str and "instead of the expected" in error_str:
                    # This is a pyannote error - could be file corruption, metadata issues, or truly too short
                    # Extract sample counts to provide better error message
                    match = re.search(r"resulted in (\d+) samples instead of the expected (\d+) samples", error_str)
                    if match:
                        actual_samples = int(match.group(1))
                        expected_samples = int(match.group(2))
                        actual_duration = actual_samples / PYANNOTE_DEFAULT_SAMPLE_RATE
                        expected_duration = expected_samples / PYANNOTE_DEFAULT_SAMPLE_RATE

                        # If actual duration < 10 seconds, it's genuinely too short
                        if actual_duration < 10.0:
                            msg = (
                                f"Audio file is too short for diarization ({actual_duration:.2f}s). "
                                f"The pyannote.audio model requires at least 10 seconds of audio."
                            )
                            raise ValueError(msg) from e
                        # File is long enough but has sample mismatch - likely metadata/encoding issue
                        msg = (
                            f"Audio file sample mismatch error. This usually indicates:\n"
                            f"  - File corruption or incomplete download\n"
                            f"  - Metadata mismatch (reported duration doesn't match actual audio)\n"
                            f"  - Unusual encoding that pyannote can't handle properly\n"
                            f"Expected {expected_duration:.2f}s ({expected_samples} samples), "
                            f"but got {actual_duration:.2f}s ({actual_samples} samples).\n\n"
                            f"Try re-encoding to WAV format (more compatible but larger file):\n"
                            f"  ffmpeg -i input.mp3 -acodec pcm_s16le -ar 16000 -ac 1 output.wav"
                        )
                        raise ValueError(msg) from e
                # Other ValueError - just re-raise
                raise

        segments = []
        for turn, _, speaker in diarization.speaker_diarization.itertracks(yield_label=True):
            segments.append((turn.start, turn.end, speaker))

        return segments

    def apply_speakers_to_transcript(
        self,
        transcript: str,
        speaker_segments: list[tuple[float, float, str]],
    ) -> str:
        """Apply speaker labels to timestamped transcript.

        Args:
            transcript: Transcript with [HH:MM:SS - HH:MM:SS] text format.
            speaker_segments: List of (start_time, end_time, speaker_label) tuples.

        Returns:
            Transcript with speaker labels: [HH:MM:SS - HH:MM:SS] Speaker: text
        """
        if not speaker_segments:
            return transcript

        lines = transcript.split("\n")
        labeled_lines = [self._process_line(line, speaker_segments) for line in lines]
        return "\n".join(labeled_lines)

    def _process_line(self, line: str, speaker_segments: list[tuple[float, float, str]]) -> str:
        """Process a single transcript line and add speaker label if applicable.

        Args:
            line: Single line from transcript.
            speaker_segments: List of (start_time, end_time, speaker_label) tuples.

        Returns:
            Line with speaker label added, or original line if no match.
        """
        # Match timestamp pattern [HH:MM:SS - HH:MM:SS] or [MM:SS - MM:SS]
        match = re.match(r"\[(\d{2}):(\d{2}):(\d{2}) - (\d{2}):(\d{2}):(\d{2})\] (.+)", line)
        if match:
            start_hr, start_min, start_sec, end_hr, end_min, end_sec, text = match.groups()
            start_time = int(start_hr) * 3600 + int(start_min) * 60 + int(start_sec)
            end_time = int(end_hr) * 3600 + int(end_min) * 60 + int(end_sec)
            timestamp = f"{start_hr}:{start_min}:{start_sec} - {end_hr}:{end_min}:{end_sec}"
        else:
            # Try MM:SS format
            match = re.match(r"\[(\d{2}):(\d{2}) - (\d{2}):(\d{2})\] (.+)", line)
            if not match:
                return line
            start_min, start_sec, end_min, end_sec, text = match.groups()
            start_time = int(start_min) * 60 + int(start_sec)
            end_time = int(end_min) * 60 + int(end_sec)
            timestamp = f"{start_min}:{start_sec} - {end_min}:{end_sec}"

        # Find speaker for this segment (use midpoint for matching)
        midpoint = (start_time + end_time) / 2
        speaker = self._find_speaker_at_time(midpoint, speaker_segments)

        if speaker:
            return f"[{timestamp}] {speaker}: {text}"
        return line

    def _find_speaker_at_time(
        self,
        time: float,
        speaker_segments: list[tuple[float, float, str]],
    ) -> str | None:
        """Find the speaker label at a given time.

        Args:
            time: Time in seconds.
            speaker_segments: List of (start_time, end_time, speaker_label) tuples.

        Returns:
            Speaker label if found, None otherwise.
        """
        for start, end, speaker in speaker_segments:
            if start <= time <= end:
                return speaker
        return None


def format_diarization_output(segments: list[tuple[float, float, str]]) -> str:
    """Format diarization segments into human-readable output.

    Args:
        segments: List of (start_time, end_time, speaker_label) tuples.

    Returns:
        Formatted string with [MM:SS - MM:SS] Speaker format.
    """

    def format_time(seconds: float) -> str:
        total_seconds = int(seconds)
        minutes = total_seconds // 60
        secs = total_seconds % 60
        return f"{minutes:02d}:{secs:02d}"

    lines = []
    for start, end, speaker in segments:
        start_str = format_time(start)
        end_str = format_time(end)
        lines.append(f"[{start_str} - {end_str}] {speaker}")

    return "\n".join(lines)


def get_unique_speakers(segments: list[tuple[float, float, str]]) -> list[str]:
    """Extract unique speaker labels from segments in order of first appearance.

    Args:
        segments: List of (start_time, end_time, speaker_label) tuples.

    Returns:
        List of unique speaker labels in order of first appearance.
    """
    seen = set()
    speakers = []
    for _, _, speaker in segments:
        if speaker not in seen:
            seen.add(speaker)
            speakers.append(speaker)
    return speakers


def get_speaker_context_lines(
    transcript: str,
    speaker_label: str,
    context_lines: int = 5,
) -> list[str]:
    """Extract context lines for a specific speaker's segments from transcript.

    Args:
        transcript: Transcript with [HH:MM:SS - HH:MM:SS] SPEAKER_XX: text format.
                   Also accepts legacy [MM:SS - MM:SS] format for backward compatibility.
        speaker_label: Speaker label to extract contexts for.
        context_lines: Number of lines to show before and after each speaker segment group.

    Returns:
        List of context strings, one per continuous segment group for the speaker.
    """
    # Split transcript into lines
    lines = transcript.split("\n")

    # Build a mapping of line index to speaker label by parsing the line
    line_to_speaker = {}
    for i, line in enumerate(lines):
        # Match pattern: [HH:MM:SS - HH:MM:SS] SPEAKER_XX: text
        # The optional (?:\d{2}:)? group provides backward compatibility with legacy [MM:SS - MM:SS] format
        match = re.match(r"\[(?:\d{2}:)?\d{2}:\d{2} - (?:\d{2}:)?\d{2}:\d{2}\]\s+(SPEAKER_\d+):?", line)
        if match:
            line_to_speaker[i] = match.group(1)

    # Find groups of continuous segments for the speaker
    speaker_groups = []
    current_group = []
    for i in range(len(lines)):
        if line_to_speaker.get(i) == speaker_label:
            current_group.append(i)
        elif current_group:
            # End of a group
            speaker_groups.append(current_group)
            current_group = []
    if current_group:
        speaker_groups.append(current_group)

    # Extract context for each group
    contexts = []
    for group in speaker_groups:
        start_idx = max(0, group[0] - context_lines)
        end_idx = min(len(lines), group[-1] + context_lines + 1)
        context = "\n".join(lines[start_idx:end_idx])
        contexts.append(context)

    return contexts
