FROM nvcr.io/nvidia/pytorch:25.12-py3

ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# Rename the existing 'ubuntu' user to 'vscode' 
# and give them sudo powers
# Install ffmpeg (required for pyannote.audio torchcodec backend)
# Install GitHub CLI for task management
RUN if getent passwd ubuntu; then \
    usermod -l vscode ubuntu && \
    groupmod -n vscode ubuntu && \
    usermod -d /home/vscode -m vscode; \
    fi \
    && apt-get update \
    && apt-get install -y sudo ffmpeg curl ca-certificates gnupg \
    && curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
    && chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
    > /etc/apt/sources.list.d/github-cli.list \
    && apt-get update \
    && apt-get install -y gh \
    && echo vscode ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/vscode \
    && chmod 0440 /etc/sudoers.d/vscode \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory to the new home
WORKDIR /home/vscode

USER vscode