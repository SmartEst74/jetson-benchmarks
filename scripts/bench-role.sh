#!/usr/bin/env bash
# bench-role.sh — Run all custom benchmark tasks for a specific agent role
#
# Usage:
#   ./scripts/bench-role.sh <role_id> [--model <model>] [--output <dir>]
#
# Examples:
#   ./scripts/bench-role.sh coder
#   ./scripts/bench-role.sh tool_caller --model "Qwen3.5-4B"
#   ./scripts/bench-role.sh all --output results/2026-03-24
#
# Reads task definitions from data/agent-roles.json and sends each prompt
# to the LLM API, capturing response + timing metadata.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
ROLES_JSON="$REPO_DIR/data/agent-roles.json"
API_URL="${LLM_API_URL:-http://192.168.1.23:8000/v1}"
OUTPUT_DIR="${BENCH_OUTPUT_DIR:-$REPO_DIR/results/$(date +%Y-%m-%d)}"
MODEL=""
MAX_TOKENS=2048
TEMPERATURE=0.6

usage() {
    echo "Usage: $0 <role_id|all> [--model <name>] [--output <dir>]"
    echo ""
    echo "Roles: coder, tool_caller, researcher, planner, writer, reviewer, all"
    exit 1
}

[[ $# -lt 1 ]] && usage

ROLE_ID="$1"
shift

while [[ $# -gt 0 ]]; do
    case "$1" in
        --model)  MODEL="$2"; shift 2 ;;
        --output) OUTPUT_DIR="$2"; shift 2 ;;
        *)        echo "Unknown arg: $1"; usage ;;
    esac
done

if ! command -v jq &>/dev/null; then
    echo "Error: jq is required. Install with: apt install jq"
    exit 1
fi

if [[ ! -f "$ROLES_JSON" ]]; then
    echo "Error: $ROLES_JSON not found"
    exit 1
fi

mkdir -p "$OUTPUT_DIR"

# Get current model from API if not specified
if [[ -z "$MODEL" ]]; then
    MODEL=$(curl -sf "$API_URL/models" 2>/dev/null | jq -r '.data[0].id // "unknown"') || MODEL="unknown"
fi

echo "=== Jetson Role Benchmark ==="
echo "Role:      $ROLE_ID"
echo "Model:     $MODEL"
echo "API:       $API_URL"
echo "Output:    $OUTPUT_DIR"
echo "Tokens:    $MAX_TOKENS"
echo ""

run_task() {
    local role="$1"
    local task_id="$2"
    local task_name="$3"
    local prompt="$4"
    local out_file="$OUTPUT_DIR/${role}_${task_id}.json"

    echo -n "  [$task_id] $task_name ... "

    local start_ns
    start_ns=$(date +%s%N)

    local response
    response=$(curl -sf "$API_URL/chat/completions" \
        -H "Content-Type: application/json" \
        -d "$(jq -n \
            --arg model "$MODEL" \
            --arg prompt "$prompt" \
            --argjson max_tokens "$MAX_TOKENS" \
            --argjson temperature "$TEMPERATURE" \
            '{
                model: $model,
                messages: [{role: "user", content: $prompt}],
                max_tokens: $max_tokens,
                temperature: $temperature
            }')" 2>&1) || {
        echo "FAIL (API error)"
        echo "{\"error\": \"API call failed\", \"task_id\": \"$task_id\"}" > "$out_file"
        return 1
    }

    local end_ns
    end_ns=$(date +%s%N)
    local elapsed_ms=$(( (end_ns - start_ns) / 1000000 ))

    local content
    content=$(echo "$response" | jq -r '.choices[0].message.content // "null"')
    local usage_tokens
    usage_tokens=$(echo "$response" | jq '.usage.completion_tokens // 0')
    local tok_per_sec
    if [[ $elapsed_ms -gt 0 && $usage_tokens -gt 0 ]]; then
        tok_per_sec=$(echo "scale=1; $usage_tokens * 1000 / $elapsed_ms" | bc 2>/dev/null || echo "0")
    else
        tok_per_sec="0"
    fi

    jq -n \
        --arg role "$role" \
        --arg task_id "$task_id" \
        --arg task_name "$task_name" \
        --arg model "$MODEL" \
        --arg prompt "$prompt" \
        --arg response "$content" \
        --argjson tokens "$usage_tokens" \
        --argjson elapsed_ms "$elapsed_ms" \
        --arg tok_per_sec "$tok_per_sec" \
        --arg timestamp "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        '{
            role: $role,
            task_id: $task_id,
            task_name: $task_name,
            model: $model,
            prompt: $prompt,
            response: $response,
            tokens: $tokens,
            elapsed_ms: $elapsed_ms,
            tok_per_sec: $tok_per_sec,
            timestamp: $timestamp
        }' > "$out_file"

    echo "OK (${usage_tokens} tokens, ${elapsed_ms}ms, ${tok_per_sec} tok/s)"
}

# Extract roles and tasks from JSON
if [[ "$ROLE_ID" == "all" ]]; then
    ROLE_IDS=$(jq -r '.roles[].id' "$ROLES_JSON")
else
    ROLE_IDS="$ROLE_ID"
    # Validate role exists
    if ! jq -e ".roles[] | select(.id == \"$ROLE_ID\")" "$ROLES_JSON" > /dev/null 2>&1; then
        echo "Error: Unknown role '$ROLE_ID'"
        echo "Available: $(jq -r '.roles[].id' "$ROLES_JSON" | tr '\n' ' ')"
        exit 1
    fi
fi

TOTAL=0
PASS=0

for rid in $ROLE_IDS; do
    role_name=$(jq -r ".roles[] | select(.id == \"$rid\") | .name" "$ROLES_JSON")
    echo "--- $role_name ($rid) ---"

    task_count=$(jq ".roles[] | select(.id == \"$rid\") | .tasks | length" "$ROLES_JSON")
    for i in $(seq 0 $((task_count - 1))); do
        task_id=$(jq -r ".roles[] | select(.id == \"$rid\") | .tasks[$i].id" "$ROLES_JSON")
        task_name=$(jq -r ".roles[] | select(.id == \"$rid\") | .tasks[$i].name" "$ROLES_JSON")
        prompt=$(jq -r ".roles[] | select(.id == \"$rid\") | .tasks[$i].prompt" "$ROLES_JSON")
        TOTAL=$((TOTAL + 1))
        if run_task "$rid" "$task_id" "$task_name" "$prompt"; then
            PASS=$((PASS + 1))
        fi
    done
    echo ""
done

echo "=== Results: $PASS/$TOTAL tasks completed ==="
echo "Output: $OUTPUT_DIR/"
echo ""
echo "Next: python3 scripts/collect-results.py $OUTPUT_DIR"
