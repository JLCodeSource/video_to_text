#!/usr/bin/env bats
# Smoke tests for standard (non-stdin) functionality

setup() {
    # Determine project root relative to test directory
    PROJECT_ROOT="${BATS_TEST_DIRNAME}/../.."
    
    # Load environment variables from .env if it exists and variables aren't already set
    if [[ -f "${PROJECT_ROOT}/.env" ]]; then
        set -a  # automatically export all variables
        source "${PROJECT_ROOT}/.env"
        set +a
    fi
    
    # Test file paths
    TEST_AUDIO_MP3="${BATS_TEST_DIRNAME}/../hello_conversation.mp3"
    TEST_VIDEO_MP4="${BATS_TEST_DIRNAME}/../hello_conversation.mp4"
    
    # Skip if test files don't exist
    if [[ ! -f "$TEST_AUDIO_MP3" ]]; then
        skip "Test audio file not found: $TEST_AUDIO_MP3"
    fi
    
    if [[ ! -f "$TEST_VIDEO_MP4" ]]; then
        skip "Test video file not found: $TEST_VIDEO_MP4"
    fi
    
    # Ensure venv is activated or vtt is available
    if [[ -f "${PROJECT_ROOT}/.venv/bin/vtt" ]]; then
        export PATH="${PROJECT_ROOT}/.venv/bin:$PATH"
    fi
    
    # Install vtt if not available (for package tests)
    if ! command -v vtt &> /dev/null; then
        echo "# Installing vtt package..." >&3
        cd "${PROJECT_ROOT}" && uv pip install -e . >&3 2>&1
        export PATH="${PROJECT_ROOT}/.venv/bin:$PATH"
    fi
    
    # Temp directory for output files
    TEMP_DIR=$(mktemp -d)
}

teardown() {
    # Cleanup temp directory if it exists
    if [[ -n "$TEMP_DIR" ]] && [[ -d "$TEMP_DIR" ]]; then
        rm -rf "$TEMP_DIR"
    fi
}

# ============================================================================
# MP3 Audio File Tests
# ============================================================================

@test "standard: transcribe MP3 file with vtt command" {
    # Skip if OPENAI_API_KEY not set
    if [[ -z "$OPENAI_API_KEY" ]]; then
        skip "OPENAI_API_KEY not set (set in environment or .env file)"
    fi
    
    OUTPUT_FILE="${TEMP_DIR}/transcript_mp3.txt"
    
    run vtt "$TEST_AUDIO_MP3" --save-transcript "$OUTPUT_FILE" -k "$OPENAI_API_KEY"
    
    # Debug output on failure
    if [ "$status" -ne 0 ]; then
        echo "Exit status: $status"
        echo "Output: $output"
    fi
    
    [ "$status" -eq 0 ]
    [[ -f "$OUTPUT_FILE" ]]
    [[ -s "$OUTPUT_FILE" ]]  # File is not empty
    grep -qi "hello world" "$OUTPUT_FILE"
}

@test "standard: transcribe MP3 file with uv run" {
    # Skip if OPENAI_API_KEY not set
    if [[ -z "$OPENAI_API_KEY" ]]; then
        skip "OPENAI_API_KEY not set (set in environment or .env file)"
    fi
    
    OUTPUT_FILE="${TEMP_DIR}/transcript_mp3_uv.txt"
    
    run bash -c "cd '$PROJECT_ROOT' && uv run vtt_transcribe/main.py '$TEST_AUDIO_MP3' --save-transcript '$OUTPUT_FILE' -k '$OPENAI_API_KEY'"
    
    [ "$status" -eq 0 ]
    [[ -f "$OUTPUT_FILE" ]]
    [[ -s "$OUTPUT_FILE" ]]
    grep -qi "hello world" "$OUTPUT_FILE"
}

# ============================================================================
# MP4 Video File Tests
# ============================================================================

@test "standard: transcribe MP4 video file with vtt command" {
    # Skip if OPENAI_API_KEY not set
    if [[ -z "$OPENAI_API_KEY" ]]; then
        skip "OPENAI_API_KEY not set (set in environment or .env file)"
    fi
    
    OUTPUT_FILE="${TEMP_DIR}/transcript_mp4.txt"
    
    run vtt "$TEST_VIDEO_MP4" --save-transcript "$OUTPUT_FILE" -k "$OPENAI_API_KEY"
    
    # Debug output on failure
    if [ "$status" -ne 0 ]; then
        echo "Exit status: $status"
        echo "Output: $output"
    fi
    
    [ "$status" -eq 0 ]
    [[ -f "$OUTPUT_FILE" ]]
    [[ -s "$OUTPUT_FILE" ]]
    grep -qi "hello world" "$OUTPUT_FILE"
}

@test "standard: transcribe MP4 video file with uv run" {
    # Skip if OPENAI_API_KEY not set
    if [[ -z "$OPENAI_API_KEY" ]]; then
        skip "OPENAI_API_KEY not set (set in environment or .env file)"
    fi
    
    OUTPUT_FILE="${TEMP_DIR}/transcript_mp4_uv.txt"
    
    run bash -c "cd '$PROJECT_ROOT' && uv run vtt_transcribe/main.py '$TEST_VIDEO_MP4' --save-transcript '$OUTPUT_FILE' -k '$OPENAI_API_KEY'"
    
    [ "$status" -eq 0 ]
    [[ -f "$OUTPUT_FILE" ]]
    [[ -s "$OUTPUT_FILE" ]]
    grep -qi "hello world" "$OUTPUT_FILE"
}

# ============================================================================
# Diarization Tests
# ============================================================================

@test "standard: transcribe MP4 with diarization (no review)" {
    # Skip if OPENAI_API_KEY not set
    if [[ -z "$OPENAI_API_KEY" ]]; then
        skip "OPENAI_API_KEY not set (set in environment or .env file)"
    fi
    
    # Skip if HF_TOKEN not set (needed for diarization)
    if [[ -z "$HF_TOKEN" ]]; then
        skip "HF_TOKEN not set (set in environment or .env file)"
    fi
    
    OUTPUT_FILE="${TEMP_DIR}/transcript_diarized.txt"
    
    run vtt "$TEST_VIDEO_MP4" --save-transcript "$OUTPUT_FILE" -k "$OPENAI_API_KEY" --diarize --no-review-speakers --hf-token "$HF_TOKEN"
    
    # Debug output on failure
    if [ "$status" -ne 0 ]; then
        echo "Exit status: $status"
        echo "Output: $output"
    fi
    
    [ "$status" -eq 0 ]
    [[ -f "$OUTPUT_FILE" ]]
    [[ -s "$OUTPUT_FILE" ]]
    grep -q "SPEAKER" "$OUTPUT_FILE"  # Should contain speaker labels
}

# ============================================================================
# Output Format Validation Tests
# ============================================================================

@test "standard: output contains timestamp format" {
    # Skip if OPENAI_API_KEY not set
    if [[ -z "$OPENAI_API_KEY" ]]; then
        skip "OPENAI_API_KEY not set (set in environment or .env file)"
    fi
    
    OUTPUT_FILE="${TEMP_DIR}/transcript_timestamps.txt"
    
    run vtt "$TEST_AUDIO_MP3" --save-transcript "$OUTPUT_FILE" -k "$OPENAI_API_KEY"
    
    [ "$status" -eq 0 ]
    [[ -f "$OUTPUT_FILE" ]]
    
    # Check for timestamp format [HH:MM:SS - HH:MM:SS]
    grep -E "\[[0-9]{2}:[0-9]{2}:[0-9]{2} - [0-9]{2}:[0-9]{2}:[0-9]{2}\]" "$OUTPUT_FILE"
}
