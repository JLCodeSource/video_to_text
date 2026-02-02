"""Health checks and dependency validation for vtt-transcribe.

This module provides preflight checks to ensure all required dependencies
are available before executing transcription workflow.
"""

import importlib
import shutil
from pathlib import Path


class DependencyError(Exception):
    """Raised when a required dependency is missing or invalid."""


def check_ffmpeg() -> None:
    """Check that ffmpeg and ffprobe are available.

    Raises:
        DependencyError: If ffmpeg or ffprobe not found in PATH.
    """
    ffmpeg_path = shutil.which("ffmpeg")
    if not ffmpeg_path:
        msg = "ffmpeg not found in PATH. Please install ffmpeg: https://ffmpeg.org/download.html"
        raise DependencyError(msg)

    ffprobe_path = shutil.which("ffprobe")
    if not ffprobe_path:
        msg = "ffprobe not found in PATH. Please install ffmpeg: https://ffmpeg.org/download.html"
        raise DependencyError(msg)


def check_python_packages() -> None:
    """Check that required Python packages are available.

    Raises:
        DependencyError: If a required package is missing.
    """
    required_packages = ["openai", "moviepy"]

    for package in required_packages:
        try:
            importlib.import_module(package)
        except ImportError as e:
            msg = f"Required Python package not found: {package}. Please install with: uv pip install vtt-transcribe"
            raise DependencyError(msg) from e


def check_disk_space(output_path: Path, min_free_mb: int = 100) -> None:
    """Check that sufficient disk space is available for output.

    Args:
        output_path: Path where output will be written.
        min_free_mb: Minimum free space required in megabytes (default: 100MB).

    Raises:
        DependencyError: If insufficient disk space or path inaccessible.
    """
    try:
        # Check parent directory if output file doesn't exist yet
        check_path = output_path.parent if not output_path.exists() else output_path
        usage = shutil.disk_usage(check_path)
        free_mb = usage.free / (1024 * 1024)

        if free_mb < min_free_mb:
            msg = f"Insufficient disk space. Required: {min_free_mb}MB, Available: {free_mb:.1f}MB"
            raise DependencyError(msg)
    except (FileNotFoundError, OSError) as e:
        msg = f"Cannot access output path: {output_path}. Ensure parent directory exists and is writable."
        raise DependencyError(msg) from e


def run_preflight(output_path: Path) -> None:
    """Run all preflight checks before transcription.

    Args:
        output_path: Path where transcript will be written.

    Raises:
        DependencyError: If any preflight check fails.
    """
    check_ffmpeg()
    check_python_packages()
    check_disk_space(output_path)
