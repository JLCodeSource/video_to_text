"""Transcript formatting utilities for different response types."""

import re
from typing import Any

from openai.types.audio.transcription_verbose import TranscriptionVerbose


class TranscriptFormatter:
    """Format transcription responses into readable text with timestamps."""

    @staticmethod
    def format(response: TranscriptionVerbose | dict | str, *, include_timestamps: bool = True) -> list[str]:
        """Format transcription response into text lines.

        Args:
            response: Transcription response (can be API object, dict, or string).
            include_timestamps: Whether to include timestamps in output.

        Returns:
            List of formatted transcript lines.
        """
        # Handle string response
        if isinstance(response, str):
            return [response]

        # Handle dictionary response
        if isinstance(response, dict):
            return TranscriptFormatter._format_from_dict(response, include_timestamps=include_timestamps)

        # Handle SDK response object
        return TranscriptFormatter._format_from_sdk(response, include_timestamps=include_timestamps)

    @staticmethod
    def _format_from_dict(response: dict, *, include_timestamps: bool) -> list[str]:
        """Format transcript from dictionary response."""
        lines: list[str] = []

        # Try to get segments from various possible locations
        segments = response.get("segments", [])

        if not segments:
            # Fallback to text-only response
            text = response.get("text", response.get("transcription", ""))
            return [text] if text else []

        for segment in segments:
            text = segment.get("text", "").strip()
            if not text:
                continue

            if include_timestamps:
                start = segment.get("start", 0)
                end = segment.get("end", 0)
                start_time = TranscriptFormatter.format_timestamp(start)
                end_time = TranscriptFormatter.format_timestamp(end)
                lines.append(f"[{start_time} - {end_time}] {text}")
            else:
                lines.append(text)

        return lines

    @staticmethod
    def _format_from_sdk(response: TranscriptionVerbose | Any, *, include_timestamps: bool) -> list[str]:
        """Format transcript from SDK-style response object."""
        lines: list[str] = []

        # Try to access segments attribute
        segments_attr = getattr(response, "segments", None)
        if not segments_attr:
            # Fallback to text attribute
            text = getattr(response, "text", "")
            return [text] if text else []

        for segment in segments_attr:
            text_attr = getattr(segment, "text", "")
            text = str(text_attr).strip() if text_attr is not None else ""
            if not text:
                continue

            if include_timestamps:
                start = getattr(segment, "start", 0)
                end = getattr(segment, "end", 0)
                start_time = TranscriptFormatter.format_timestamp(start)
                end_time = TranscriptFormatter.format_timestamp(end)
                lines.append(f"[{start_time} - {end_time}] {text}")
            else:
                lines.append(text)

        return lines

    @staticmethod
    def format_timestamp(seconds: float) -> str:
        """Convert seconds to HH:MM:SS format.

        Args:
            seconds: Time in seconds.

        Returns:
            Formatted timestamp string.
        """
        try:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
        except (TypeError, ValueError):
            # Fallback for invalid input
            hours, minutes, secs = 0, 0, 0
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    @staticmethod
    def adjust_timestamps(lines: list[str], offset_seconds: float) -> list[str]:
        """Adjust timestamps in formatted lines by an offset.

        Args:
            lines: List of formatted transcript lines with timestamps.
            offset_seconds: Seconds to add to all timestamps.

        Returns:
            List of lines with adjusted timestamps.
        """
        adjusted_lines = []
        timestamp_pattern = r"\[(\d{2}):(\d{2}):(\d{2}) - (\d{2}):(\d{2}):(\d{2})\]"

        for line in lines:
            match = re.match(timestamp_pattern, line)
            if match:
                # Extract timestamps
                start_h, start_m, start_s, end_h, end_m, end_s = map(int, match.groups())

                # Calculate total seconds
                start_total = start_h * 3600 + start_m * 60 + start_s + offset_seconds
                end_total = end_h * 3600 + end_m * 60 + end_s + offset_seconds

                # Format new timestamps
                new_start = TranscriptFormatter.format_timestamp(start_total)
                new_end = TranscriptFormatter.format_timestamp(end_total)

                # Replace timestamps in line
                text = line[match.end() :].strip()
                adjusted_lines.append(f"[{new_start} - {new_end}] {text}")
            else:
                adjusted_lines.append(line)

        return adjusted_lines
