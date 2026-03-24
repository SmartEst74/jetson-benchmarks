#!/usr/bin/env bash
set -euo pipefail

API_URL="${API_URL:-http://localhost:8000/v1/chat/completions}"
MODEL="${MODEL:-qwen35-4b}"

tmp_json="$(mktemp)"
trap 'rm -f "$tmp_json"' EXIT

wget -qO- "$API_URL" \
  --header="Content-Type: application/json" \
  --post-data="{
    \"model\": \"$MODEL\",
    \"messages\": [{\"role\": \"user\", \"content\": \"Write a Python async task queue with priority, retry, and timeout support.\"}],
    \"temperature\": 0.6,
    \"max_tokens\": 512,
    \"stream\": false
  }" > "$tmp_json"

python3 - <<'PY' "$tmp_json"
import json, sys
with open(sys.argv[1]) as f:
    d = json.load(f)
t = d.get("timings", {})
msg = d.get("choices", [{}])[0].get("message", {})
print("generation_tok_s=%.2f" % t.get("predicted_per_second", 0.0))
print("prompt_tok_s=%.2f" % t.get("prompt_per_second", 0.0))
print("tokens=%d" % t.get("predicted_n", 0))
print("thinking=%s" % bool(msg.get("reasoning_content")))
PY
