# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0b0] - 2026-01-31

### Added
- **Speaker diarization support**: Identify and label different speakers in transcripts using pyannote.audio
  - New `--diarize` flag to enable speaker identification
  - Interactive speaker review to rename/merge speakers
  - GPU support for faster processing (10-100x speedup)
  - Device selection via `--device` flag (`auto`, `cuda`, or `cpu`)
  - Requires Hugging Face token and model access
- **Direct audio transcription**: First-class support for audio-only inputs (.mp3, .wav, .ogg, .m4a)
  - Accepts audio files directly without video processing
  - New `--scan-chunks` flag to process all sibling chunk files
- **Enhanced timestamp format**: Changed from MM:SS to HH:MM:SS for better handling of long recordings
- **Modular architecture**: Refactored codebase into separate modules for better maintainability
  - `vtt.main`: CLI entrypoint and transcriber
  - `vtt.cli`: Command-line argument parsing
  - `vtt.handlers`: High-level processing handlers
  - `vtt.audio_manager`: Audio extraction and chunking
  - `vtt.audio_chunker`: Audio chunk management
  - `vtt.transcript_formatter`: Transcript formatting logic
  - `vtt.diarization`: Speaker diarization functionality

### Changed
- **BREAKING**: Diarization dependencies now optional
  - `pyannote.audio` and `torch` moved to optional `[diarization]` extra
  - Users must explicitly install with: `uv sync --extra diarization` or `pip install video-to-text[diarization]`
  - Use `make install-diarization` instead of `make install` to include diarization support
- **Dependency updates**: `python-dotenv` moved from dev dependencies to main dependencies
- Version format corrected to PEP 440 compliant: `0.3.0b0` (was `0.3.0_beta0`)

### Fixed
- Corrected chunk file sorting to handle indices >= 10 correctly (numerical sort instead of lexicographic)
- Fixed CLI help text examples to show correct argument order
- Resolved NameError in GPU memory checking when device is CPU
- Updated stale line number references in comments after refactoring

## Upgrading from 0.2.0

### For users NOT using speaker diarization
If you are only using basic transcription features (no speaker identification), no changes are required. Simply upgrade to 0.3.0b0:

```bash
uv sync
# or
pip install --upgrade video-to-text
```

### For users using or planning to use speaker diarization
If you were using diarization features in a development version OR plan to use the new diarization features in 0.3.0:

**Using uv:**
```bash
uv sync --extra diarization
```

**Using pip:**
```bash
pip install video-to-text[diarization]
```

**Using make:**
```bash
make install-diarization
```

This will install the required dependencies: `pyannote.audio` and `torch`.

### Why this change?
The diarization dependencies (torch + pyannote.audio) are quite large (~2-4GB) and not needed by all users. Making them optional:
- Reduces installation time and disk space for users who only need transcription
- Allows users to choose whether they need GPU support (torch with CUDA)
- Provides flexibility for different deployment scenarios (cloud vs local, CPU vs GPU)

## [0.2.0] - 2024-XX-XX

Initial stable release with core transcription functionality.

### Features
- Extract audio from video files
- Chunk large audio files to handle 25MB Whisper API limit
- Transcribe audio using OpenAI's Whisper API
- Format transcripts with timestamps
- Command-line interface
