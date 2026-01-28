"""Speaker diarization using pyannote.audio."""

import os
import re
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
                use_auth_token=self.hf_token,  # type: ignore[call-arg]
            )
        assert self.pipeline is not None
        return self.pipeline

    def diarize_audio(self, audio_path: Path) -> list[tuple[float, float, str]]:
        """Run speaker diarization on an audio file.

        Args:
            audio_path: Path to the audio file.

        Returns:
            List of (start_time, end_time, speaker_label) tuples in seconds.
        """
        pipeline = self._load_pipeline()
        diarization = pipeline(str(audio_path))

        segments = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
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
