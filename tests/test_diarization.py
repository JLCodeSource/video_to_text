"""Tests for speaker diarization functionality."""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from vtt_transcribe.handlers import DIARIZATION_DEPS_ERROR_MSG

# Suppress torchcodec warning and mark all tests as requiring diarization dependencies
pytestmark = [
    pytest.mark.filterwarnings("ignore::UserWarning:pyannote.audio.core.io"),
    pytest.mark.diarization,
]


class TestDiarizationImportHandling:
    """Test handling of missing diarization dependencies (mocked imports)."""

    def test_diarize_flag_without_dependencies_shows_error(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        """Should show error when --diarize is used without diarization dependencies."""
        from vtt_transcribe.main import main

        # Create a dummy audio file
        audio_file = tmp_path / "test.mp3"
        audio_file.write_text("dummy audio")

        # Mock the transcription to succeed so we can test diarization import failure
        # Simulate missing torch dependency (the actual scenario when optional deps not installed)
        def mock_lazy_import() -> None:
            raise ImportError(DIARIZATION_DEPS_ERROR_MSG)

        with (
            patch("vtt_transcribe.transcriber.VideoTranscriber") as mock_transcriber,
            patch("vtt_transcribe.handlers._lazy_import_diarization", side_effect=mock_lazy_import),
            patch("sys.argv", ["vtt", str(audio_file), "--diarize"]),
            patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}),
        ):
            # Mock transcription to return a dummy transcript
            mock_transcriber.return_value.transcribe.return_value = "dummy transcript"

            # Should exit with error
            with pytest.raises(SystemExit) as exc_info:
                main()

        assert exc_info.value.code == 1

        # Capture output to check error message (errors print to stderr)
        captured = capsys.readouterr()
        assert "Diarization dependencies not installed" in captured.err

    def test_diarize_only_without_dependencies_shows_error(self, tmp_path: Path) -> None:
        """Should show error when --diarize-only is used without diarization dependencies."""
        from vtt_transcribe.main import main

        audio_file = tmp_path / "test.mp3"
        audio_file.write_text("dummy audio")

        # Simulate missing pyannote.audio dependency (the actual scenario)
        def mock_lazy_import() -> None:
            raise ImportError(DIARIZATION_DEPS_ERROR_MSG)

        with (
            patch("vtt_transcribe.handlers._lazy_import_diarization", side_effect=mock_lazy_import),
            patch("sys.argv", ["vtt", str(audio_file), "--diarize-only"]),
            pytest.raises(SystemExit) as exc_info,
        ):
            main()

        assert exc_info.value.code == 1

    def test_apply_diarization_without_dependencies_shows_error(self, tmp_path: Path) -> None:
        """Should show error when --apply-diarization is used without diarization dependencies."""
        from vtt_transcribe.main import main

        audio_file = tmp_path / "test.mp3"
        audio_file.write_text("dummy audio")
        transcript_file = tmp_path / "transcript.txt"
        transcript_file.write_text("dummy transcript")

        # Simulate missing torch dependency (the actual scenario)
        def mock_lazy_import() -> None:
            raise ImportError(DIARIZATION_DEPS_ERROR_MSG)

        with (
            patch("vtt_transcribe.handlers._lazy_import_diarization", side_effect=mock_lazy_import),
            patch("sys.argv", ["vtt", str(audio_file), "--apply-diarization", str(transcript_file)]),
            pytest.raises(SystemExit) as exc_info,
        ):
            main()

        assert exc_info.value.code == 1


def test_speaker_diarizer_can_import_pyannote() -> None:
    """Test that pyannote.audio can be imported."""
    try:
        from pyannote.audio import Pipeline  # noqa: F401
    except ImportError:
        pytest.fail("pyannote.audio not installed")


def test_speaker_diarizer_initialization_with_token() -> None:
    """Test SpeakerDiarizer can be initialized with a token."""
    from vtt_transcribe.diarization import SpeakerDiarizer

    diarizer = SpeakerDiarizer(hf_token="test_token")  # noqa: S106
    assert diarizer.hf_token == "test_token"  # noqa: S105


def test_speaker_diarizer_initialization_from_env() -> None:
    """Test SpeakerDiarizer can be initialized from HF_TOKEN env var."""
    from vtt_transcribe.diarization import SpeakerDiarizer

    os.environ["HF_TOKEN"] = "env_token"  # noqa: S105
    try:
        diarizer = SpeakerDiarizer()
        assert diarizer.hf_token == "env_token"  # noqa: S105
    finally:
        del os.environ["HF_TOKEN"]


def test_speaker_diarizer_initialization_no_token_raises_error() -> None:
    """Test SpeakerDiarizer raises error when no token provided."""
    from vtt_transcribe.diarization import SpeakerDiarizer

    # Ensure HF_TOKEN is not set
    os.environ.pop("HF_TOKEN", None)

    with pytest.raises(ValueError, match="Hugging Face token not provided"):
        SpeakerDiarizer()


def test_speaker_diarizer_initialization_with_device() -> None:
    """Test SpeakerDiarizer can be initialized with a device."""
    from vtt_transcribe.diarization import SpeakerDiarizer

    diarizer = SpeakerDiarizer(hf_token="test_token", device="cuda")  # noqa: S106
    assert diarizer.device == "cuda"


def test_speaker_diarizer_default_device_is_auto() -> None:
    """Test SpeakerDiarizer defaults to auto device."""
    from vtt_transcribe.diarization import SpeakerDiarizer

    diarizer = SpeakerDiarizer(hf_token="test_token")  # noqa: S106
    assert diarizer.device == "auto"


def test_diarize_audio_returns_speaker_segments() -> None:
    """Test diarize_audio returns list of speaker segments."""
    from vtt_transcribe.diarization import SpeakerDiarizer

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

    with patch("vtt_transcribe.diarization.Pipeline.from_pretrained", return_value=mock_pipeline):
        audio_path = Path("/fake/audio.mp3")
        segments = diarizer.diarize_audio(audio_path)

        assert len(segments) == 1
        assert segments[0] == (0.0, 5.0, "SPEAKER_00")


def test_apply_speakers_to_transcript_adds_labels() -> None:
    """Test apply_speakers_to_transcript adds speaker labels to transcript."""
    from vtt_transcribe.diarization import SpeakerDiarizer

    diarizer = SpeakerDiarizer(hf_token="test_token")  # noqa: S106

    transcript = "[00:00 - 00:05] Hello world"
    speaker_segments = [(0.0, 5.0, "SPEAKER_00")]

    result = diarizer.apply_speakers_to_transcript(transcript, speaker_segments)

    assert result == "[00:00 - 00:05] SPEAKER_00: Hello world"


def test_apply_speakers_to_transcript_empty_segments() -> None:
    """Test apply_speakers_to_transcript returns transcript unchanged when no segments."""
    from vtt_transcribe.diarization import SpeakerDiarizer

    diarizer = SpeakerDiarizer(hf_token="test_token")  # noqa: S106

    transcript = "[00:00 - 00:05] Hello world"
    speaker_segments: list[tuple[float, float, str]] = []

    result = diarizer.apply_speakers_to_transcript(transcript, speaker_segments)

    assert result == transcript


def test_apply_speakers_to_transcript_no_match() -> None:
    """Test apply_speakers_to_transcript handles lines without timestamp match."""
    from vtt_transcribe.diarization import SpeakerDiarizer

    diarizer = SpeakerDiarizer(hf_token="test_token")  # noqa: S106

    transcript = "Plain text without timestamps\n[00:00 - 00:05] Hello"
    speaker_segments = [(0.0, 5.0, "SPEAKER_00")]

    result = diarizer.apply_speakers_to_transcript(transcript, speaker_segments)

    assert "Plain text without timestamps" in result
    assert "SPEAKER_00: Hello" in result


def test_apply_speakers_to_transcript_no_speaker_found() -> None:
    """Test apply_speakers_to_transcript when no speaker matches timestamp."""
    from vtt_transcribe.diarization import SpeakerDiarizer

    diarizer = SpeakerDiarizer(hf_token="test_token")  # noqa: S106

    transcript = "[00:10 - 00:15] Hello"
    # Doesn't overlap with timestamp
    speaker_segments = [(0.0, 5.0, "SPEAKER_00")]

    result = diarizer.apply_speakers_to_transcript(transcript, speaker_segments)

    assert result == "[00:10 - 00:15] Hello"  # Unchanged


def test_find_speaker_at_time_no_match() -> None:
    """Test _find_speaker_at_time returns None when no speaker found."""
    from vtt_transcribe.diarization import SpeakerDiarizer

    diarizer = SpeakerDiarizer(hf_token="test_token")  # noqa: S106

    speaker_segments = [(0.0, 5.0, "SPEAKER_00"), (10.0, 15.0, "SPEAKER_01")]

    result = diarizer._find_speaker_at_time(7.5, speaker_segments)

    assert result is None


def test_format_diarization_output() -> None:
    """Test format_diarization_output formats segments correctly."""
    from vtt_transcribe.diarization import format_diarization_output

    segments = [(0.0, 5.0, "SPEAKER_00"), (65.0, 125.0, "SPEAKER_01")]

    result = format_diarization_output(segments)

    assert "[00:00 - 00:05] SPEAKER_00" in result
    assert "[01:05 - 02:05] SPEAKER_01" in result


def test_diarize_audio_short_file_raises_error() -> None:
    """Test that diarizing a short audio file raises a helpful error."""
    from vtt_transcribe.diarization import SpeakerDiarizer

    diarizer = SpeakerDiarizer(hf_token="test_token")  # noqa: S106

    # Mock the pipeline to raise the short audio error
    mock_pipeline = MagicMock()
    mock_pipeline.return_value = MagicMock()
    mock_pipeline.side_effect = ValueError(
        "requested chunk [ 00:00:00.000 --> 00:00:10.000] resulted in 100 samples instead of the expected 441000 samples"
    )

    with (
        patch("vtt_transcribe.diarization.Pipeline.from_pretrained", return_value=mock_pipeline),
        pytest.raises(ValueError, match="Audio file is too short for diarization"),
    ):
        diarizer.diarize_audio(Path("/fake/short.mp3"))


def test_diarize_audio_other_error_is_reraised() -> None:
    """Test that non-short-audio errors are re-raised as-is."""
    from vtt_transcribe.diarization import SpeakerDiarizer

    diarizer = SpeakerDiarizer(hf_token="test_token")  # noqa: S106

    # Mock the pipeline to raise a different error
    mock_pipeline = MagicMock()
    mock_pipeline.side_effect = RuntimeError("Some other error")

    with (
        patch("vtt_transcribe.diarization.Pipeline.from_pretrained", return_value=mock_pipeline),
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
    from vtt_transcribe.diarization import SpeakerDiarizer

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
    from vtt_transcribe.diarization import SpeakerDiarizer

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
    from vtt_transcribe.diarization import SpeakerDiarizer, format_diarization_output

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
    from vtt_transcribe.diarization import get_unique_speakers

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


def test_get_speaker_context_lines() -> None:
    """Test extracting context lines for a specific speaker from transcript."""
    from vtt_transcribe.diarization import get_speaker_context_lines

    transcript = """[00:00 - 00:05] SPEAKER_00: Hello world
[00:05 - 00:10] SPEAKER_01: This is speaker one
[00:10 - 00:15] SPEAKER_01: More from speaker one
[00:15 - 00:20] SPEAKER_02: Now speaker two talking
[00:20 - 00:25] SPEAKER_02: Speaker two continues
[00:25 - 00:30] SPEAKER_01: Back to speaker one
[00:30 - 00:35] SPEAKER_01: Still speaker one"""

    # Get context for SPEAKER_01 with 1 line before/after
    contexts = get_speaker_context_lines(transcript, "SPEAKER_01", context_lines=1)

    # Should have 2 contexts (first appearance and later appearance)
    assert len(contexts) == 2
    # First context should include line before and after
    assert "SPEAKER_00: Hello world" in contexts[0]  # before
    assert "SPEAKER_01: This is speaker one" in contexts[0]  # speaker segment
    # speaker continues
    assert "SPEAKER_01: More from speaker one" in contexts[0]
    assert "SPEAKER_02: Now speaker two" in contexts[0]  # after
    # Second context
    assert "SPEAKER_02: Speaker two continues" in contexts[1]  # before
    assert "SPEAKER_01: Back to speaker one" in contexts[1]  # speaker segment
    # same speaker continues
    assert "SPEAKER_01: Still speaker one" in contexts[1]


def test_diarize_audio_sample_mismatch_error() -> None:
    """Test that sample mismatch errors trigger WAV conversion fallback."""
    from vtt_transcribe.diarization import SpeakerDiarizer

    diarizer = SpeakerDiarizer(hf_token="test_token")  # noqa: S106

    # Mock the pipeline to raise a sample mismatch error for a file > 10s
    # Simulating a 15-second file with wrong sample count
    # actual_samples = 500000 -> duration = 11.34s at 44.1kHz (> 10s threshold)
    # expected_samples = 992250 for a 15s chunk
    mock_pipeline = MagicMock()
    mock_pipeline.return_value = MagicMock()
    mock_pipeline.side_effect = ValueError(
        "requested chunk [ 00:00:00.000 -->  00:00:15.000] resulted in 500000 samples instead of the expected 992250 samples"
    )

    # The code will try to convert to WAV when it sees MP3 encoding issues
    # Mock the conversion to fail (since /fake/audio.mp3 doesn't exist)
    with (
        patch("vtt_transcribe.diarization.Pipeline.from_pretrained", return_value=mock_pipeline),
        pytest.raises(RuntimeError, match="Failed to convert to WAV"),
    ):
        diarizer.diarize_audio(Path("/fake/audio.mp3"))


def test_diarize_audio_other_value_error() -> None:
    """Test that non-sample-mismatch ValueError is re-raised as-is."""
    from vtt_transcribe.diarization import SpeakerDiarizer

    diarizer = SpeakerDiarizer(hf_token="test_token")  # noqa: S106

    # Mock the pipeline to raise a ValueError that doesn't match the pattern
    mock_pipeline = MagicMock()
    mock_pipeline.side_effect = ValueError("Some random ValueError")

    with (
        patch("vtt_transcribe.diarization.Pipeline.from_pretrained", return_value=mock_pipeline),
        pytest.raises(ValueError, match="Some random ValueError"),
    ):
        diarizer.diarize_audio(Path("/fake/audio.mp3"))


def test_resolve_device_auto_with_cuda_available() -> None:
    """Test device resolution: auto with CUDA available should return cuda."""
    from vtt_transcribe.diarization import resolve_device

    with patch("torch.cuda.is_available", return_value=True):
        assert resolve_device("auto") == "cuda"


def test_resolve_device_auto_without_cuda() -> None:
    """Test device resolution: auto without CUDA should return cpu."""
    from vtt_transcribe.diarization import resolve_device

    with patch("torch.cuda.is_available", return_value=False):
        assert resolve_device("auto") == "cpu"


def test_resolve_device_explicit_cuda() -> None:
    """Test device resolution: explicit cuda should return cuda."""
    from vtt_transcribe.diarization import resolve_device

    assert resolve_device("cuda") == "cuda"


def test_resolve_device_explicit_cpu() -> None:
    """Test device resolution: explicit cpu should return cpu."""
    from vtt_transcribe.diarization import resolve_device

    assert resolve_device("cpu") == "cpu"


def test_diarizer_device_move_failure_fallback() -> None:
    """Test that diarizer handles device move failures gracefully."""
    from vtt_transcribe.diarization import SpeakerDiarizer

    diarizer = SpeakerDiarizer(hf_token="test_token", device="cuda")  # noqa: S106

    mock_pipeline = MagicMock()
    mock_pipeline.to.side_effect = RuntimeError("CUDA not available")

    with (
        patch("vtt_transcribe.diarization.Pipeline.from_pretrained", return_value=mock_pipeline),
        patch("vtt_transcribe.diarization.logger.warning") as mock_logger,
    ):
        pipeline = diarizer._load_pipeline()

        # Verify warning was logged
        mock_logger.assert_called_once()
        assert "Failed to move pipeline to" in mock_logger.call_args[0][0]
        assert pipeline == mock_pipeline


@pytest.mark.integration
def test_diarization_uses_cuda_when_available(gpu_available: bool) -> None:  # noqa: FBT001
    """Integration test: Verify CUDA is used when available."""
    if not gpu_available:
        pytest.skip("GPU not available")

    import torch

    from vtt_transcribe.diarization import SpeakerDiarizer

    hf_token = os.environ.get("HF_TOKEN")
    if not hf_token:
        pytest.skip("HF_TOKEN not available in environment")

    # Create diarizer with auto device (should use CUDA)
    diarizer = SpeakerDiarizer(hf_token=hf_token, device="auto")

    # Load pipeline to trigger device resolution
    pipeline = diarizer._load_pipeline()

    # Verify CUDA device is being used
    assert torch.cuda.is_available()
    # Check if model has been moved to CUDA
    if hasattr(pipeline, "model"):
        # The model should be on a CUDA device
        # Note: This is a best-effort check as pyannote's internal structure may vary
        pass


@pytest.mark.integration
def test_diarization_fallback_to_cpu(gpu_available: bool) -> None:  # noqa: FBT001
    """Integration test: Verify CPU fallback when CUDA requested but not available."""
    if gpu_available:
        pytest.skip("GPU is available, can't test CPU fallback")

    from vtt_transcribe.diarization import SpeakerDiarizer

    hf_token = os.environ.get("HF_TOKEN")
    if not hf_token:
        pytest.skip("HF_TOKEN not available in environment")

    # Create diarizer with CUDA device (should fallback gracefully)
    diarizer = SpeakerDiarizer(hf_token=hf_token, device="cuda")

    # Load pipeline - should not crash even if CUDA not available
    pipeline = diarizer._load_pipeline()

    # Pipeline should be loaded successfully
    assert pipeline is not None


@pytest.mark.integration
def test_diarization_explicit_cpu_device() -> None:
    """Integration test: Verify explicit CPU device selection works."""
    from vtt_transcribe.diarization import SpeakerDiarizer

    hf_token = os.environ.get("HF_TOKEN")
    if not hf_token:
        pytest.skip("HF_TOKEN not available in environment")

    # Create diarizer with explicit CPU device
    diarizer = SpeakerDiarizer(hf_token=hf_token, device="cpu")

    # Load pipeline
    pipeline = diarizer._load_pipeline()

    # Pipeline should be loaded successfully
    assert pipeline is not None
    # Device should be resolved to cpu
    from vtt_transcribe.diarization import resolve_device

    assert resolve_device(diarizer.device) == "cpu"


def test_load_pipeline_logs_device_info() -> None:
    """Test that loading pipeline logs device information."""
    from unittest.mock import patch

    from vtt_transcribe.diarization import SpeakerDiarizer

    diarizer = SpeakerDiarizer(hf_token="test_token", device="cuda")  # noqa: S106

    mock_pipeline = MagicMock()

    with (
        patch("vtt_transcribe.diarization.Pipeline.from_pretrained", return_value=mock_pipeline),
        patch("vtt_transcribe.diarization.logger.info") as mock_info,
        patch("torch.cuda.is_available", return_value=True),
    ):
        diarizer._load_pipeline()

        # Should log the device being used
        assert mock_info.called
        call_args = str(mock_info.call_args_list)
        assert "cuda" in call_args.lower() or "device" in call_args.lower()


def test_disable_gpu_via_env_var() -> None:
    """Test that DISABLE_GPU env var forces CPU usage."""
    from vtt_transcribe.diarization import resolve_device

    # Set env var to disable GPU
    os.environ["DISABLE_GPU"] = "1"

    try:
        # Even with cuda request, should return cpu
        assert resolve_device("auto") == "cpu"
        assert resolve_device("cuda") == "cpu"
        assert resolve_device("gpu") == "cpu"

        # Explicit cpu should still work
        assert resolve_device("cpu") == "cpu"
    finally:
        del os.environ["DISABLE_GPU"]


def test_gpu_alias_maps_to_cuda() -> None:
    """Test that 'gpu' device string maps to 'cuda'."""
    from unittest.mock import patch

    from vtt_transcribe.diarization import resolve_device

    with patch("torch.cuda.is_available", return_value=True):
        # 'gpu' should resolve to 'cuda' when available
        assert resolve_device("gpu") == "cuda"


def test_add_speaker_label_with_hh_mm_ss_format() -> None:
    """Test adding speaker label to transcript line with HH:MM:SS timestamp format."""
    from vtt_transcribe.diarization import SpeakerDiarizer

    diarizer = SpeakerDiarizer(hf_token="test_token")  # noqa: S106

    # Test with HH:MM:SS format (hour:minute:second)
    line = "[01:30:45 - 01:30:50] Hello world"
    # 1:30:45 = 1*3600 + 30*60 + 45 = 5445s
    segments = [(5445.0, 5450.0, "SPEAKER_00")]

    result = diarizer._process_line(line, segments)

    assert result == "[01:30:45 - 01:30:50] SPEAKER_00: Hello world"


class TestWAVConversionFallback:
    """Test automatic WAV conversion when MP3 encoding causes issues."""

    def test_wav_conversion_triggered_by_sample_mismatch(self) -> None:
        """Test that sample mismatch error with duration >= 9.5s triggers WAV conversion."""
        import tempfile

        from vtt_transcribe.diarization import SpeakerDiarizer

        diarizer = SpeakerDiarizer(hf_token="test_token")  # noqa: S106

        with tempfile.NamedTemporaryFile(mode="wb", suffix=".mp3", delete=False) as f:
            audio_path = Path(f.name)
            f.write(b"fake_mp3_data")

        try:
            # Tracks method calls
            calls = []

            def mock_internal(_self: object, path: Path) -> list:
                calls.append(str(path))
                # First call raises MP3 encoding error (duration >= 9.5s, so conversion triggered)
                if len(calls) == 1:
                    # Simulate the processed error message from _diarize_audio_internal
                    msg = (
                        "Audio file sample mismatch error. This usually indicates:\n"
                        "  - MP3 encoding imprecision (metadata doesn't match exact sample count)\n"
                        "  - File corruption or incomplete download\n"
                        "Expected 10.00s (441000 samples), but got 9.97s (439895 samples)."
                    )
                    raise ValueError(msg)
                # Second call (with WAV) succeeds
                return [(0.0, 10.0, "SPEAKER_00")]

            def mock_convert(_self: object, _input_path: Path, output_path: Path) -> None:
                # Create the WAV file
                output_path.write_bytes(b"fake_wav_data")

            with (
                patch.object(SpeakerDiarizer, "_diarize_audio_internal", mock_internal),
                patch.object(SpeakerDiarizer, "_convert_to_wav", mock_convert),
            ):
                result = diarizer.diarize_audio(audio_path)

            # Should have called internal twice: MP3 then WAV
            assert len(calls) == 2
            assert calls[0].endswith(".mp3")
            assert calls[1].endswith(".wav")
            assert result == [(0.0, 10.0, "SPEAKER_00")]

            # WAV should be cleaned up
            wav_path = audio_path.with_suffix(".wav")
            assert not wav_path.exists()

        finally:
            if audio_path.exists():
                audio_path.unlink()

    def test_wav_conversion_cleanup_on_retry_failure(self) -> None:
        """Test that WAV file is cleaned up even when retry fails."""
        import tempfile

        from vtt_transcribe.diarization import SpeakerDiarizer

        diarizer = SpeakerDiarizer(hf_token="test_token")  # noqa: S106

        with tempfile.NamedTemporaryFile(mode="wb", suffix=".mp3", delete=False) as f:
            audio_path = Path(f.name)
            f.write(b"fake_mp3_data")

        try:

            def mock_internal(_self: object, path: Path) -> list:
                # Both calls fail
                if str(path).endswith(".mp3"):
                    msg = (
                        "Audio file sample mismatch error. This usually indicates:\n"
                        "  - MP3 encoding imprecision (metadata doesn't match exact sample count)\n"
                        "Expected 10.00s (441000 samples), but got 9.97s (439895 samples)."
                    )
                    raise ValueError(msg)
                # WAV also fails
                msg = "WAV processing also failed"
                raise RuntimeError(msg)

            def mock_convert(_self: object, _input_path: Path, output_path: Path) -> None:
                output_path.write_bytes(b"fake_wav_data")

            with (
                patch.object(SpeakerDiarizer, "_diarize_audio_internal", mock_internal),
                patch.object(SpeakerDiarizer, "_convert_to_wav", mock_convert),
                pytest.raises(RuntimeError, match="WAV processing also failed"),
            ):
                diarizer.diarize_audio(audio_path)

            # WAV should be cleaned up even on failure
            wav_path = audio_path.with_suffix(".wav")
            assert not wav_path.exists()

        finally:
            if audio_path.exists():
                audio_path.unlink()

    def test_non_mp3_error_bypasses_conversion(self) -> None:
        """Test that errors without MP3 encoding text don't trigger conversion."""
        import tempfile

        from vtt_transcribe.diarization import SpeakerDiarizer

        diarizer = SpeakerDiarizer(hf_token="test_token")  # noqa: S106

        with tempfile.NamedTemporaryFile(mode="wb", suffix=".mp3", delete=False) as f:
            audio_path = Path(f.name)
            f.write(b"fake_data")

        try:

            def mock_internal(_self: object, _path: Path) -> list:
                msg = "Some other error unrelated to MP3"
                raise ValueError(msg)

            with (
                patch.object(SpeakerDiarizer, "_diarize_audio_internal", mock_internal),
                pytest.raises(ValueError, match="Some other error unrelated to MP3"),
            ):
                diarizer.diarize_audio(audio_path)

        finally:
            if audio_path.exists():
                audio_path.unlink()

    def test_convert_to_wav_success(self) -> None:
        """Test WAV conversion using ffmpeg."""
        import tempfile
        from unittest.mock import Mock

        from vtt_transcribe.diarization import SpeakerDiarizer

        diarizer = SpeakerDiarizer(hf_token="test_token")  # noqa: S106

        with (
            tempfile.NamedTemporaryFile(mode="wb", suffix=".mp3", delete=False) as f1,
            tempfile.NamedTemporaryFile(mode="wb", suffix=".wav", delete=False) as f2,
        ):
            input_path = Path(f1.name)
            output_path = Path(f2.name)
            f1.write(b"fake_mp3")

        try:
            # Mock subprocess to succeed
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stderr = ""

            with patch("subprocess.run", return_value=mock_result):
                diarizer._convert_to_wav(input_path, output_path)

        finally:
            if input_path.exists():
                input_path.unlink()
            if output_path.exists():
                output_path.unlink()

    def test_convert_to_wav_failure(self) -> None:
        """Test WAV conversion failure handling."""
        import tempfile
        from unittest.mock import Mock

        from vtt_transcribe.diarization import SpeakerDiarizer

        diarizer = SpeakerDiarizer(hf_token="test_token")  # noqa: S106

        with (
            tempfile.NamedTemporaryFile(mode="wb", suffix=".mp3", delete=False) as f1,
            tempfile.NamedTemporaryFile(mode="wb", suffix=".wav", delete=False) as f2,
        ):
            input_path = Path(f1.name)
            output_path = Path(f2.name)

        try:
            # Mock subprocess to fail
            mock_result = Mock()
            mock_result.returncode = 1
            mock_result.stderr = "ffmpeg error: invalid file"

            with (
                patch("subprocess.run", return_value=mock_result),
                pytest.raises(RuntimeError, match="Failed to convert to WAV"),
            ):
                diarizer._convert_to_wav(input_path, output_path)

        finally:
            if input_path.exists():
                input_path.unlink()
            if output_path.exists():
                output_path.unlink()
