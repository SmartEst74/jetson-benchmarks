#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-status}"
CONTAINER_NAME="llm-server"
CACHE_DIR="${CACHE_DIR:-/home/jetson/models/llama-cache}"
DOCKER_IMAGE="${DOCKER_IMAGE:-ghcr.io/nvidia-ai-iot/llama_cpp:latest-jetson-orin}"
SERVER_PORT="${SERVER_PORT:-8000}"
STARTUP_TIMEOUT_SEC="${STARTUP_TIMEOUT_SEC:-120}"

# Model mapping: alias -> filename pattern
declare -A MODELS=(
  ["qwen35-4b"]="Qwen3.5-4B-Q8_0.gguf"
  ["qwen35-9b"]="Qwen3.5-9B-Q4_K_M.gguf"
  ["nanbeige4-3b"]="Nanbeige4-3B-Thinking-Q8_0.gguf"
  ["qwen3-8b"]="Qwen3-8B-Q5_K_M.gguf"
  ["xlam-2-1b"]="xLAM-2-1B-fc-r-Q8_0.gguf"
  ["qwen3-1.7b"]="Qwen3-1.7B-Q8_0.gguf"
  ["arch-agent-1.5b"]="Arch-Agent-1.5B.gguf"
  ["granite-4.0-350m"]="granite-4.0-350m-Q8_0.gguf"
  ["hammer2.1-3b"]="hammer2.1-3b-q8_0.gguf"
  ["xlam-2-3b"]="xLAM-2-3B-fc-r-Q8_0.gguf"
  ["llama-3.2-3b"]="Llama-3.2-3B-Instruct-Q8_0.gguf"
  ["arch-agent-3b"]="Arch-Agent-3B.gguf"
  ["gemma-3-4b"]="gemma-3-4b-it-q4_0.gguf"
  ["minicpm3-4b"]="minicpm3-4b-q4_k_m.gguf"
  ["qwen3-4b-2507"]="Qwen3-4B-Instruct-2507-Q8_0.gguf"
  # Tier 2 models (larger)
  ["xlam-2-8b"]="Llama-xLAM-2-8B-fc-r-Q4_K_M.gguf"
  ["hammer2.1-7b"]="Hammer2.1-7b-Q4_K_M.gguf"
  ["bitagent-8b"]="BitAgent-Bounty-8B.Q4_K_M.gguf"
  ["toolace-2-8b"]="ToolACE-2-8B.Q4_K_M.gguf"
  ["llama-3.1-8b"]="Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"
  ["granite-3.2-8b"]="granite-3.2-8b-instruct-Q4_K_M.gguf"
  ["command-r7b"]="c4ai-command-r7b-12-2024-Q4_K_M.gguf"
  ["coalm-8b"]="CoALM-8B.Q4_K_M.gguf"
  ["falcon3-7b"]="Falcon3-7B-Instruct-Q4_K_M.gguf"
  ["qwen3-14b"]="Qwen3-14B-Q3_K_M.gguf"
  ["phi-4"]="phi-4-Q3_K_M.gguf"
  ["gemma-3-12b"]="gemma-3-12b-it-Q3_K_M.gguf"
  ["ternary-bonsai-8b"]="Ternary-Bonsai-8B-Q2_0.gguf"
)

# Context size by tier
declare -A CTX_SIZES=(
  ["1"]=4096
  ["2"]=2048
  ["3"]=2048
  ["4"]=1024
)

declare -A MODEL_CTX_OVERRIDE=(
  ["ternary-bonsai-8b"]=8192
)

stop_all() {
  echo "Stopping all LLM containers..."
  sudo systemctl stop qwen35-llm.service 2>/dev/null || true
  sudo docker stop "$CONTAINER_NAME" 2>/dev/null || true
  sudo docker rm "$CONTAINER_NAME" 2>/dev/null || true
  # Also stop legacy containers
  sudo docker stop qwen35-4b qwen35-9b 2>/dev/null || true
  sudo docker rm qwen35-4b qwen35-9b 2>/dev/null || true
  sudo sync
  echo 3 | sudo tee /proc/sys/vm/drop_caches >/dev/null
  sleep 2
}

status_all() {
  echo "=== LLM Service Status ==="
  if systemctl is-active qwen35-llm.service >/dev/null 2>&1; then
    echo "qwen35-llm.service: ACTIVE"
  else
    echo "qwen35-llm.service: INACTIVE"
  fi
  
  echo ""
  echo "=== Docker Containers ==="
  if sudo docker ps -a --filter "name=$CONTAINER_NAME" --format "{{.Names}}: {{.Status}}" | grep -q "$CONTAINER_NAME"; then
    sudo docker ps -a --filter "name=$CONTAINER_NAME" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
  else
    echo "No $CONTAINER_NAME container found"
  fi
  
  echo ""
  echo "=== Memory Usage ==="
  free -h
  
  echo ""
  echo "=== GPU Temperature ==="
  cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null | awk '{printf "%.1f°C\n", $1/1000}' || echo "Temperature unavailable"
}

get_model_tier() {
  local model="$1"
  # Simple heuristic based on model size in filename
  if [[ "$model" == *"8b"* ]] || [[ "$model" == *"14b"* ]] || [[ "$model" == *"12b"* ]]; then
    echo "2"
  elif [[ "$model" == *"7b"* ]]; then
    echo "1"
  else
    echo "1"  # Default to tier 1 for small models
  fi
}

start_model() {
  local alias="$1"
  local filename="${MODELS[$alias]}"
  
  if [[ -z "$filename" ]]; then
    echo "Error: Unknown model alias '$alias'" >&2
    echo "Available models:" >&2
    for key in "${!MODELS[@]}"; do
      echo "  $key" >&2
    done
    return 1
  fi
  
  local model_path="$CACHE_DIR/$filename"
  if [[ ! -f "$model_path" ]]; then
    echo "Error: Model file not found: $model_path" >&2
    echo "Please download the model first." >&2
    return 1
  fi
  
  local tier=$(get_model_tier "$alias")
  local ctx_size="${MODEL_CTX_OVERRIDE[$alias]:-${CTX_SIZES[$tier]:-2048}}"
  
  echo "Starting $alias (tier $tier, ctx=$ctx_size)..."
  echo "Model: $model_path"
  
  stop_all
  
  # Calculate model size for memory estimation
  local size_gb=$(du -h "$model_path" | cut -f1)
  echo "Model size: $size_gb"
  
  # Start container
  sudo docker run -d \
    --name "$CONTAINER_NAME" \
    --runtime nvidia \
    --gpus all \
    -v "$CACHE_DIR:/models" \
    -p "$SERVER_PORT:8000" \
    "$DOCKER_IMAGE" \
    /usr/local/bin/llama-server \
    --model "/models/$filename" \
    --host 0.0.0.0 \
    --port 8000 \
    --ctx-size "$ctx_size" \
    --n-gpu-layers 99 \
    --flash-attn on \
    --mlock \
    --no-mmap \
    --threads 4
  
  echo "Waiting for model to load..."
  local deadline=$((SECONDS + STARTUP_TIMEOUT_SEC))
  local ready=0
  while (( SECONDS < deadline )); do
    if curl -fsS "http://localhost:${SERVER_PORT}/health" >/dev/null 2>&1; then
      ready=1
      break
    fi
    sleep 2
  done
  
  # Check if container is running
  if [[ "$ready" -eq 1 ]] && sudo docker ps --filter "name=$CONTAINER_NAME" --format "{{.Names}}" | grep -q "$CONTAINER_NAME"; then
    echo "✓ Model $alias started successfully"
    echo "API available at: http://$(hostname -I | awk '{print $1}'):${SERVER_PORT}"
    echo ""
    echo "Test with:"
    echo "  curl http://localhost:${SERVER_PORT}/v1/chat/completions \\" 
    echo "    -H 'Content-Type: application/json' \\"
    echo "    -d '{\"model\":\"$alias\",\"messages\":[{\"role\":\"user\",\"content\":\"Hello\"}],\"max_tokens\":50}'"
  else
    echo "✗ Failed to start model $alias" >&2
    sudo docker logs "$CONTAINER_NAME" 2>&1 | tail -20
    return 1
  fi
}

list_models() {
  echo "Available model aliases:"
  echo "========================"
  for alias in $(echo "${!MODELS[@]}" | tr ' ' '\n' | sort); do
    local filename="${MODELS[$alias]}"
    local tier=$(get_model_tier "$alias")
    local ctx_size="${MODEL_CTX_OVERRIDE[$alias]:-${CTX_SIZES[$tier]:-2048}}"
    local status="available"
    
    if [[ -f "$CACHE_DIR/$filename" ]]; then
      status="downloaded"
    fi
    
    printf "  %-20s %-40s tier=%s ctx=%s [%s]\n" "$alias" "$filename" "$tier" "$ctx_size" "$status"
  done
}

case "$MODE" in
  stop)
    stop_all
    status_all
    ;;
  status)
    status_all
    ;;
  list)
    list_models
    ;;
  qwen35-4b|qwen35-9b|nanbeige4-3b|qwen3-8b|xlam-2-1b|qwen3-1.7b|arch-agent-1.5b|granite-4.0-350m|hammer2.1-3b|xlam-2-3b|llama-3.2-3b|arch-agent-3b|gemma-3-4b|minicpm3-4b|qwen3-4b-2507|xlam-2-8b|hammer2.1-7b|bitagent-8b|toolace-2-8b|llama-3.1-8b|granite-3.2-8b|command-r7b|coalm-8b|falcon3-7b|qwen3-14b|phi-4|gemma-3-12b|ternary-bonsai-8b)
    start_model "$MODE"
    ;;
  *)
    echo "Usage: ./scripts/llm-switch.sh {status|stop|list|MODEL_ALIAS}" >&2
    echo "" >&2
    echo "Examples:" >&2
    echo "  ./scripts/llm-switch.sh status          # Check current status" >&2
    echo "  ./scripts/llm-switch.sh list            # List available models" >&2
    echo "  ./scripts/llm-switch.sh qwen35-4b       # Start Qwen3.5-4B" >&2
    echo "  ./scripts/llm-switch.sh nanbeige4-3b    # Start Nanbeige4-3B (champion)" >&2
    echo "  ./scripts/llm-switch.sh stop            # Stop all models" >&2
    echo "" >&2
    echo "Popular models:" >&2
    echo "  qwen35-4b      - Production default (4.48 GB, 10.5 tok/s)" >&2
    echo "  nanbeige4-3b   - Champion (3.9 GB, 17.2 tok/s)" >&2
    echo "  ternary-bonsai-8b - Ternary Bonsai Q2_0 (Prism build)" >&2
    echo "  qwen35-9b      - Backup (5.3 GB, 10.4 tok/s)" >&2
    echo "  qwen3-1.7b     - Fast 1.7B (1.71 GB, 32.6 tok/s)" >&2
    exit 1
    ;;
esac
