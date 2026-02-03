# Docker Registry Configuration

This document describes the GitHub secrets required for publishing Docker images to Docker Hub and GitHub Container Registry (GHCR).

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

## Published Images

Once configured, images will be available at:
- Docker Hub: `docker pull jlcodesource/vtt-transcribe:latest`
- GHCR: `docker pull ghcr.io/jlcodesource/vtt-transcribe:latest`

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
