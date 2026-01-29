"""Speaker diarization using pyannote.audio."""

import os
import re
import warnings
from pathlib import Path

from pyannote.audio import Pipeline  # type: ignore[import-not-found]


class SpeakerDiarizer:
    """Speaker diarization using pyannote.audio."""

    def __init__(self, hf_token: str | None = None) -> None:
        """Initialize diarizer with Hugging Face token.

        Args:
            hf_token: Hugging Face token for model access. If None, uses HF_TOKEN env var.

        Raises:
            ValueError: If no token is provided and HF_TOKEN env var is not set.
        """
        self.hf_token = hf_token or os.environ.get("HF_TOKEN")
        if not self.hf_token:
            msg = "Hugging Face token not provided. Use --hf-token or set HF_TOKEN environment variable."
            raise ValueError(msg)
        self.pipeline: Pipeline | None = None

    def _load_pipeline(self) -> Pipeline:
        """Lazy load the diarization pipeline."""
        if self.pipeline is None:
            self.pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                token=self.hf_token,
            )
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
                    import re

                    match = re.search(r"resulted in (\d+) samples instead of the expected (\d+) samples", error_str)
                    if match:
                        actual_samples = int(match.group(1))
                        expected_samples = int(match.group(2))
                        sample_rate = 44100  # pyannote default
                        actual_duration = actual_samples / sample_rate
                        expected_duration = expected_samples / sample_rate

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
            transcript: Transcript with [MM:SS - MM:SS] text format.
            speaker_segments: List of (start_time, end_time, speaker_label) tuples.

        Returns:
            Transcript with speaker labels: [MM:SS - MM:SS] Speaker: text
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
        # Match timestamp pattern [MM:SS - MM:SS]
        match = re.match(r"\[(\d{2}):(\d{2}) - (\d{2}):(\d{2})\] (.+)", line)
        if not match:
            return line

        start_min, start_sec, end_min, end_sec, text = match.groups()
        start_time = int(start_min) * 60 + int(start_sec)
        end_time = int(end_min) * 60 + int(end_sec)

        # Find speaker for this segment (use midpoint for matching)
        midpoint = (start_time + end_time) / 2
        speaker = self._find_speaker_at_time(midpoint, speaker_segments)

        if speaker:
            return f"[{start_min}:{start_sec} - {end_min}:{end_sec}] {speaker}: {text}"
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
