#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-8000}"
CTX="${CTX:-8192}"
IMAGE="${IMAGE:-ghcr.io/nvidia-ai-iot/llama_cpp:latest-jetson-orin}"

sudo docker stop qwen35-9b >/dev/null 2>&1 || true
sudo docker rm qwen35-9b >/dev/null 2>&1 || true
sudo sync
echo 3 | sudo tee /proc/sys/vm/drop_caches >/dev/null

exec sudo docker run --rm --name qwen35-9b \
  --runtime nvidia \
  --network host \
  -v /home/jetson/models/llama-cache:/root/.cache/llama.cpp \
  -v /home/jetson/models/slot-cache:/slot-cache \
  "$IMAGE" \
  llama-server \
    --hf-repo unsloth/Qwen3.5-9B-GGUF \
    --hf-file Qwen3.5-9B-Q4_K_M.gguf \
    --ctx-size "$CTX" \
    --n-gpu-layers 999 \
    --flash-attn on \
    --parallel 1 \
    --mlock \
    --no-mmap \
    --cache-type-k q8_0 \
    --cache-type-v q8_0 \
    --reasoning-format deepseek \
    --slot-save-path /slot-cache \
    --host 0.0.0.0 \
    --port "$PORT"
