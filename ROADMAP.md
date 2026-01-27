Roadmap

Version 0.3 (current)
Last updated: 2026-01-27T10:24:11.434Z
- TDD Github agent skill: add workflows and tests that enable a GitHub agent to run test-driven tasks, validate patches, and report status back to PRs.
- .devcontainer structure: include a .devcontainer with recommended VS Code settings, extensions, and a consistent dev image for contributors.

Features and behavior
- Direct audio transcription: first-class support for audio-only inputs (.mp3, .ogg, .wav). If the provided file is an individual chunk, default to processing that chunk only; provide a --scan-chunks (or similar) flag to detect sibling chunk files and process them all in order when requested.
- Speaker diarization: integrate or provide hooks for speaker identification/diarization so transcripts can label or cluster speech segments by speaker; when diarization is requested via a flag, offer to download required diarization models (show model sizes and links) or accept a path via an env var; expose a flag to enable/disable diarization and to choose diarization backends when available.
- Local-only processing via ffmpeg + Whisper model: on first run, search PATH for ffmpeg, check its version (must be > v8) and notify the user if the system ffmpeg is too old, including instructions to set an environment variable to point to a different ffmpeg binary.
  - Model handling: check for an env var (e.g., WHISPER_MODEL_PATH) that points to a local Whisper model; if absent, offer to download a selected optional Whisper model (show model size and a download link). If automatic download fails, present manual download instructions and ask the user to set the env var to the downloaded model path for next runs.

- UX details: provide clear prompts and non-blocking flags to perform downloads or to skip them for air-gapped setups; surface helpful error messages and next steps when checks fail.

- Tests and validation: add unit and integration tests covering direct-audio paths, chunk scanning/ordering, diarization toggle, ffmpeg version checks, and model download/error flows.

Version 0.4 (packaging)
Objective: make distribution easy for both connected and air-gapped users by providing two packaging options.

Packaging options
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
