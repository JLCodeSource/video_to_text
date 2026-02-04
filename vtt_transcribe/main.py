import os
import sys
import tempfile
from argparse import Namespace
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
        diarization_result = handle_diarize_only_mode(
            Path(args.input_file), args.hf_token, save_path, args.device)

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
            Path(args.input_file), Path(
                args.apply_diarization), args.hf_token, save_path, args.device
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


def main() -> None:  # noqa: C901
    parser = create_parser()
    args = parser.parse_args()

    # Check if we're in stdin mode (data piped from stdin)
    stdin_mode = not sys.stdin.isatty()

    # Validate incompatible flags with stdin mode
    if stdin_mode:
        incompatible_flags = []
        if args.save_transcript:
            incompatible_flags.append("-s/--save-transcript")
        if args.output_audio:
            incompatible_flags.append("-o/--output-audio")
        if args.apply_diarization:
            incompatible_flags.append("--apply-diarization")
        if args.scan_chunks:
            incompatible_flags.append("--scan-chunks")

        if incompatible_flags:
            parser.error(
                f"stdin mode is incompatible with: {', '.join(incompatible_flags)}")

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
            # Determine file extension from args.input_file or default to .mp3
            extension = ".mp3"
            if args.input_file:
                extension = Path(args.input_file).suffix or ".mp3"

            # Read binary data from stdin
            audio_data = sys.stdin.buffer.read()

            # Create temp file with appropriate extension
            with tempfile.NamedTemporaryFile(mode="wb", suffix=extension, delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = Path(temp_file.name)

            # Override args.input_file to use the temp file
            args.input_file = str(temp_file_path)

        # Handle diarization modes first (they don't require OpenAI API key)
        if handle_diarization_modes(args):
            return

        # Standard transcription flow
        api_key = get_api_key(args.api_key)
        result = handle_standard_transcription(args, api_key)

        # In stdin mode, write transcript to stdout without formatting
        if stdin_mode:
            sys.stdout.write(result)
        else:
            display_result(result)

        if args.save_transcript:
            save_transcript(Path(args.save_transcript), result)

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
        if stdin_mode and temp_file_path and temp_file_path.exists():
            temp_file_path.unlink()


if __name__ == "__main__":
    main()
