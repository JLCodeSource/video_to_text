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

    # Mock the pipeline and its return value structure
    mock_turn = MagicMock()
    mock_turn.start = 0.0
    mock_turn.end = 5.0

    mock_diarization = MagicMock()
    mock_diarization.speaker_diarization.itertracks.return_value = [
        (mock_turn, None, "SPEAKER_00"),
    ]

    mock_pipeline = MagicMock()
    mock_pipeline.return_value = mock_diarization

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


def test_diarize_audio_short_file_raises_error() -> None:
    """Test that diarizing a short audio file raises a helpful error."""
    from vtt.diarization import SpeakerDiarizer

    diarizer = SpeakerDiarizer(hf_token="test_token")  # noqa: S106

    # Mock the pipeline to raise the short audio error
    mock_pipeline = MagicMock()
    mock_pipeline.return_value = MagicMock()
    mock_pipeline.side_effect = ValueError(
        "requested chunk [ 00:00:00.000 --> 00:00:10.000] resulted in 100 samples instead of the expected 441000 samples"
    )

    with (
        patch("vtt.diarization.Pipeline.from_pretrained", return_value=mock_pipeline),
        pytest.raises(ValueError, match="Audio file is too short for diarization"),
    ):
        diarizer.diarize_audio(Path("/fake/short.mp3"))


def test_diarize_audio_other_error_is_reraised() -> None:
    """Test that non-short-audio errors are re-raised as-is."""
    from vtt.diarization import SpeakerDiarizer

    diarizer = SpeakerDiarizer(hf_token="test_token")  # noqa: S106

    # Mock the pipeline to raise a different error
    mock_pipeline = MagicMock()
    mock_pipeline.side_effect = RuntimeError("Some other error")

    with (
        patch("vtt.diarization.Pipeline.from_pretrained", return_value=mock_pipeline),
        pytest.raises(RuntimeError, match="Some other error"),
    ):
        diarizer.diarize_audio(Path("/fake/audio.mp3"))


# Integration tests - use real pyannote models with HF_TOKEN from .env
# NOTE: Requires accepting terms for these models on HuggingFace:
#   - https://huggingface.co/pyannote/segmentation-3.0
#   - https://huggingface.co/pyannote/speaker-diarization-3.1
@pytest.mark.integration
def test_diarize_audio_integration() -> None:
    """Integration test: Run real diarization on test audio file."""
    from vtt.diarization import SpeakerDiarizer

    # Explicitly get HF_TOKEN to avoid env issues during test runs
    hf_token = os.environ.get("HF_TOKEN")
    if not hf_token:
        pytest.skip("HF_TOKEN not available in environment")

    test_audio = Path(__file__).parent / "hello_conversation.mp3"
    assert test_audio.exists(), f"Test audio file not found: {test_audio}"

    try:
        diarizer = SpeakerDiarizer(hf_token=hf_token)
        segments = diarizer.diarize_audio(test_audio)
    except Exception as e:
        if "GatedRepo" in str(type(e).__name__):
            pytest.skip(f"Gated model access required. Visit HuggingFace to accept terms. Error: {e}")
        raise

    # Should detect at least 2 speakers
    assert len(segments) >= 2, f"Expected at least 2 segments, got {len(segments)}"

    # Should have SPEAKER_00 and SPEAKER_01
    speakers = {seg[2] for seg in segments}
    assert "SPEAKER_00" in speakers
    assert "SPEAKER_01" in speakers

    # Each segment should be a tuple of (start, end, speaker_label)
    for seg in segments:
        assert len(seg) == 3
        start, end, speaker = seg
        assert isinstance(start, float)
        assert isinstance(end, float)
        assert isinstance(speaker, str)
        assert end > start
        assert speaker.startswith("SPEAKER_")


@pytest.mark.integration
def test_apply_speakers_to_transcript_integration() -> None:
    """Integration test: Apply real diarization to transcript."""
    from vtt.diarization import SpeakerDiarizer

    test_audio = Path(__file__).parent / "hello_conversation.mp3"
    hf_token = os.environ.get("HF_TOKEN")
    if not hf_token:
        pytest.skip("HF_TOKEN not available in environment")

    assert test_audio.exists(), f"Test audio file not found: {test_audio}"

    try:
        diarizer = SpeakerDiarizer(hf_token=hf_token)
        segments = diarizer.diarize_audio(test_audio)
    except Exception as e:
        if "GatedRepo" in str(type(e).__name__):
            pytest.skip("Gated model access required. Visit HuggingFace to accept terms.")
        raise

    # Create a mock transcript covering the audio duration
    transcript = "[00:00 - 00:01] Hello world\n[00:01 - 00:02] Hello earth"

    result = diarizer.apply_speakers_to_transcript(transcript, segments)

    # Should have speaker labels added
    assert "SPEAKER" in result
    # Original text should still be present
    assert "Hello world" in result
    assert "Hello earth" in result


@pytest.mark.integration
def test_format_diarization_output_integration() -> None:
    """Integration test: Format real diarization output."""
    from vtt.diarization import SpeakerDiarizer, format_diarization_output

    test_audio = Path(__file__).parent / "hello_conversation.mp3"
    assert test_audio.exists(), f"Test audio file not found: {test_audio}"

    hf_token = os.environ.get("HF_TOKEN")
    if not hf_token:
        pytest.skip("HF_TOKEN not available in environment")

    try:
        diarizer = SpeakerDiarizer()
        segments = diarizer.diarize_audio(test_audio)
    except Exception as e:
        if "GatedRepo" in str(type(e).__name__):
            pytest.skip("Gated model access required. Visit HuggingFace to accept terms.")
        raise

    result = format_diarization_output(segments)

    # Should have timestamp format
    assert "[" in result
    assert "]" in result
    # Should have speaker labels
    assert "SPEAKER" in result


def test_get_unique_speakers_from_segments() -> None:
    """Test extracting unique speaker labels from segments."""
    from vtt.diarization import get_unique_speakers  # type: ignore[attr-defined]

    segments = [
        (0.0, 5.0, "SPEAKER_00"),
        (5.0, 10.0, "SPEAKER_01"),
        (10.0, 15.0, "SPEAKER_00"),
        (15.0, 20.0, "SPEAKER_02"),
        (20.0, 25.0, "SPEAKER_01"),
    ]

    speakers = get_unique_speakers(segments)

    # Should return speakers in order of first appearance
    assert speakers == ["SPEAKER_00", "SPEAKER_01", "SPEAKER_02"]
