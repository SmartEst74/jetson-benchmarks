#!/usr/bin/env bash
# Start Ternary-Bonsai-8B as an OpenAI-compatible API server using PrismML llama.cpp.
# Requires ~/prism-llama to be built first — see docs/jetson-setup.md#ternary-models-prismml-fork
#
# PERFORMANCE NOTE: For best throughput, run this first (requires root):
#   sudo nvpmodel -m 2      # MAXN_SUPER: removes GPU frequency cap (612→1020 MHz)
# Without this, generation speed is ~7 tok/s. With MAXN_SUPER it is ~12 tok/s.
# Target of 20 tok/s requires MAXN_SUPER mode — see benchmarks/current-performance.md
set -euo pipefail

MODEL_PATH="${MODEL_PATH:-$HOME/models/llama-cache/Ternary-Bonsai-8B-Q2_0.gguf}"
PORT="${PORT:-8001}"
CTX="${CTX:-65536}"
THREADS="${THREADS:-6}"
PRISM_DIR="${PRISM_DIR:-$HOME/prism-llama}"
ALIAS="${ALIAS:-ternary-bonsai-8b}"
APPLY_MAX_CLOCKS="${APPLY_MAX_CLOCKS:-1}"
RECOVER_MEMORY="${RECOVER_MEMORY:-1}"
KV_K="${KV_K:-q4_0}"
KV_V="${KV_V:-q4_0}"
CACHE_RAM="${CACHE_RAM:-0}"

if [[ ! -f "$MODEL_PATH" ]]; then
  echo "Model not found: $MODEL_PATH" >&2
  echo "Download with:" >&2
  echo "  wget -O \"$MODEL_PATH\" 'https://huggingface.co/prism-ml/Ternary-Bonsai-8B-gguf/resolve/main/Ternary-Bonsai-8B-Q2_0.gguf'" >&2
  exit 1
fi

LLAMA_SERVER="$PRISM_DIR/build/bin/llama-server"
if [[ ! -x "$LLAMA_SERVER" ]]; then
  echo "PrismML llama-server not built: $LLAMA_SERVER" >&2
  echo "Build with: cd $PRISM_DIR && cmake --build build --target llama-server -j4" >&2
  exit 1
fi

if [[ "$APPLY_MAX_CLOCKS" == "1" ]]; then
  echo "Applying MAXN_SUPER clocks (sudo nvpmodel -m 2 && sudo jetson_clocks)..."
  sudo nvpmodel -m 2
  sudo jetson_clocks
fi

GPU_MAX_FREQ=$(cat /sys/devices/platform/bus@0/17000000.gpu/devfreq/17000000.gpu/max_freq 2>/dev/null || echo "unknown")
echo "GPU max freq: ${GPU_MAX_FREQ}"

if [[ "$RECOVER_MEMORY" == "1" ]]; then
  echo "Stopping any existing server and reclaiming memory..."
  fuser -k "${PORT}/tcp" 2>/dev/null || true
  sleep 1
  sudo sync
  echo 3 | sudo tee /proc/sys/vm/drop_caches >/dev/null
  sudo swapoff -a || true
  sudo swapon -a || true
fi

echo "Starting Ternary-Bonsai-8B on port $PORT ..."
echo "  Model : $MODEL_PATH"
echo "  Alias : $ALIAS"
echo "  Ctx   : $CTX tokens"
echo "  GPU   : all layers (-ngl 999), flash-attn on"
echo "  Mem   : --mlock --no-mmap (avoids swap, contiguous allocation)"
echo "  KV    : -ctk $KV_K -ctv $KV_V"
echo ""
echo "OpenAI API endpoint: http://0.0.0.0:$PORT/v1"
echo ""

exec env LD_LIBRARY_PATH="$PRISM_DIR/build/bin" \
  "$LLAMA_SERVER" \
    --model      "$MODEL_PATH" \
    --alias      "$ALIAS" \
    --host       0.0.0.0 \
    --port       "$PORT" \
    --ctx-size   "$CTX" \
    --threads    "$THREADS" \
    -ngl         999 \
    -fa          on \
    -ctk         "$KV_K" \
    -ctv         "$KV_V" \
    --mlock \
    --no-mmap \
    --cache-ram  "$CACHE_RAM"

