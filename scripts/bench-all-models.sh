#!/usr/bin/env bash
# bench-all-models.sh — Run speed benchmark on all available GGUF models
# Usage: bash bench-all-models.sh
#
# Stops current model, starts each in turn, runs speed test, records results.
# Restores production model (4B) when done.

set -euo pipefail

MODELS_DIR="/home/jetson/models/llama-cache"
IMAGE="ghcr.io/nvidia-ai-iot/llama_cpp:latest-jetson-orin"
PORT=8000
RESULTS_DIR="/tmp/bench-all-models"
mkdir -p "$RESULTS_DIR"

# Models to test (name:gguf_file)
declare -A MODELS
MODELS=(
  ["Qwen3.5-4B-Q8_0"]="Qwen3.5-4B-Q8_0.gguf"
  ["Qwen3.5-9B-Q4_K_M"]="unsloth_Qwen3.5-9B-GGUF_Qwen3.5-9B-Q4_K_M.gguf"
  ["Qwen3-8B-Q5_K_M"]="Qwen3-8B-Q5_K_M.gguf"
  ["Nanbeige4-3B-Thinking-Q8_0"]="Nanbeige4-3B-Thinking-Q8_0.gguf"
)

# Order matters: test from smallest to largest
ORDER=("Nanbeige4-3B-Thinking-Q8_0" "Qwen3.5-4B-Q8_0" "Qwen3.5-9B-Q4_K_M" "Qwen3-8B-Q5_K_M")

stop_all() {
    echo "Stopping all model containers..."
    docker stop qwen35-4b qwen35-9b nanbeige-3b bench-model 2>/dev/null || true
    docker rm qwen35-4b qwen35-9b nanbeige-3b bench-model 2>/dev/null || true
    sleep 3
}

start_model() {
    local name="$1"
    local gguf="${MODELS[$name]}"
    local model_path="/root/.cache/llama.cpp/$gguf"

    echo ""
    echo "============================================"
    echo "Starting: $name ($gguf)"
    echo "============================================"

    # Drop caches
    sudo sync && echo 3 | sudo tee /proc/sys/vm/drop_caches > /dev/null
    sleep 2

    docker run -d \
      --name bench-model \
      --runtime nvidia \
      --network host \
      -v "$MODELS_DIR:/root/.cache/llama.cpp" \
      "$IMAGE" \
      llama-server \
        --model "$model_path" \
        --host 0.0.0.0 \
        --port "$PORT" \
        --ctx-size 4096 \
        --n-gpu-layers 999 \
        --flash-attn on \
        --mlock \
        --no-mmap \
        --parallel 1

    # Wait for ready
    echo "Waiting for $name to load..."
    for i in $(seq 1 90); do
        if curl -s "http://localhost:$PORT/health" | grep -q 'ok'; then
            echo "$name is ready!"
            return 0
        fi
        sleep 2
    done
    echo "ERROR: $name failed to start"
    docker logs bench-model --tail 20
    return 1
}

run_speed_test() {
    local name="$1"
    echo "Running speed test for $name..."
    python3 /tmp/quick-speed-test.py 512 > "$RESULTS_DIR/${name}.json" 2>&1
    cat "$RESULTS_DIR/${name}.json"
}

echo "=== Multi-Model Jetson Benchmark ==="
echo "Date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "Models: ${#ORDER[@]}"
echo ""

ALL_RESULTS="[]"

for name in "${ORDER[@]}"; do
    gguf="${MODELS[$name]}"
    if [ ! -f "$MODELS_DIR/$gguf" ]; then
        echo "SKIP: $name — GGUF not found: $gguf"
        continue
    fi

    stop_all
    if start_model "$name"; then
        # Warmup run
        echo "Warmup..."
        python3 /tmp/quick-speed-test.py 64 > /dev/null 2>&1 || true
        sleep 2

        # Actual test
        run_speed_test "$name"
    fi

    docker stop bench-model 2>/dev/null || true
    docker rm bench-model 2>/dev/null || true
done

# Restore production model
echo ""
echo "============================================"
echo "Restoring production model (Qwen3.5-4B Q8_0)"
echo "============================================"
stop_all
# Use the existing systemd service / serve script
if command -v systemctl &>/dev/null && systemctl is-enabled qwen35-llm.service 2>/dev/null; then
    sudo systemctl start qwen35-llm.service
    echo "Production model restored via systemd"
else
    echo "NOTE: Restart production model manually (~/serve_qwen35_4b.sh or ~/llm-switch.sh 4b)"
fi

echo ""
echo "=== All Results ==="
echo "Saved to: $RESULTS_DIR/"
ls -la "$RESULTS_DIR/"
