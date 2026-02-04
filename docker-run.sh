#!/bin/bash
# Helper script to run vtt-transcribe in Docker with proper volume mounting
#
# This script handles the complexity of Docker-in-Docker scenarios (like devcontainers)
# by automatically detecting the correct host path to mount.

set -e

# Detect if we're in a devcontainer by checking if we're already in a Docker container
if [ -f /.dockerenv ] || grep -sq 'docker\|lxc' /proc/1/cgroup 2>/dev/null; then
    # We're in a container - get the host path from our own container inspect
    HOST_PATH=$(docker inspect $(hostname) 2>/dev/null | grep -A1 '"Source"' | grep -v "docker.sock" | head -1 | sed 's/.*"Source": "\(.*\)",/\1/')
    
    if [ -z "$HOST_PATH" ]; then
        echo "Warning: Could not detect host path. Falling back to current directory."
        HOST_PATH=$(pwd)
    fi
else
    # Not in a container - use current directory
    HOST_PATH=$(pwd)
fi

# Run docker with the detected path
docker run --rm \
    -v "$HOST_PATH:/workspace" \
    -w /workspace \
    -e OPENAI_API_KEY \
    -e HF_TOKEN \
    vtt-transcribe:latest \
    "$@"
