FROM nvcr.io/nvidia/pytorch:25.12-py3

ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# Rename the existing 'ubuntu' user to 'vscode' 
# and give them sudo powers
# Install ffmpeg (required for pyannote.audio torchcodec backend)
RUN if getent passwd ubuntu; then \
    usermod -l vscode ubuntu && \
    groupmod -n vscode ubuntu && \
    usermod -d /home/vscode -m vscode; \
    fi \
    && apt-get update \
    && apt-get install -y sudo ffmpeg \
    && echo vscode ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/vscode \
    && chmod 0440 /etc/sudoers.d/vscode \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory to the new home
WORKDIR /home/vscode

USER vscode