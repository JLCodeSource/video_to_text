# BATS Test Audit

## Summary
Reviewed all BATS smoke tests in `stdin.bats` to identify tests that can be moved to Python unit tests.

## Findings

### Tests That Should Stay in BATS (Environment/Integration Tests)

1. **"uv run transcribes from stdin"** - Tests `uv run` command execution
   - Reason: Tests the `uv run` development workflow

2. **"installed package transcribes from stdin"** - Tests `vtt` CLI command
   - Reason: Tests package installation and CLI availability

3. **"docker transcribes from stdin with env var"** - Tests Docker container
   - Reason: Docker-specific integration test

4. **"docker transcribes with output redirect"** - Tests Docker output handling
   - Reason: Docker-specific integration test

5. **"docker diarization with env vars"** - Tests Docker diarization
   - Reason: Docker-specific integration test

**Total BATS tests to keep: 5**

### Tests Already Covered by Python Unit Tests

6. **"rejects incompatible -s flag"** 
   - Python equivalent: `tests/test_stdin_mode.py::TestStdinIncompatibleFlags::test_save_transcript_incompatible`
   - Recommendation: **Can remove from BATS** (redundant)

7. **"rejects incompatible -o flag"**
   - Python equivalent: `tests/test_stdin_mode.py::TestStdinIncompatibleFlags::test_output_audio_incompatible`
   - Recommendation: **Can remove from BATS** (redundant)

8. **"auto-enables --no-review-speakers for diarization"**
   - Python equivalent: `tests/test_main.py::TestStdinMode::test_stdin_diarize_only_auto_enables`
   - Recommendation: **Can remove from BATS** (redundant)

9. **"accepts diarization with explicit --no-review-speakers"**
   - Python equivalent: `tests/test_main.py::TestStdinMode::test_stdin_no_review_speakers_already_set`
   - Recommendation: **Can remove from BATS** (redundant)

## Recommendations

### Option 1: Remove Redundant BATS Tests (Recommended)
Remove tests #6-9 from `stdin.bats` since they're fully covered by Python unit tests. This would reduce BATS tests from 9 to 5, focusing on Docker/environment integration only.

**Pros:**
- Faster test execution (Python tests are much faster)
- No duplication of test logic
- Clearer separation: BATS for integration, Python for unit/logic

**Cons:**
- Lose end-to-end validation of these specific behaviors via CLI

### Option 2: Keep BATS Tests As Integration Validation
Keep all BATS tests as end-to-end smoke tests, even though logic is tested in Python.

**Pros:**
- Full end-to-end validation via actual CLI
- Catches integration issues that unit tests might miss

**Cons:**
- Slower test execution
- Duplication of test coverage
- Requires OPENAI_API_KEY and HF_TOKEN for more tests

## Decision

**Recommend Option 1**: Remove tests #6-9 from BATS.

**Reasoning:**
- Python unit tests provide better isolation and faster feedback
- The remaining 5 BATS tests focus on what BATS is good at: environment/Docker integration
- The removed behaviors are critical logic that's better tested in Python with mocks
- Users can still run the Docker integration tests (#3-5) to verify end-to-end functionality

## Action Items

- [x] Audit BATS tests
- [ ] Create PR to remove redundant BATS tests #6-9
- [ ] Update `tests/smoke/README.md` to document new test scope
