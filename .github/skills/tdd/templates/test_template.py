"""Template for new test classes."""  # noqa: INP001

from unittest.mock import patch

from vtt_transcribe.main import VideoTranscriber


class TestFeatureTemplate:
    """Test [feature description]."""

    def test_happy_path(self) -> None:
        """Should [expected behavior in happy case]."""
        # Given setup/context
        with patch("vtt.main.OpenAI"):
            _transcriber = VideoTranscriber("test_key")

        # When action
        # result = _transcriber.some_method()  # noqa: ERA001

        # Then assertion
        # assert result is not None
        pass  # noqa: PIE790

    def test_edge_case(self) -> None:
        """Should [expected behavior for edge case]."""
        # Given edge case setup

        # When action triggering edge case

        # Then assertion
        pass  # noqa: PIE790
