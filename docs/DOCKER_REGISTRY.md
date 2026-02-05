# Docker Registry Configuration

This document describes the GitHub secrets required for publishing Docker images to Docker Hub and GitHub Container Registry (GHCR).

## Image Strategy

This project publishes two Docker images:

1. **Base Image** (`latest`) - Lightweight, transcription-only
   - Fast build (~27s)
   - Small size (~500MB)
   - Suitable for basic transcription workflows
   - Built on every release

2. **Diarization Image** (`diarization`) - Full feature set
   - Includes PyTorch and pyannote.audio
   - Larger size (~3-5GB)
   - Supports speaker identification
   - Built only on releases (not on PRs, to save build time)

## Required Secrets

Configure these secrets in your GitHub repository settings under **Settings > Secrets and variables > Actions**:

### Docker Hub

1. **DOCKERHUB_USERNAME**
   - Your Docker Hub username
   - Example: `jlcodesource`

2. **DOCKERHUB_TOKEN**
   - Docker Hub access token (NOT your password)
   - Create at: https://hub.docker.com/settings/security
   - Recommended permissions: Read, Write, Delete

### GitHub Container Registry

No additional secrets required. The workflow uses `GITHUB_TOKEN` which is automatically provided by GitHub Actions.

## Setting Up Secrets

### Via GitHub Web UI

1. Navigate to your repository on GitHub
2. Go to **Settings > Secrets and variables > Actions**
3. Click **New repository secret**
4. Add each secret with its name and value
5. Click **Add secret**

### Via GitHub CLI

```bash
# Set Docker Hub credentials
gh secret set DOCKERHUB_USERNAME --body "your-username"
gh secret set DOCKERHUB_TOKEN --body "your-token"
```

## Creating Docker Hub Access Token

1. Log in to Docker Hub: https://hub.docker.com
2. Click on your username > **Account Settings**
3. Go to **Security** tab
4. Click **New Access Token**
5. Name it (e.g., "GitHub Actions CI/CD")
6. Select permissions: **Read, Write, Delete**
7. Click **Generate**
8. Copy the token immediately (you won't see it again)
9. Add it as `DOCKERHUB_TOKEN` secret in GitHub

## Testing the Configuration

After setting up secrets, the Docker publish workflow will:
- Trigger automatically on release publication
- Can be manually triggered via **Actions > Docker CD - Publish Images > Run workflow**

### Manual Workflow Dispatch

To manually publish images:
```bash
# Using GitHub CLI (note: input version includes 'v' prefix, output tags will not)
gh workflow run docker-publish.yml -f version=v0.3.0b3

# Or via GitHub web UI
# Go to Actions > Docker CD - Publish Images > Run workflow
# Enter the version tag with 'v' prefix (e.g., v0.3.0b3)
# The workflow strips the 'v' when publishing Docker tags
```

## Published Images

Once configured, images will be available at:

**Base Image (transcription-only):**
- Docker Hub: `docker pull jlcodesource/vtt-transcribe:latest`
- GHCR: `docker pull ghcr.io/jlcodesource/vtt-transcribe:latest`

**Diarization Image (full feature set):**
- Docker Hub: `docker pull jlcodesource/vtt-transcribe:diarization`
- GHCR: `docker pull ghcr.io/jlcodesource/vtt-transcribe:diarization`

### Image Tags

Both registries publish the following tags:

**Base Image:**
- `latest` - Latest stable release
- `0.3.0b3` - Specific version
- `0.3` - Minor version (tracks latest 0.3.x)
- `0` - Major version (tracks latest 0.x.x)

**Diarization Image:**
- `diarization` - Latest stable release
- `0.3.0b3-diarization` - Specific version
- `0.3-diarization` - Minor version
- `0-diarization` - Major version

## CI/CD Build Strategy

To optimize CI/CD performance:

- **Base image**: Built and tested on all PRs and main branch pushes
- **Diarization image**: Built and tested only on main branch (skipped for PRs to save ~10-15 minutes build time)
- **Publishing**: Both images published only on releases or manual workflow dispatch

## Troubleshooting

**Authentication failed:**
- Verify secrets are set correctly (no extra spaces)
- Ensure Docker Hub token has write permissions
- Check token hasn't expired

**Build fails:**
- Check workflow logs in Actions tab
- Verify Dockerfile builds locally: `docker build -t test .`

**Multi-platform build issues:**
- Ensure Docker Buildx is available (handled by workflow)
- May need to enable experimental features for some runners
