"""Tests for health check and dependency validation."""

import re
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from vtt_transcribe.health import (
    DependencyError,
    check_disk_space,
    check_ffmpeg,
    check_python_packages,
    run_preflight,
)


class TestFFmpegCheck:
    """Tests for ffmpeg availability checks."""

    def test_check_ffmpeg_success(self) -> None:
        """Test ffmpeg check passes when both executables present."""
        with (
            patch("shutil.which") as mock_which,
        ):
            mock_which.side_effect = lambda x: f"/usr/bin/{x}" if x in ["ffmpeg", "ffprobe"] else None

            check_ffmpeg()  # Should not raise

    def test_check_ffmpeg_missing_ffmpeg(self) -> None:
        """Test ffmpeg check fails when ffmpeg missing."""
        with patch("shutil.which") as mock_which:
            mock_which.side_effect = lambda x: "/usr/bin/ffprobe" if x == "ffprobe" else None

            with pytest.raises(DependencyError, match="ffmpeg not found"):
                check_ffmpeg()

    def test_check_ffmpeg_missing_ffprobe(self) -> None:
        """Test ffmpeg check fails when ffprobe missing."""
        with patch("shutil.which") as mock_which:
            mock_which.side_effect = lambda x: "/usr/bin/ffmpeg" if x == "ffmpeg" else None

            with pytest.raises(DependencyError, match="ffprobe not found"):
                check_ffmpeg()

    def test_check_ffmpeg_missing_both(self) -> None:
        """Test ffmpeg check fails when both missing."""
        with (
            patch("shutil.which", return_value=None),
            pytest.raises(DependencyError, match="ffmpeg not found"),
        ):
            check_ffmpeg()


class TestPythonPackagesCheck:
    """Tests for Python package validation."""

    def test_check_python_packages_success(self) -> None:
        """Test package check passes when all packages available."""
        check_python_packages()  # Should not raise if deps installed

    def test_check_python_packages_missing(self) -> None:
        """Test package check fails when required package missing."""
        with patch("importlib.import_module") as mock_import:
            mock_import.side_effect = ImportError("No module named 'openai'")

            with pytest.raises(DependencyError, match=re.escape("Required Python package") + r".*openai"):
                check_python_packages()


class TestDiskSpaceCheck:
    """Tests for disk space validation."""

    def test_check_disk_space_sufficient(self, tmp_path: Path) -> None:
        """Test disk space check passes when space available."""
        output_path = tmp_path / "test_output.txt"

        with patch("shutil.disk_usage") as mock_usage:
            mock_usage.return_value = MagicMock(free=10 * 1024 * 1024 * 1024)  # 10GB free

            check_disk_space(output_path)  # Should not raise

    def test_check_disk_space_insufficient(self, tmp_path: Path) -> None:
        """Test disk space check fails when space low."""
        output_path = tmp_path / "test_output.txt"

        with patch("shutil.disk_usage") as mock_usage:
            mock_usage.return_value = MagicMock(free=50 * 1024 * 1024)  # 50MB free

            with pytest.raises(DependencyError, match="Insufficient disk space"):
                check_disk_space(output_path)

    def test_check_disk_space_invalid_path(self, tmp_path: Path) -> None:
        """Test disk space check handles invalid paths."""
        output_path = tmp_path / "nonexistent" / "path" / "output.txt"

        with patch("shutil.disk_usage") as mock_usage:
            mock_usage.side_effect = FileNotFoundError()

            with pytest.raises(DependencyError, match="Cannot access output path"):
                check_disk_space(output_path)


class TestRunPreflight:
    """Tests for complete preflight check."""

    def test_run_preflight_success(self, tmp_path: Path) -> None:
        """Test preflight passes when all checks succeed."""
        output_path = tmp_path / "test_output.txt"

        with (
            patch("vtt_transcribe.health.check_ffmpeg"),
            patch("vtt_transcribe.health.check_python_packages"),
            patch("vtt_transcribe.health.check_disk_space"),
        ):
            run_preflight(output_path)  # Should not raise

    def test_run_preflight_ffmpeg_failure(self, tmp_path: Path) -> None:
        """Test preflight fails on ffmpeg check."""
        output_path = tmp_path / "test_output.txt"

        with (
            patch("vtt_transcribe.health.check_ffmpeg") as mock_ffmpeg,
            patch("vtt_transcribe.health.check_python_packages"),
            patch("vtt_transcribe.health.check_disk_space"),
        ):
            mock_ffmpeg.side_effect = DependencyError("ffmpeg not found")

            with pytest.raises(DependencyError, match="ffmpeg not found"):
                run_preflight(output_path)

    def test_run_preflight_package_failure(self, tmp_path: Path) -> None:
        """Test preflight fails on package check."""
        output_path = tmp_path / "test_output.txt"

        with (
            patch("vtt_transcribe.health.check_ffmpeg"),
            patch("vtt_transcribe.health.check_python_packages") as mock_packages,
            patch("vtt_transcribe.health.check_disk_space"),
        ):
            mock_packages.side_effect = DependencyError("Missing openai")

            with pytest.raises(DependencyError, match="Missing openai"):
                run_preflight(output_path)

    def test_run_preflight_disk_space_failure(self, tmp_path: Path) -> None:
        """Test preflight fails on disk space check."""
        output_path = tmp_path / "test_output.txt"

        with (
            patch("vtt_transcribe.health.check_ffmpeg"),
            patch("vtt_transcribe.health.check_python_packages"),
            patch("vtt_transcribe.health.check_disk_space") as mock_disk,
        ):
            mock_disk.side_effect = DependencyError("Insufficient disk space")

            with pytest.raises(DependencyError, match="Insufficient disk space"):
                run_preflight(output_path)
