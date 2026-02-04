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

# Copy only dependency files first (for better layer caching)
COPY pyproject.toml README.md ./

# Create virtual environment
RUN uv venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy source code
COPY vtt_transcribe ./vtt_transcribe

# Install package with dependencies (cached unless pyproject.toml or source changes)
RUN uv pip install "."

# Runtime stage: Minimal image with only runtime dependencies
FROM python:3.13-slim

# Configurable UID for non-root user (default 1000 for typical Linux desktops)
ARG USER_UID=1000

# Install only runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u "$USER_UID" vttuser

# Copy virtual environment from builder (includes installed package)
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory for user files
WORKDIR /workspace

# Switch to non-root user
USER vttuser

# Ensure Python output is unbuffered
ENV PYTHONUNBUFFERED=1

# Set entrypoint (no CMD - let stdin detection or user args determine behavior)
ENTRYPOINT ["vtt"]
