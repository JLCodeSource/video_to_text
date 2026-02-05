import os
import sys
import tempfile
from argparse import ArgumentParser, Namespace
from pathlib import Path

from dotenv import load_dotenv

from vtt_transcribe.cli import create_parser
from vtt_transcribe.dependencies import check_diarization_dependencies, check_ffmpeg_installed
from vtt_transcribe.handlers import (
    display_result,
    handle_apply_diarization_mode,
    handle_diarize_only_mode,
    handle_review_speakers,
    handle_standard_transcription,
    save_transcript,
)

# Load environment variables from .env file
load_dotenv()


def get_api_key(api_key_arg: str | None) -> str:
    """Get API key from argument or environment variable."""
    api_key = api_key_arg or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        msg = "OpenAI API key not provided. Use -k/--api-key or set OPENAI_API_KEY environment variable."
        raise ValueError(msg)
    return api_key


def handle_diarization_modes(args: Namespace) -> bool:
    """Handle diarization-only and apply-diarization modes. Returns True if handled."""
    save_path = Path(args.save_transcript) if args.save_transcript else None

    # Handle diarization-only mode
    if args.diarize_only:
        diarization_result = handle_diarize_only_mode(Path(args.input_file), args.hf_token, save_path, args.device)

        # Run review unless disabled
        if not args.no_review_speakers:
            handle_review_speakers(
                input_path=None,
                hf_token=args.hf_token,
                save_path=save_path,
                device=args.device,
                transcript=diarization_result,
            )
        return True

    # Handle apply-diarization mode
    if args.apply_diarization:
        apply_result = handle_apply_diarization_mode(
            Path(args.input_file), Path(args.apply_diarization), args.hf_token, save_path, args.device
        )

        # Run review unless disabled
        if not args.no_review_speakers:
            handle_review_speakers(
                input_path=None,
                hf_token=args.hf_token,
                save_path=save_path,
                device=args.device,
                transcript=apply_result,
            )
        return True

    return False


def _validate_stdin_mode(args: Namespace, parser: ArgumentParser, *, stdin_mode: bool) -> None:
    """Validate args compatibility with stdin mode and auto-enable flags."""
    if not stdin_mode:
        return

    incompatible_flags = []
    if args.save_transcript:
        incompatible_flags.append("-s/--save-transcript")
    if args.output_audio:
        incompatible_flags.append("-o/--output-audio")
    if args.apply_diarization:
        incompatible_flags.append("--apply-diarization")
    if args.scan_chunks:
        incompatible_flags.append("--scan-chunks")

    # Auto-enable --no-review-speakers in stdin mode (interactive review requires TTY)
    if (args.diarize or args.diarize_only) and not args.no_review_speakers:
        args.no_review_speakers = True
        print(
            "Note: Automatically enabling --no-review-speakers (interactive review unavailable in stdin mode)",
            file=sys.stderr,
        )

    if incompatible_flags:
        parser.error(f"stdin mode is incompatible with: {', '.join(incompatible_flags)}")


def _output_result(result: str, *, stdin_mode: bool, save_path: str | None) -> None:
    """Output transcription result to stdout or display, and optionally save."""
    if stdin_mode:
        sys.stdout.write(result)
        # Ensure output ends with a newline to prevent shell prompt on same line
        if not result.endswith("\n"):
            sys.stdout.write("\n")
    else:
        display_result(result)

    if save_path:
        save_transcript(Path(save_path), result)


def _detect_format_from_data(data: bytes) -> str:
    """Detect file format from binary data magic bytes.

    Returns appropriate file extension (.mp4, .avi, .mov, .mp3, etc.)
    Falls back to .mp3 if format cannot be determined.
    """
    if len(data) < 12:
        return ".mp3"

    # MP4/M4A/MOV - ftyp box at bytes 4-8
    if data[4:8] == b"ftyp":
        # Check specific ftyp brand
        brand = data[8:12]
        if brand.startswith((b"isom", b"iso2", b"mp41", b"mp42", b"M4A ", b"M4V ", b"qt  ")):
            # Could be mp4, m4a, or mov - default to mp4 for video
            return ".mp4"
        # Fallback: any file with an 'ftyp' box is an ISO-BMFF/MP4-family file
        return ".mp4"

    # AVI - RIFF header with AVI signature
    if data[0:4] == b"RIFF" and data[8:12] == b"AVI ":
        return ".avi"

    # WebM/MKV - EBML header
    if data[0:4] == b"\x1a\x45\xdf\xa3":
        return ".webm"

    # MP3 - ID3 tag or MPEG sync
    if data[0:3] == b"ID3" or (data[0:2] == b"\xff\xfb") or (data[0:2] == b"\xff\xf3"):
        return ".mp3"

    # WAV - RIFF header with WAVE signature
    if data[0:4] == b"RIFF" and data[8:12] == b"WAVE":
        return ".wav"

    # OGG - OggS signature
    if data[0:4] == b"OggS":
        return ".ogg"

    # Default to mp3 for unknown formats
    return ".mp3"


def _create_temp_file_from_stdin(args: Namespace) -> Path:
    """Read audio data from stdin and create temporary file.

    Returns Path to temporary file that MUST be cleaned up by the caller.
    """
    # Read binary data from stdin
    audio_data = sys.stdin.buffer.read()

    # Determine file extension from args.input_file or detect from data
    if args.input_file:  # noqa: SIM108
        extension = Path(args.input_file).suffix or ".mp3"
    else:
        extension = _detect_format_from_data(audio_data)

    # Create temp file with appropriate extension
    with tempfile.NamedTemporaryFile(mode="wb", suffix=extension, delete=False) as temp_file:
        temp_file.write(audio_data)
        return Path(temp_file.name)


def main() -> None:
    parser = create_parser()
    args = parser.parse_args()

    # Check if we're in stdin mode (data piped from stdin)
    stdin_mode = not sys.stdin.isatty()

    # Validate incompatible flags with stdin mode
    _validate_stdin_mode(args, parser, stdin_mode=stdin_mode)

    # Validate that input_file is provided (unless using --version which is handled by argparse or stdin mode)
    # Note: input_file uses nargs="?" to support --version without requiring input_file.
    # This means parse_args() succeeds without input_file, so we validate here.
    # If adding new flags that don't require input_file, update this check accordingly.
    if args.input_file is None and not stdin_mode:
        parser.error("the following arguments are required: input_file")

    # Run dependency checks before any processing
    check_ffmpeg_installed()

    # Check diarization dependencies if any diarization flag is used
    if args.diarize or args.diarize_only or args.apply_diarization:
        check_diarization_dependencies()

    try:
        # Handle stdin mode: read binary data from stdin and create temp file
        temp_file_path = None
        if stdin_mode:
            temp_file_path = _create_temp_file_from_stdin(args)
            # Override args.input_file to use the temp file
            args.input_file = str(temp_file_path)

        # Handle diarization modes first (they don't require OpenAI API key)
        if handle_diarization_modes(args):
            return

        # Standard transcription flow
        api_key = get_api_key(args.api_key)
        result = handle_standard_transcription(args, api_key)
        _output_result(result, stdin_mode=stdin_mode, save_path=args.save_transcript)

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr, flush=True)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr, flush=True)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr, flush=True)
        sys.exit(1)
    finally:
        # Clean up temp file if created
        if stdin_mode and temp_file_path is not None and temp_file_path.exists():
            temp_file_path.unlink()


if __name__ == "__main__":
    main()
