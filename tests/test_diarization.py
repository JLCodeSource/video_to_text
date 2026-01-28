"""Tests for speaker diarization functionality."""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Suppress torchcodec warning
pytestmark = pytest.mark.filterwarnings("ignore::UserWarning:pyannote.audio.core.io")


def test_speaker_diarizer_can_import_pyannote() -> None:
    """Test that pyannote.audio can be imported."""
    try:
        from pyannote.audio import Pipeline  # type: ignore[import-not-found]  # noqa: F401
    except ImportError:
        pytest.fail("pyannote.audio not installed")


def test_speaker_diarizer_initialization_with_token() -> None:
    """Test SpeakerDiarizer can be initialized with a token."""
    from vtt.diarization import SpeakerDiarizer  # type: ignore[import-not-found]

    diarizer = SpeakerDiarizer(hf_token="test_token")  # noqa: S106
    assert diarizer.hf_token == "test_token"  # noqa: S105


def test_speaker_diarizer_initialization_from_env() -> None:
    """Test SpeakerDiarizer can be initialized from HF_TOKEN env var."""
    from vtt.diarization import SpeakerDiarizer  # type: ignore[import-not-found]

    os.environ["HF_TOKEN"] = "env_token"  # noqa: S105
    try:
        diarizer = SpeakerDiarizer()
        assert diarizer.hf_token == "env_token"  # noqa: S105
    finally:
        del os.environ["HF_TOKEN"]


def test_speaker_diarizer_initialization_no_token_raises_error() -> None:
    """Test SpeakerDiarizer raises error when no token provided."""
    from vtt.diarization import SpeakerDiarizer  # type: ignore[import-not-found]

    # Ensure HF_TOKEN is not set
    os.environ.pop("HF_TOKEN", None)

    with pytest.raises(ValueError, match="Hugging Face token not provided"):
        SpeakerDiarizer()


def test_diarize_audio_returns_speaker_segments() -> None:
    """Test diarize_audio returns list of speaker segments."""
    from vtt.diarization import SpeakerDiarizer  # type: ignore[import-not-found]

    diarizer = SpeakerDiarizer(hf_token="test_token")  # noqa: S106

    # Mock the pipeline
    mock_turn = MagicMock()
    mock_turn.start = 0.0
    mock_turn.end = 5.0

    mock_pipeline = MagicMock()
    mock_pipeline.return_value.itertracks.return_value = [
        (mock_turn, None, "SPEAKER_00"),
    ]

    with patch("vtt.diarization.Pipeline.from_pretrained", return_value=mock_pipeline):
        audio_path = Path("/fake/audio.mp3")
        segments = diarizer.diarize_audio(audio_path)  # type: ignore[attr-defined]

        assert len(segments) == 1
        assert segments[0] == (0.0, 5.0, "SPEAKER_00")


def test_apply_speakers_to_transcript_adds_labels() -> None:
    """Test apply_speakers_to_transcript adds speaker labels to transcript."""
    from vtt.diarization import SpeakerDiarizer  # type: ignore[import-not-found]

    diarizer = SpeakerDiarizer(hf_token="test_token")  # noqa: S106

    transcript = "[00:00 - 00:05] Hello world"
    speaker_segments = [(0.0, 5.0, "SPEAKER_00")]

    result = diarizer.apply_speakers_to_transcript(transcript, speaker_segments)  # type: ignore[attr-defined]

    assert result == "[00:00 - 00:05] SPEAKER_00: Hello world"


def test_apply_speakers_to_transcript_empty_segments() -> None:
    """Test apply_speakers_to_transcript returns transcript unchanged when no segments."""
    from vtt.diarization import SpeakerDiarizer  # type: ignore[import-not-found]

    diarizer = SpeakerDiarizer(hf_token="test_token")  # noqa: S106

    transcript = "[00:00 - 00:05] Hello world"
    speaker_segments: list[tuple[float, float, str]] = []

    result = diarizer.apply_speakers_to_transcript(transcript, speaker_segments)  # type: ignore[attr-defined]

    assert result == transcript


def test_apply_speakers_to_transcript_no_match() -> None:
    """Test apply_speakers_to_transcript handles lines without timestamp match."""
    from vtt.diarization import SpeakerDiarizer  # type: ignore[import-not-found]

    diarizer = SpeakerDiarizer(hf_token="test_token")  # noqa: S106

    transcript = "Plain text without timestamps\n[00:00 - 00:05] Hello"
    speaker_segments = [(0.0, 5.0, "SPEAKER_00")]

    result = diarizer.apply_speakers_to_transcript(transcript, speaker_segments)  # type: ignore[attr-defined]

    assert "Plain text without timestamps" in result
    assert "SPEAKER_00: Hello" in result


def test_apply_speakers_to_transcript_no_speaker_found() -> None:
    """Test apply_speakers_to_transcript when no speaker matches timestamp."""
    from vtt.diarization import SpeakerDiarizer  # type: ignore[import-not-found]

    diarizer = SpeakerDiarizer(hf_token="test_token")  # noqa: S106

    transcript = "[00:10 - 00:15] Hello"
    speaker_segments = [(0.0, 5.0, "SPEAKER_00")]  # Doesn't overlap with timestamp

    result = diarizer.apply_speakers_to_transcript(transcript, speaker_segments)  # type: ignore[attr-defined]

    assert result == "[00:10 - 00:15] Hello"  # Unchanged


def test_find_speaker_at_time_no_match() -> None:
    """Test _find_speaker_at_time returns None when no speaker found."""
    from vtt.diarization import SpeakerDiarizer  # type: ignore[import-not-found]

    diarizer = SpeakerDiarizer(hf_token="test_token")  # noqa: S106

    speaker_segments = [(0.0, 5.0, "SPEAKER_00"), (10.0, 15.0, "SPEAKER_01")]

    result = diarizer._find_speaker_at_time(7.5, speaker_segments)  # type: ignore[attr-defined]

    assert result is None


def test_format_diarization_output() -> None:
    """Test format_diarization_output formats segments correctly."""
    from vtt.diarization import format_diarization_output

    segments = [(0.0, 5.0, "SPEAKER_00"), (65.0, 125.0, "SPEAKER_01")]

    result = format_diarization_output(segments)

    assert "[00:00 - 00:05] SPEAKER_00" in result
    assert "[01:05 - 02:05] SPEAKER_01" in result
