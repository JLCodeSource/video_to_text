# Roadmap

## Version 0.3.0b3 (Released 2026-02-01)
✅ **COMPLETED** - PyPI packaging and publication
- Package renamed from `vtt` to `vtt-transcribe` for PyPI publication
- Build system migrated to Hatch for modern Python packaging
- GitHub Actions configured for automated PyPI publishing with OIDC
- Comprehensive package structure tests added
- FFmpeg validation for diarization features
- Full documentation updated (README, CHANGELOG, CONTRIBUTING, USER_SETUP_GUIDE)
- Published to PyPI: `pip install vtt-transcribe`

## Version 0.3.0 (Next - Stable Release)
- Complete any remaining documentation improvements
- Address any user feedback from 0.3.0b3
- Final testing across platforms
- Remove beta tag and release stable version

## Features completed in 0.3.x series
- ✅ Direct audio transcription: first-class support for audio-only inputs (.mp3, .ogg, .wav, .m4a)
- ✅ Speaker diarization: pyannote.audio integration for speaker identification
- ✅ Tests and validation: comprehensive unit and integration tests (207 tests, 95% coverage)
- ✅ PyPI packaging: Published package with automated workflows

## Version 0.4 (local processing & packaging)
Objective: add local-only Whisper processing and comprehensive packaging options for both connected and air-gapped environments.

**Why deferred to 0.4:**
- Local Whisper processing requires ffmpeg v8+, but current ecosystem tools (moviepy with imageio-ffmpeg and pyannote) don't yet support v8
- This allows time for upstream dependencies to mature and for proper testing of ffmpeg version detection and fallback mechanisms
- Packaging strategy can be finalized alongside local processing implementation

## Technical Debt
- **Torch version locked to 2.8.0**: torch 2.10+ introduced breaking changes to `torch.load(..., weights_only=...)` that cause pyannote.audio 3.1 diarization models to fail. Upgrade to torch 2.10+ once pyannote.audio officially supports it.

## Features and behavior
- Local-only processing via ffmpeg + Whisper model: on first run, search PATH for ffmpeg, check its version (must be >= v8 for Whisper compatibility) and notify the user if the system ffmpeg is too old, including instructions to set an environment variable to point to a different ffmpeg binary.
  - Model handling: check for an env var (e.g., WHISPER_MODEL_PATH) that points to a local Whisper model; if absent, offer to download a selected optional Whisper model (show model size and a download link). If automatic download fails, present manual download instructions and ask the user to set the env var to the downloaded model path for next runs.
- UX details: provide clear prompts and non-blocking flags to perform downloads or to skip them for air-gapped setups; surface helpful error messages and next steps when checks fail.
- Tests and validation: add unit and integration tests covering ffmpeg version checks and model download/error flows.

## Packaging options

This needs a rethink given the new functionality, but initially, the intention was to use one of these approaches:

1) imageio-based ffmpeg (recommended default)
- Rely on imageio-ffmpeg (used by moviepy) to download an ffmpeg binary on first run.
- Advantages: smaller wheel/artifact, no need to ship a large ffmpeg binary, leverages imageio's single-download-per-environment behaviour.
- UX notes: document that the download happens once per environment and provide guidance when running in CI or constrained networks.

2) Bundled ffmpeg / self-contained artifacts
- Produce self-contained artifacts that include an ffmpeg binary built on ManyLinux2010 (or equivalent) or provide a PyInstaller-built single executable bundling ffmpeg.
- Advantages: works in air-gapped environments and on systems without a system ffmpeg available.
- Build notes: implement a manylinux/CI build pipeline that compiles ffmpeg against ManyLinux2010, runs auditwheel to produce a compliant wheel, and publishes artifacts alongside the main release.

Implementation plan
- Document both options in README and ROADMAP, and make imageio-based behaviour the default runtime path.
- Add CI jobs for manylinux builds and PyInstaller packaging; publish bundled artifacts for users who need them.
- Provide clear installation docs showing how to opt into bundled artifacts vs the default imageio behaviour.

Next steps
- Add packaging CI jobs and test wheels/artifacts; optionally add a small packaging script that automates building and publishing bundled artifacts.
