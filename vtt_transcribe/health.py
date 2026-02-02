"""Health checks and dependency validation for vtt-transcribe.

This module provides preflight checks to ensure all required dependencies
are available before executing transcription workflow.
"""

import shutil
import sys


def check_ffmpeg_installed() -> None:
    """Check if ffmpeg is installed and available in PATH.

    Exits with detailed installation instructions if ffmpeg is not found.
    """
    if shutil.which("ffmpeg") is None:
        print("\nError: ffmpeg is not installed or not in PATH.", file=sys.stderr)
        print(
            "\nffmpeg is required for audio extraction and processing.",
            file=sys.stderr,
        )
        print("\nInstallation instructions:", file=sys.stderr)
        print("  • Ubuntu/Debian: sudo apt-get install ffmpeg", file=sys.stderr)
        print("  • macOS (Homebrew): brew install ffmpeg", file=sys.stderr)
        print("  • Windows (Chocolatey): choco install ffmpeg", file=sys.stderr)
        print("  • Windows (Scoop): scoop install ffmpeg", file=sys.stderr)
        print("  • Or download from: https://ffmpeg.org/download.html\n", file=sys.stderr)
        sys.exit(1)
