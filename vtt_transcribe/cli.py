"""Command-line interface argument parsing for video_to_text."""

import argparse

from vtt_transcribe import __version__


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="Transcribe video or audio files using OpenAI's Whisper model",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s video.mp4                           # Basic transcription
  %(prog)s audio.mp3 --diarize                 # Audio with speaker identification
  %(prog)s video.mp4 --diarize -s output.txt   # Save diarized transcript
  %(prog)s audio.mp3 --diarize-only            # Only identify speakers
  %(prog)s audio.mp3 --apply-diarization transcript.txt  # Add speakers to existing transcript

Environment Variables:
  OPENAI_API_KEY    OpenAI API key for transcription
  HF_TOKEN          Hugging Face token for diarization (requires model access)
  DISABLE_GPU       Set to 1 to force CPU usage for diarization
        """,
    )

    # Version
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    # Positional arguments
    parser.add_argument(
        "input_file",
        nargs="?",
        help="Path to the video or audio file to transcribe (.mp4, .mp3, .wav, .ogg, .m4a)",
    )

    # API credentials
    api_group = parser.add_argument_group("API Credentials")
    api_group.add_argument(
        "-k",
        "--api-key",
        help="OpenAI API key (defaults to OPENAI_API_KEY environment variable)",
    )
    api_group.add_argument(
        "--hf-token",
        help="Hugging Face token for pyannote.audio models (defaults to HF_TOKEN environment variable)",
    )

    # Input/Output options
    io_group = parser.add_argument_group("Input/Output Options")
    io_group.add_argument(
        "-o",
        "--output-audio",
        help="Path for extracted audio file (defaults to input name with .mp3 extension)",
    )
    io_group.add_argument(
        "-s",
        "--save-transcript",
        help="Path to save the transcript to a file",
    )

    # Processing options
    process_group = parser.add_argument_group("Processing Options")
    process_group.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Re-extract audio even if it already exists",
    )
    process_group.add_argument(
        "--delete-audio",
        action="store_true",
        help="Delete audio files after transcription (default: keep audio files)",
    )
    process_group.add_argument(
        "--scan-chunks",
        action="store_true",
        help="When input is a chunk file, detect and process all sibling chunks in order",
    )

    # Diarization options
    diarize_group = parser.add_argument_group("Speaker Diarization Options")
    diarize_group.add_argument(
        "--diarize",
        action="store_true",
        help="Enable speaker diarization using pyannote.audio",
    )
    diarize_group.add_argument(
        "--device",
        choices=["auto", "cuda", "gpu", "cpu"],
        default="auto",
        help=(
            "Device for diarization: 'auto' (GPU if available), 'gpu'/'cuda' (force GPU), 'cpu'."
            " Set DISABLE_GPU=1 to force CPU."
        ),
    )
    diarize_group.add_argument(
        "--diarize-only",
        action="store_true",
        help="Run diarization on existing audio file without transcription",
    )
    diarize_group.add_argument(
        "--apply-diarization",
        help="Apply diarization to an existing transcript file",
    )
    diarize_group.add_argument(
        "--no-review-speakers",
        action="store_true",
        help="Skip interactive speaker review (default: review is ON for all diarization modes)",
    )

    return parser
