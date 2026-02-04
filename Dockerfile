# Multi-stage Dockerfile for vtt-transcribe
# Optimized for size and security with non-root user

# Build stage: Install dependencies and build
FROM python:3.13-slim AS builder

WORKDIR /app

# Install system dependencies required for building
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency installation
RUN pip install --no-cache-dir uv

# Copy all files needed for installation
COPY pyproject.toml README.md ./
COPY vtt_transcribe ./vtt_transcribe

# Create virtual environment and install package with dependencies
RUN uv venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN uv pip install .

# Runtime stage: Minimal image with only runtime dependencies
FROM python:3.13-slim

# Install only runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 vttuser

# Copy virtual environment from builder (includes installed package)
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory for user files
WORKDIR /workspace

# Switch to non-root user
USER vttuser

# Set entrypoint
ENTRYPOINT ["vtt"]
CMD ["--help"]
