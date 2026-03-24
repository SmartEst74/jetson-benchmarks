#!/usr/bin/env bash
# serve_nanbeige_3b.sh — Serve Nanbeige4-3B-Thinking Q8_0 via llama.cpp on Jetson
# Based on production serve_qwen35_4b.sh pattern

set -euo pipefail

MODEL="/root/.cache/llama.cpp/Nanbeige4-3B-Thinking-Q8_0.gguf"
CONTAINER_NAME="nanbeige-3b"
IMAGE="ghcr.io/nvidia-ai-iot/llama_cpp:latest-jetson-orin"
PORT=8000

# Drop caches before model load
echo "Dropping caches..."
sudo sync && echo 3 | sudo tee /proc/sys/vm/drop_caches > /dev/null
sleep 2

# Stop any running model container
echo "Stopping existing containers..."
docker stop qwen35-4b qwen35-9b nanbeige-3b 2>/dev/null || true
docker rm qwen35-4b qwen35-9b nanbeige-3b 2>/dev/null || true
sleep 2

echo "Starting Nanbeige4-3B-Thinking Q8_0..."
docker run -d \
  --name "$CONTAINER_NAME" \
  --runtime nvidia \
  --network host \
  -v /home/jetson/models/llama-cache:/root/.cache/llama.cpp \
  "$IMAGE" \
  llama-server \
    --model "$MODEL" \
    --host 0.0.0.0 \
    --port "$PORT" \
    --ctx-size 8192 \
    --n-gpu-layers 999 \
    --flash-attn on \
    --mlock \
    --no-mmap \
    --parallel 1

echo "Waiting for server to start..."
for i in $(seq 1 60); do
  if curl -s http://localhost:$PORT/health | grep -q 'ok'; then
    echo "Nanbeige4-3B-Thinking Q8_0 is ready on port $PORT"
    exit 0
  fi
  sleep 2
done

echo "ERROR: Server failed to start within 120s"
docker logs "$CONTAINER_NAME" --tail 20
exit 1
