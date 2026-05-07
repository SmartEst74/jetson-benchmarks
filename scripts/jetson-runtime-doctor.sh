#!/usr/bin/env bash
set -euo pipefail

JETSON_HOST="${JETSON_HOST:-localhost}"
API_PORT="${API_PORT:-8001}"
LLM_PORT="${LLM_PORT:-8000}"
SWITCH_SCRIPT="${SWITCH_SCRIPT:-./scripts/llm-switch.sh}"
TEST_ALIAS="${TEST_ALIAS:-qwen35-4b}"

if [[ "$JETSON_HOST" != "localhost" ]]; then
  echo "This script is intended to run on the Jetson host."
  echo "Current JETSON_HOST=$JETSON_HOST"
  exit 1
fi

run_check() {
  local name="$1"
  shift
  echo "[check] $name"
  if "$@"; then
    echo "[ok] $name"
  else
    echo "[fail] $name"
    return 1
  fi
}

run_check "docker available" command -v docker >/dev/null
run_check "curl available" command -v curl >/dev/null
run_check "switch script exists" test -x "$SWITCH_SCRIPT"

if ! sudo docker info >/dev/null 2>&1; then
  echo "[fail] docker daemon or permissions"
  echo "Run with a user that can sudo docker commands."
  exit 1
fi

echo "[step] switch to test alias: $TEST_ALIAS"
"$SWITCH_SCRIPT" "$TEST_ALIAS"

echo "[step] verify llama server health"
if ! curl -fsS "http://127.0.0.1:${LLM_PORT}/health" >/dev/null; then
  echo "[fail] llama health endpoint unavailable on port ${LLM_PORT}"
  exit 1
fi

echo "[step] verify hot-swap API status"
if ! curl -fsS "http://127.0.0.1:${API_PORT}/api/status" >/tmp/jetson-hot-swap-status.json; then
  echo "[fail] hot-swap API unavailable on port ${API_PORT}"
  exit 1
fi

if ! grep -q '"model"' /tmp/jetson-hot-swap-status.json; then
  echo "[fail] invalid status response"
  cat /tmp/jetson-hot-swap-status.json
  exit 1
fi

echo "[ok] Jetson runtime checks passed"
echo "Status payload:"
cat /tmp/jetson-hot-swap-status.json
