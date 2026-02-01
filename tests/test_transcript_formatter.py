"""Tests for transcript_formatter module."""

from unittest.mock import MagicMock

from vtt_transcribe.transcript_formatter import TranscriptFormatter


class TestTranscriptFormatter:
    """Test TranscriptFormatter functionality."""

    def test_format_string_response(self) -> None:
        """Should return string as single-item list."""
        result = TranscriptFormatter.format("Simple text transcript")

        assert result == ["Simple text transcript"]

    def test_format_dict_with_segments_and_timestamps(self) -> None:
        """Should format dict response with segments and timestamps."""
        response: dict[str, object] = {
            "segments": [
                {"start": 0.0, "end": 5.0, "text": "Hello world"},
                {"start": 5.0, "end": 10.0, "text": "How are you?"},
            ]
        }

        result = TranscriptFormatter.format(response, include_timestamps=True)

        assert len(result) == 2
        assert result[0] == "[00:00:00 - 00:00:05] Hello world"
        assert result[1] == "[00:00:05 - 00:00:10] How are you?"

    def test_format_dict_without_timestamps(self) -> None:
        """Should format dict response without timestamps."""
        response: dict[str, object] = {
            "segments": [
                {"start": 0.0, "end": 5.0, "text": "Hello world"},
                {"start": 5.0, "end": 10.0, "text": "How are you?"},
            ]
        }

        result = TranscriptFormatter.format(response, include_timestamps=False)

        assert len(result) == 2
        assert result[0] == "Hello world"
        assert result[1] == "How are you?"

    def test_format_dict_with_empty_text(self) -> None:
        """Should skip segments with empty text."""
        response: dict[str, object] = {
            "segments": [
                {"start": 0.0, "end": 5.0, "text": "Hello"},
                {"start": 5.0, "end": 10.0, "text": "   "},
                {"start": 10.0, "end": 15.0, "text": "World"},
            ]
        }

        result = TranscriptFormatter.format(response)

        assert len(result) == 2
        assert "Hello" in result[0]
        assert "World" in result[1]

    def test_format_dict_without_segments(self) -> None:
        """Should fallback to text field if no segments."""
        response: dict[str, object] = {"text": "Full transcript text"}

        result = TranscriptFormatter.format(response)

        assert result == ["Full transcript text"]

    def test_format_sdk_response_with_segments(self) -> None:
        """Should format SDK-style response object."""
        mock_segment1 = MagicMock()
        mock_segment1.start = 0.0
        mock_segment1.end = 5.0
        mock_segment1.text = "First segment"

        mock_segment2 = MagicMock()
        mock_segment2.start = 5.0
        mock_segment2.end = 10.0
        mock_segment2.text = "Second segment"

        mock_response = MagicMock()
        mock_response.segments = [mock_segment1, mock_segment2]

        result = TranscriptFormatter.format(mock_response)

        assert len(result) == 2
        assert "First segment" in result[0]
        assert "Second segment" in result[1]

    def test_format_sdk_response_without_segments(self) -> None:
        """Should fallback to text attribute if no segments."""
        mock_response = MagicMock()
        mock_response.segments = None
        mock_response.text = "Fallback text"

        result = TranscriptFormatter.format(mock_response)

        assert result == ["Fallback text"]

    def test_format_timestamp_hours_minutes_seconds(self) -> None:
        """Should format timestamp as HH:MM:SS."""
        # 1 hour, 23 minutes, 45 seconds
        result = TranscriptFormatter.format_timestamp(5025.0)

        assert result == "01:23:45"

    def test_format_timestamp_only_minutes_seconds(self) -> None:
        """Should format timestamp with zero hours."""
        # 5 minutes, 30 seconds
        result = TranscriptFormatter.format_timestamp(330.0)

        assert result == "00:05:30"

    def test_format_timestamp_only_seconds(self) -> None:
        """Should format timestamp with zero hours and minutes."""
        result = TranscriptFormatter.format_timestamp(45.0)

        assert result == "00:00:45"

    def test_format_timestamp_zero(self) -> None:
        """Should format zero correctly."""
        result = TranscriptFormatter.format_timestamp(0.0)

        assert result == "00:00:00"

    def test_adjust_timestamps_with_offset(self) -> None:
        """Should adjust timestamps by offset."""
        lines = [
            "[00:00:00 - 00:00:05] First segment",
            "[00:00:05 - 00:00:10] Second segment",
        ]

        result = TranscriptFormatter.adjust_timestamps(lines, 60.0)

        assert result[0] == "[00:01:00 - 00:01:05] First segment"
        assert result[1] == "[00:01:05 - 00:01:10] Second segment"

    def test_adjust_timestamps_with_large_offset(self) -> None:
        """Should handle large time offsets correctly."""
        lines = ["[00:00:00 - 00:00:05] Text"]

        # Add 1 hour offset
        result = TranscriptFormatter.adjust_timestamps(lines, 3600.0)

        assert result[0] == "[01:00:00 - 01:00:05] Text"

    def test_adjust_timestamps_preserves_non_timestamp_lines(self) -> None:
        """Should preserve lines without timestamps."""
        lines = [
            "[00:00:00 - 00:00:05] Has timestamp",
            "No timestamp here",
            "[00:00:05 - 00:00:10] Another timestamp",
        ]

        result = TranscriptFormatter.adjust_timestamps(lines, 10.0)

        assert "[00:00:10 - 00:00:15]" in result[0]
        assert result[1] == "No timestamp here"
        assert "[00:00:15 - 00:00:20]" in result[2]

    def test_format_from_dict_strips_whitespace(self) -> None:
        """Should strip whitespace from segment text."""
        response: dict[str, object] = {
            "segments": [
                {"start": 0.0, "end": 5.0, "text": "  Hello  "},
                {"start": 5.0, "end": 10.0, "text": "\tWorld\n"},
            ]
        }

        result = TranscriptFormatter.format(response)

        assert "Hello" in result[0]
        assert "World" in result[1]
        assert not result[0].endswith("  ")
        assert not result[1].startswith("\t")


class TestTranscriptFormatterEdgeCases:
    """Test edge cases and error handling."""

    def test_format_empty_dict(self) -> None:
        """Should handle empty dictionary."""
        response: dict[str, list[dict[str, str]]] = {}
        result = TranscriptFormatter.format(response)

        assert result == []

    def test_format_dict_with_empty_segments(self) -> None:
        """Should handle empty segments list."""
        response: dict[str, object] = {"segments": []}

        result = TranscriptFormatter.format(response)

        assert result == []

    def test_format_sdk_with_none_text(self) -> None:
        """Should handle None text in SDK segments."""
        mock_segment = MagicMock()
        mock_segment.start = 0.0
        mock_segment.end = 5.0
        mock_segment.text = None

        mock_response = MagicMock()
        mock_response.segments = [mock_segment]

        result = TranscriptFormatter.format(mock_response)

        assert len(result) == 0  # Should skip None text

    def test_adjust_timestamps_empty_list(self) -> None:
        """Should handle empty list gracefully."""
        result = TranscriptFormatter.adjust_timestamps([], 10.0)

        assert result == []

    def test_adjust_timestamps_zero_offset(self) -> None:
        """Should handle zero offset."""
        lines = ["[00:00:00 - 00:00:05] Text"]

        result = TranscriptFormatter.adjust_timestamps(lines, 0.0)

        assert result[0] == "[00:00:00 - 00:00:05] Text"


def test_format_dict_segments_without_timestamps() -> None:
    """Test formatting dict segments without timestamps (text-only)."""
    response = {
        "segments": [
            {"start": 0.0, "end": 2.0, "text": "First"},
            {"start": 2.0, "end": 4.0, "text": ""},  # Empty text should be skipped
            {"start": 4.0, "end": 6.0, "text": "Second"},
        ]
    }

    lines = TranscriptFormatter.format(response, include_timestamps=False)

    assert len(lines) == 2
    assert lines[0] == "First"
    assert lines[1] == "Second"


def test_format_sdk_segments_without_timestamps() -> None:
    """Test formatting SDK response without timestamps (text-only)."""
    from unittest.mock import MagicMock

    response = MagicMock()
    segment1 = MagicMock()
    segment1.start = 0.0
    segment1.end = 2.0
    segment1.text = "First"

    segment2 = MagicMock()
    segment2.start = 2.0
    segment2.end = 4.0
    segment2.text = "Second"

    response.segments = [segment1, segment2]

    lines = TranscriptFormatter.format(response, include_timestamps=False)

    assert len(lines) == 2
    assert lines[0] == "First"
    assert lines[1] == "Second"
