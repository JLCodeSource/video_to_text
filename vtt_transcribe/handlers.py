"""Handler functions for different transcription and diarization workflows."""

import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from vtt_transcribe.diarization import SpeakerDiarizer, format_diarization_output  # noqa: F401


AUDIO_EXTENSION = ".mp3"
TRANSCRIPT_EXTENSION = ".txt"


def save_transcript(output_path: Path, transcript: str) -> None:
    """Save transcript to a file, ensuring .txt extension."""
    # Ensure output path has .txt extension
    if output_path.suffix.lower() != ".txt":
        output_path = output_path.with_suffix(TRANSCRIPT_EXTENSION)
    output_path.write_text(transcript)
    print(f"\nTranscript saved to: {output_path}")


def display_result(transcript: str) -> None:
    """Display transcription result."""
    print("\n" + "=" * 50)
    print("Transcription Result:")
    print("=" * 50)
    print(transcript)


def handle_diarize_only_mode(input_path: Path, hf_token: str | None, save_path: Path | None, device: str = "auto") -> str:
    """Handle --diarize-only mode: run diarization without transcription.

    Returns:
        The formatted diarization output transcript.
    """
    if not input_path.exists():
        msg = f"Audio file not found: {input_path}"
        raise FileNotFoundError(msg)

    SpeakerDiarizer, format_diarization_output, _, _ = _lazy_import_diarization()  # noqa: N806
    print(f"Running speaker diarization on: {input_path}")
    print(f"Using device: {device}")

    # Show GPU info if using CUDA
    torch_imported = False
    if device in ("cuda", "auto"):
        import torch

        torch_imported = True
        if torch.cuda.is_available():
            print(f"GPU: {torch.cuda.get_device_name(0)}")
            print(f"GPU memory before: {torch.cuda.memory_allocated(0) / 1024**2:.2f} MB")

    diarizer = SpeakerDiarizer(hf_token=hf_token, device=device)
    segments = diarizer.diarize_audio(input_path)

    # Show GPU memory after if using CUDA
    if torch_imported and device in ("cuda", "auto") and torch.cuda.is_available():
        print(f"GPU memory after: {torch.cuda.memory_allocated(0) / 1024**2:.2f} MB")

    result = format_diarization_output(segments)
    display_result(result)

    if save_path:
        save_transcript(save_path, result)

    return result


def handle_apply_diarization_mode(
    input_path: Path, transcript_path: Path, hf_token: str | None, save_path: Path | None, device: str = "auto"
) -> str:
    """Handle --apply-diarization mode: apply diarization to existing transcript.

    Returns:
        The transcript with speaker labels applied.
    """
    if not transcript_path.exists():
        msg = f"Transcript file not found: {transcript_path}"
        raise FileNotFoundError(msg)

    if not input_path.exists():
        msg = f"Audio file not found: {input_path}"
        raise FileNotFoundError(msg)

    # Load transcript
    transcript = transcript_path.read_text()

    # Run diarization
    SpeakerDiarizer, _, _, _ = _lazy_import_diarization()  # noqa: N806
    diarizer = SpeakerDiarizer(hf_token=hf_token, device=device)
    print(f"Running speaker diarization on: {input_path}")
    segments = diarizer.diarize_audio(input_path)

    # Apply speakers to transcript
    print("Applying speaker labels to transcript...")
    result = diarizer.apply_speakers_to_transcript(transcript, segments)
    display_result(result)

    if save_path:
        save_transcript(save_path, result)

    return result


def _load_transcript_from_input(input_path: Path, hf_token: str | None, device: str) -> str:
    """Load or generate transcript from input path."""
    is_transcript = input_path.suffix.lower() in [".txt", ".srt", ".vtt"]

    if is_transcript:
        print(f"Loading transcript from: {input_path}")
        return input_path.read_text()

    # Run diarization on audio file
    SpeakerDiarizer, format_diarization_output, _, _ = _lazy_import_diarization()  # noqa: N806
    diarizer = SpeakerDiarizer(hf_token=hf_token, device=device)
    print(f"Running speaker diarization on: {input_path}")
    segments = diarizer.diarize_audio(input_path)
    return format_diarization_output(segments)


def _extract_speakers_from_transcript(transcript: str) -> list[str]:
    """Extract unique speaker labels from transcript in order of appearance."""
    speakers = []
    seen = set()
    for line in transcript.split("\n"):
        # Match pattern: [HH:MM:SS - HH:MM:SS] or [MM:SS - MM:SS] SPEAKER_XX: text (with colon)
        # or [HH:MM:SS - HH:MM:SS] / [MM:SS - MM:SS] SPEAKER_XX (without colon, from diarization-only output)
        match = re.match(r"\[(?:\d{2}:)?\d{2}:\d{2} - (?:\d{2}:)?\d{2}:\d{2}\]\s+(SPEAKER_\d+):?", line)
        if match:
            speaker = match.group(1)
            if speaker not in seen:
                seen.add(speaker)
                speakers.append(speaker)
    return speakers


def _review_speaker_interactively(speaker: str, transcript: str, get_speaker_context_lines: Any) -> tuple[str, str | None]:
    """Review a single speaker and prompt for renaming.

    Returns:
        Tuple of (updated_transcript, new_name_or_none)
    """
    contexts = get_speaker_context_lines(transcript, speaker, context_lines=5)

    print(f"\n{'=' * 50}")
    print(f"Speaker: {speaker}")
    print(f"{'=' * 50}")
    speaker_count = transcript.count(speaker)
    print(f"Number of occurrences: {speaker_count}")
    print("\nContext (showing first occurrence):")
    if contexts:
        print(contexts[0])

    new_name = input(f"\nEnter name for {speaker} (or press Enter to keep): ").strip()
    if new_name:
        transcript = transcript.replace(speaker, new_name)
        print(f"Renamed {speaker} -> {new_name}")
        return transcript, new_name

    return transcript, None


def handle_review_speakers(
    input_path: Path | None = None,
    hf_token: str | None = None,
    save_path: Path | None = None,
    device: str = "auto",
    transcript: str | None = None,
) -> str:
    """Handle interactive speaker review and renaming for diarization workflows.

    This function implements the review step that runs automatically in
    diarization modes, unless disabled with ``--no-review-speakers``. It is
    used internally and is not exposed as a direct CLI flag.

    Args:
        input_path: Path to audio/transcript file (required if transcript is None).
        hf_token: Hugging Face token for pyannote models (required if running diarization).
        save_path: Optional path to save final transcript.
        device: Device to use for diarization (auto/cuda/cpu).
        transcript: Pre-computed transcript string. If provided, skips diarization step.

    Returns:
        Final transcript with speaker labels applied.
    """
    _, _, _get_unique_speakers, get_speaker_context_lines = _lazy_import_diarization()

    # Determine final transcript source
    if transcript is not None:
        final_transcript = transcript
    elif input_path is None:
        msg = "Either input_path or transcript must be provided"
        raise ValueError(msg)
    elif not input_path.exists():
        msg = f"Input file not found: {input_path}"
        raise FileNotFoundError(msg)
    else:
        final_transcript = _load_transcript_from_input(input_path, hf_token, device)

    # Extract and review speakers
    speakers = _extract_speakers_from_transcript(final_transcript)
    print(f"\nFound {len(speakers)} speakers: {', '.join(speakers)}")
    print("\nReviewing speakers...")

    for speaker in speakers:
        final_transcript, _ = _review_speaker_interactively(speaker, final_transcript, get_speaker_context_lines)

    display_result(final_transcript)

    if save_path:
        save_transcript(save_path, final_transcript)

    return final_transcript


def _lazy_import_diarization() -> tuple:
    """Lazy import diarization module to avoid loading torch on --help."""
    try:
        from vtt_transcribe.diarization import (
            SpeakerDiarizer,
            format_diarization_output,
            get_speaker_context_lines,
            get_unique_speakers,
        )
    except ModuleNotFoundError as e:
        # Only catch ModuleNotFoundError for the package module itself
        if e.name in ("vtt_transcribe.diarization", "vtt_transcribe"):
            # Fallback for direct execution
            try:
                from diarization import (  # type: ignore[no-redef]
                    SpeakerDiarizer,
                    format_diarization_output,
                    get_speaker_context_lines,
                    get_unique_speakers,
                )
            except ImportError as e2:
                msg = (
                    "Diarization dependencies not installed. "
                    "Install with: pip install vtt-transcribe[diarization] "
                    "or: uv pip install vtt-transcribe[diarization]"
                )
                raise ImportError(msg) from e2
        else:
            # Raise a user-friendly ImportError for missing dependencies within the diarization module
            msg = (
                "Diarization dependencies not installed. "
                "Install with: pip install vtt-transcribe[diarization] "
                "or: uv pip install vtt-transcribe[diarization]"
            )
            raise ImportError(msg) from e
    except ImportError as e:
        # Any other ImportError (e.g., missing torch/pyannote inside the module)
        msg = (
            "Diarization dependencies not installed. "
            "Install with: pip install vtt-transcribe[diarization] "
            "or: uv pip install vtt-transcribe[diarization]"
        )
        raise ImportError(msg) from e
    return SpeakerDiarizer, format_diarization_output, get_unique_speakers, get_speaker_context_lines


def handle_standard_transcription(args: Any, api_key: str) -> str:
    """Handle standard transcription workflow with optional diarization.

    Returns:
        The final transcript (with or without speaker labels).
    """
    from vtt_transcribe.transcriber import VideoTranscriber

    transcriber = VideoTranscriber(api_key)

    input_path = Path(args.input_file)
    audio_path = Path(args.output_audio) if args.output_audio else None
    keep_audio = not args.delete_audio
    result = transcriber.transcribe(
        input_path, audio_path, force=args.force, keep_audio=keep_audio, scan_chunks=args.scan_chunks
    )

    # Apply diarization if requested
    if args.diarize:
        SpeakerDiarizer, _, _, _ = _lazy_import_diarization()  # noqa: N806
        diarizer = SpeakerDiarizer(hf_token=args.hf_token, device=args.device)
        # Determine the audio path used for transcription
        actual_audio_path = audio_path if audio_path else input_path.with_suffix(AUDIO_EXTENSION)
        if input_path.suffix.lower() in VideoTranscriber.SUPPORTED_AUDIO_FORMATS:
            actual_audio_path = input_path

        print("\nRunning speaker diarization...")
        segments = diarizer.diarize_audio(actual_audio_path)
        result = diarizer.apply_speakers_to_transcript(result, segments)

        # Run speaker review unless disabled
        if not args.no_review_speakers:
            result = handle_review_speakers(
                input_path=None,
                hf_token=args.hf_token,
                save_path=None,  # Don't auto-save during review, we'll save at end
                device=args.device,
                transcript=result,
            )

    return result
