"""video-to-text (vtt) package."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("vtt-transcribe")
except PackageNotFoundError:
    __version__ = "unknown"

__all__ = ["__version__"]
