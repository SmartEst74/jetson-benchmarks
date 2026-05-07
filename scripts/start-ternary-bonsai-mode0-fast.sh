#!/usr/bin/env bash
set -euo pipefail

# Strict mode-0 (15W) fast profile for aggregate throughput at large context.
# This profile is tuned for total system throughput using 4 parallel slots.
# Single-stream speed in strict mode-0 is ~7.2 tok/s; aggregate can exceed 20 tok/s.

MODEL_PATH="${MODEL_PATH:-$HOME/models/llama-cache/Ternary-Bonsai-8B-Q2_0.gguf}"
PRISM_DIR="${PRISM_DIR:-$HOME/prism-llama}"
PORT="${PORT:-8001}"
ALIAS="${ALIAS:-ternary-bonsai-8b}"
THREADS="${THREADS:-6}"
CTX="${CTX:-8192}"
NP="${NP:-4}"
BATCH="${BATCH:-2048}"
UBATCH="${UBATCH:-256}"

if [[ ! -x "$PRISM_DIR/build/bin/llama-server" ]]; then
  echo "Missing llama-server at $PRISM_DIR/build/bin/llama-server" >&2
  exit 1
fi
if [[ ! -f "$MODEL_PATH" ]]; then
  echo "Missing model at $MODEL_PATH" >&2
  exit 1
fi

echo "Applying strict mode 0 + max clocks within mode 0..."
sudo nvpmodel -m 0
sudo jetson_clocks
GPU_MAX=$(cat /sys/devices/platform/bus@0/17000000.gpu/devfreq/17000000.gpu/max_freq)
echo "Mode: $(sudo nvpmodel -q | tr '\n' ' ')"
echo "GPU max freq: ${GPU_MAX}"

echo "Stopping existing server on port ${PORT}..."
fuser -k "${PORT}/tcp" 2>/dev/null || true
pkill -f "llama-server.*${PORT}" 2>/dev/null || true

echo "Starting Ternary-Bonsai mode-0 fast profile..."
exec env LD_LIBRARY_PATH="$PRISM_DIR/build/bin" \
  "$PRISM_DIR/build/bin/llama-server" \
    --model "$MODEL_PATH" \
    --alias "$ALIAS" \
    --host 0.0.0.0 \
    --port "$PORT" \
    --threads "$THREADS" \
    -ngl 999 \
    -fa on \
    --mlock \
    --no-mmap \
    --ctx-size "$CTX" \
    -ctk q4_0 \
    -ctv q4_0 \
    -b "$BATCH" \
    -ub "$UBATCH" \
    -np "$NP"
