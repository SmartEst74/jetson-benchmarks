#!/usr/bin/env bash
set -euo pipefail

MODEL_PATH="${MODEL_PATH:-/home/jetson/models/llama-cache/Qwen3.5-4B-Q8_0.gguf}"
MODEL_BASENAME="$(basename "$MODEL_PATH")"
PORT="${PORT:-8000}"
CTX="${CTX:-8192}"
THREADS="${THREADS:-6}"
IMAGE="${IMAGE:-ghcr.io/nvidia-ai-iot/llama_cpp:latest-jetson-orin}"

if [[ ! -f "$MODEL_PATH" ]]; then
  echo "Model file not found: $MODEL_PATH" >&2
  exit 1
fi

sudo docker stop qwen35-4b >/dev/null 2>&1 || true
sudo docker rm qwen35-4b >/dev/null 2>&1 || true
sudo sync
echo 3 | sudo tee /proc/sys/vm/drop_caches >/dev/null

exec sudo docker run --rm --name qwen35-4b \
  --runtime nvidia \
  --network host \
  -v /home/jetson/models/llama-cache:/models \
  -v /home/jetson/models/slot-cache:/slot-cache \
  "$IMAGE" \
  llama-server \
    --model "/models/$MODEL_BASENAME" \
    --ctx-size "$CTX" \
    --n-gpu-layers 999 \
    --flash-attn on \
    --parallel 1 \
    --mlock \
    --no-mmap \
    --cache-type-k q8_0 \
    --cache-type-v q8_0 \
    --threads "$THREADS" \
    --slot-save-path /slot-cache \
    --host 0.0.0.0 \
    --port "$PORT"
