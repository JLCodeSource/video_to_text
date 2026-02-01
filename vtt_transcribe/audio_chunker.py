"""Audio chunking logic for handling large audio files."""

import math

# Constants
MAX_FILE_SIZE_MB = 25
CHUNK_SAFETY_FACTOR = 0.9
SECONDS_PER_MINUTE = 60


class AudioChunker:
    """Calculate and manage audio file chunking for size limits."""

    @staticmethod
    def calculate_chunk_params(file_size_mb: float, duration_seconds: float) -> tuple[int, float]:
        """Calculate number of chunks and duration per chunk.

        Args:
            file_size_mb: Size of audio file in megabytes.
            duration_seconds: Duration of audio in seconds.

        Returns:
            Tuple of (number_of_chunks, chunk_duration_seconds).
        """
        if file_size_mb <= MAX_FILE_SIZE_MB:
            return 1, duration_seconds

        # Calculate chunk duration to stay under size limit
        chunk_duration = (MAX_FILE_SIZE_MB / file_size_mb) * duration_seconds * CHUNK_SAFETY_FACTOR

        # Round down to nearest minute for cleaner chunks (minimum 1 minute)
        chunk_duration = max(float(SECONDS_PER_MINUTE), math.floor(chunk_duration / SECONDS_PER_MINUTE) * SECONDS_PER_MINUTE)

        # Calculate number of chunks needed
        num_chunks = math.ceil(duration_seconds / chunk_duration)

        return num_chunks, chunk_duration

    @staticmethod
    def get_chunk_time_ranges(duration_seconds: float, chunk_duration: float) -> list[tuple[float, float]]:
        """Generate time ranges for each chunk.

        Args:
            duration_seconds: Total duration of audio.
            chunk_duration: Duration of each chunk.

        Returns:
            List of (start_time, end_time) tuples in seconds.
        """
        chunks = []
        start = 0.0

        while start < duration_seconds:
            end = min(start + chunk_duration, duration_seconds)
            chunks.append((start, end))
            start = end

        return chunks
