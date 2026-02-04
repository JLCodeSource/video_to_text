#!/usr/bin/env bats
# Smoke tests for stdin mode functionality

setup() {
    # Test audio file path
    TEST_AUDIO="${BATS_TEST_DIRNAME}/../hello_conversation.mp3"
    
    # Skip if test audio doesn't exist
    if [[ ! -f "$TEST_AUDIO" ]]; then
        skip "Test audio file not found: $TEST_AUDIO"
    fi
}

@test "stdin mode: uv run transcribes from stdin" {
    # Skip if OPENAI_API_KEY not set
    if [[ -z "$OPENAI_API_KEY" ]]; then
        skip "OPENAI_API_KEY not set"
    fi
    
    run bash -c "cat '$TEST_AUDIO' | uv run vtt_transcribe/main.py"
    
    [ "$status" -eq 0 ]
    [[ "$output" =~ "hello world" ]] || [[ "$output" =~ "Hello world" ]]
}

@test "stdin mode: installed package transcribes from stdin" {
    # Skip if vtt not in PATH
    if ! command -v vtt &> /dev/null; then
        skip "vtt not installed"
    fi
    
    # Skip if OPENAI_API_KEY not set
    if [[ -z "$OPENAI_API_KEY" ]]; then
        skip "OPENAI_API_KEY not set"
    fi
    
    run bash -c "cat '$TEST_AUDIO' | vtt"
    
    [ "$status" -eq 0 ]
    [[ "$output" =~ "hello world" ]] || [[ "$output" =~ "Hello world" ]]
}

@test "stdin mode: docker transcribes from stdin with env var" {
    # Skip if docker not available or vtt:latest not built
    if ! command -v docker &> /dev/null; then
        skip "docker not available"
    fi
    
    if ! docker image inspect vtt:latest &> /dev/null; then
        skip "vtt:latest image not built"
    fi
    
    # Skip if OPENAI_API_KEY not set
    if [[ -z "$OPENAI_API_KEY" ]]; then
        skip "OPENAI_API_KEY not set"
    fi
    
    run bash -c "cat '$TEST_AUDIO' | docker run -i -e OPENAI_API_KEY vtt:latest"
    
    [ "$status" -eq 0 ]
    [[ "$output" =~ "hello world" ]] || [[ "$output" =~ "Hello world" ]]
}

@test "stdin mode: docker transcribes with output redirect" {
    # Skip if docker not available or vtt:latest not built
    if ! command -v docker &> /dev/null; then
        skip "docker not available"
    fi
    
    if ! docker image inspect vtt:latest &> /dev/null; then
        skip "vtt:latest image not built"
    fi
    
    # Skip if OPENAI_API_KEY not set
    if [[ -z "$OPENAI_API_KEY" ]]; then
        skip "OPENAI_API_KEY not set"
    fi
    
    # Create temp file for output
    TEMP_TRANSCRIPT=$(mktemp)
    
    # Run with output redirect
    cat "$TEST_AUDIO" | docker run -i -e OPENAI_API_KEY vtt:latest > "$TEMP_TRANSCRIPT"
    
    # Check output file
    [[ -s "$TEMP_TRANSCRIPT" ]]
    grep -qi "hello world" "$TEMP_TRANSCRIPT"
    
    # Cleanup
    rm -f "$TEMP_TRANSCRIPT"
}

@test "stdin mode: rejects incompatible -s flag" {
    run bash -c "echo '' | uv run vtt_transcribe/main.py -s output.txt"
    
    [ "$status" -eq 2 ]
    [[ "$output" =~ "incompatible" ]] || [[ "$output" =~ "stdin" ]]
}

@test "stdin mode: rejects incompatible -o flag" {
    run bash -c "echo '' | uv run vtt_transcribe/main.py -o output.mp3"
    
    [ "$status" -eq 2 ]
    [[ "$output" =~ "incompatible" ]] || [[ "$output" =~ "stdin" ]]
}

@test "stdin mode: accepts diarization flag" {
    # Skip if HF_TOKEN not set
    if [[ -z "$HF_TOKEN" ]]; then
        skip "HF_TOKEN not set"
    fi
    
    run bash -c "cat '$TEST_AUDIO' | uv run vtt_transcribe/main.py --diarize --no-review-speakers --hf-token '$HF_TOKEN'"
    
    [ "$status" -eq 0 ]
    [[ "$output" =~ "SPEAKER" ]]
}
