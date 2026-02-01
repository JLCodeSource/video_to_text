# User Setup Guide for PyPI Publishing

This guide covers the manual steps needed before we can publish `vtt-transcribe` to PyPI.

## Overview

We're using **OIDC (OpenID Connect) Trusted Publishing**, which is the modern, secure way to publish to PyPI. No API tokens needed - GitHub Actions authenticates directly with PyPI using cryptographic proofs.

## Why TestPyPI?

TestPyPI (https://test.pypi.org) is a separate PyPI instance for testing. Benefits:
- **Safe testing**: Try the full release process without affecting production
- **Catch issues early**: Verify package metadata, README rendering, install process
- **No mistakes on production**: Once published to PyPI, versions cannot be deleted
- **Best practice**: Always test on TestPyPI first for new packages

## Required Steps

---

### 1. TestPyPI Setup (T060_001) [OPTIONAL BUT RECOMMENDED]

#### 1a. Create TestPyPI Account
1. Go to: https://test.pypi.org/account/register/
2. Fill out the form:
   - Username: (your choice)
   - Email: (your email)
   - Password: (strong password)
3. Verify your email
4. Enable 2FA (Two-Factor Authentication) - **REQUIRED for OIDC**
   - Go to: https://test.pypi.org/manage/account/
   - Under "Two factor authentication", click "Add 2FA with authentication application"
   - Use app like Google Authenticator, Authy, or 1Password
   - Save recovery codes securely

#### 1b. Register Project on TestPyPI
You have two options:

**Option A: Manual Registration (Recommended)**
1. Go to: https://test.pypi.org/manage/projects/
2. Click "Create new project"
3. Enter project name: `vtt-transcribe`
4. This reserves the name before first publish

**Option B: Let first publish create it**
- OIDC publishing will auto-create the project on first push
- Slightly riskier (name might be taken)

#### 1c. Configure TestPyPI Trusted Publisher
1. Go to: https://test.pypi.org/manage/account/publishing/
2. Click "Add a new publisher"
3. Fill in the form:
   - **PyPI Project Name**: `vtt-transcribe`
   - **Owner**: `JLCodeSource`
   - **Repository name**: `vtt-transcribe`
   - **Workflow filename**: `publish.yml`
   - **Environment name**: `testpypi` (leave blank if not using environments)
4. Click "Add"

**Result**: TestPyPI will now accept publishes from your GitHub Actions workflow.

---

### 2. Production PyPI Setup (T060_002 - REQUIRED)

#### 2a. Verify PyPI Account
You should already have a PyPI account (mentioned in summary that project is registered).

**Verify 2FA is enabled** (required for OIDC):
1. Go to: https://pypi.org/manage/account/
2. Under "Two factor authentication", ensure it's enabled
3. If not, add it now (same process as TestPyPI)

#### 2b. Configure PyPI Trusted Publisher
1. Go to: https://pypi.org/manage/account/publishing/
2. Click "Add a new publisher"
3. Fill in the form:
   - **PyPI Project Name**: `vtt-transcribe`
   - **Owner**: `JLCodeSource`
   - **Repository name**: `vtt-transcribe`
   - **Workflow filename**: `publish.yml`
   - **Environment name**: `pypi`
4. Click "Add"

**Important**: The environment name `pypi` must match what we configure in GitHub (next step).

---

### 3. GitHub Environment Setup (T060_002 - REQUIRED)

GitHub Environments provide additional security by requiring approval before publishing.

#### 3a. Create `pypi` Environment
1. Go to: https://github.com/JLCodeSource/vtt-transcribe/settings/environments
2. Click "New environment"
3. Name: `pypi`
4. Click "Configure environment"

#### 3b. Add Protection Rules
Under "Environment protection rules":

1. **Required reviewers**:
   - Check "Required reviewers"
   - Add yourself (JLCodeSource)
   - This means you must manually approve each release

2. **Wait timer** (optional):
   - Leave at 0 minutes (no wait)
   - Or set to 5 minutes for a cooling-off period

3. **Deployment branches and tags**:
   - Select "Selected branches and tags"
   - Add rule: `refs/tags/v*`
   - This ensures only tagged releases trigger publishing

#### 3c. Create `testpypi` Environment (OPTIONAL)
If you want to test on TestPyPI first:
1. Repeat steps 3a-3b for environment named `testpypi`
2. Can skip protection rules for testing (or use lighter rules)

---

### 4. Update GitHub Workflow (Already Done - For Reference)

Our `.github/workflows/publish.yml` is already configured with:
- OIDC permissions (`id-token: write`)
- Environment: `pypi` (for production)
- Trigger: GitHub releases
- Uses: `pypa/gh-action-pypi-publish@release/v1`

**No changes needed** - the workflow is ready to go.

---

## Verification Checklist

Before proceeding to release:

### TestPyPI (if using)
- [ ] Account created with 2FA enabled
- [ ] Project `vtt-transcribe` registered (or will auto-create)
- [ ] Trusted Publisher configured for TestPyPI
- [ ] GitHub environment `testpypi` created (optional)

### Production PyPI
- [ ] Account verified with 2FA enabled
- [ ] Project `vtt-transcribe` registered (already done)
- [ ] Trusted Publisher configured for PyPI
- [ ] GitHub environment `pypi` created with protection rules

### GitHub
- [ ] Environment `pypi` exists with:
  - [ ] Required reviewers configured
  - [ ] Deployment branches limited to tags
- [ ] Repository permissions allow GitHub Actions to publish
- [ ] Workflow file `publish.yml` is present and correct

---

## Testing the Setup (T060_003)

Once setup is complete, we can test with TestPyPI:

### Option 1: Test with workflow_dispatch
```bash
# Trigger workflow manually with test flag
gh workflow run publish.yml --ref packaging/v0.3.0b1 -f dry-run=true
```

### Option 2: Test publish to TestPyPI locally

**Setup TestPyPI API Token:**
1. Go to: https://test.pypi.org/manage/account/token/
2. Click "Add API token"
3. Name: `vtt-transcribe-local-testing`
4. Scope: `Project: vtt-transcribe` (or "Entire account" for first publish)
5. Click "Add token"
6. **Copy the token immediately** (shown only once)

**Configure credentials in .env:**
```bash
# Add to your .env file (automatically loaded)
echo 'TWINE_USERNAME="__token__"' >> .env
echo 'TWINE_PASSWORD="pypi-your-testpypi-token-here"' >> .env
echo 'TWINE_REPOSITORY="testpypi"' >> .env

# Verify (optional)
source .env
echo $TWINE_USERNAME
```

**Build and publish:**
```bash
# Build distribution packages
make build

# Publish to TestPyPI (credentials loaded from .env automatically)
make publish-test

# OR: Manual twine upload with credentials from .env
source .env
uv run twine upload --repository testpypi dist/*
```

**If successful**: Package appears at https://test.pypi.org/project/vtt-transcribe/

### Test Installation from TestPyPI (T060_004)
```bash
# Install from TestPyPI (requires both indexes for dependencies)
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ vtt-transcribe

# Test CLI
vtt --help
vtt --version

# Verify import
python -c "import vtt_transcribe; print('Success!')"
```

**Note on .env file:** The tool automatically loads `.env` if present, so TestPyPI credentials (TWINE_*) don't need to be exported manually - they'll be available when running `make publish-test`.

---

## Troubleshooting

### "Trusted publisher configuration does not match"
- Verify Owner, Repository, Workflow, and Environment names match exactly
- Environment name is case-sensitive
- Check for typos in repository name

### "Environment protection rules"
- Ensure you're added as a required reviewer
- Check that the tag matches the deployment branch pattern

### "Permission denied" or "OIDC token verification failed"
- Ensure 2FA is enabled on PyPI/TestPyPI
- Verify Trusted Publisher is configured correctly
- Check workflow has `id-token: write` permission

### "Project name already taken"
- If `vtt-transcribe` is taken on TestPyPI, use `vtt-transcribe-test` instead
- Production PyPI name is already registered

---

## Security Notes

### Why OIDC is Better Than API Tokens
- **No secrets**: No API tokens to leak or rotate
- **Short-lived**: OIDC tokens expire after minutes
- **Scoped**: Can only publish from specific workflows
- **Auditable**: PyPI logs show which workflow published each version

### What You Should NOT Do
- ❌ Don't share API tokens in code or logs
- ❌ Don't disable 2FA (required for OIDC)
- ❌ Don't skip environment protection rules (prevents accidental publishes)
- ❌ Don't publish to production PyPI without testing on TestPyPI first

---

## Timeline

**Setup time**: ~15-30 minutes
- TestPyPI: 10 minutes
- Production PyPI: 5 minutes
- GitHub environments: 5 minutes
- Testing: 10 minutes

**After setup**: Publishing takes ~2 minutes (automated)

---

## Next Steps After Setup

Once you confirm all setup is complete:
1. Tell me "Setup complete" or "Skip TestPyPI"
2. I'll execute T060_003-004 (TestPyPI testing) if desired
3. Or skip directly to T070 (production release)
4. Then T080-T090 (validation and cleanup)

---

## References

- [PyPI Trusted Publishers Guide](https://docs.pypi.org/trusted-publishers/)
- [GitHub OIDC Documentation](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect)
- [TestPyPI Help](https://test.pypi.org/help/)

