"""Tests for audio_chunker module."""

from vtt.audio_chunker import AudioChunker


class TestAudioChunker:
    """Test AudioChunker functionality."""

    def test_calculate_chunk_params_small_file(self) -> None:
        """Should return 1 chunk for file under limit."""
        num_chunks, chunk_duration = AudioChunker.calculate_chunk_params(10.0, 300.0)

        assert num_chunks == 1
        assert chunk_duration == 300.0

    def test_calculate_chunk_params_large_file(self) -> None:
        """Should calculate multiple chunks for large file."""
        num_chunks, chunk_duration = AudioChunker.calculate_chunk_params(50.0, 3600.0)

        assert num_chunks > 1
        assert chunk_duration > 0
        assert chunk_duration <= 3600.0

    def test_get_chunk_time_ranges(self) -> None:
        """Should generate correct time ranges."""
        ranges = AudioChunker.get_chunk_time_ranges(300.0, 100.0)

        assert len(ranges) == 3
        assert ranges[0] == (0.0, 100.0)
        assert ranges[1] == (100.0, 200.0)
        assert ranges[2] == (200.0, 300.0)

    def test_get_chunk_time_ranges_uneven(self) -> None:
        """Should handle uneven division."""
        ranges = AudioChunker.get_chunk_time_ranges(250.0, 100.0)

        assert len(ranges) == 3
        assert ranges[0] == (0.0, 100.0)
        assert ranges[1] == (100.0, 200.0)
        assert ranges[2] == (200.0, 250.0)
