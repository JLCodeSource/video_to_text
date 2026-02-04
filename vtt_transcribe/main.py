import os
import sys
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


def main() -> None:
    parser = create_parser()
    args = parser.parse_args()

    # Validate that input_file is provided (unless using --version which is handled by argparse)
    # Note: input_file uses nargs="?" to support --version without requiring input_file.
    # This means parse_args() succeeds without input_file, so we validate here.
    # If adding new flags that don't require input_file, update this check accordingly.
    if args.input_file is None:
        parser.error("the following arguments are required: input_file")

    # Run dependency checks before any processing
    check_ffmpeg_installed()

    # Check diarization dependencies if any diarization flag is used
    if args.diarize or args.diarize_only or args.apply_diarization:
        check_diarization_dependencies()

    try:
        # Handle diarization modes first (they don't require OpenAI API key)
        if handle_diarization_modes(args):
            return

        # Standard transcription flow
        api_key = get_api_key(args.api_key)
        result = handle_standard_transcription(args, api_key)
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


if __name__ == "__main__":
    main()
