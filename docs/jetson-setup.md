# Jetson Orin Nano Setup Guide — From Fresh Flash to Running LLMs

This guide takes you from a freshly flashed Jetson to running your first LLM benchmark. No prior experience required.

---

## What You Need

- [NVIDIA Jetson Orin Nano Developer Kit](https://www.nvidia.com/en-us/autonomous-machines/embedded-systems/jetson-orin/)
- 8GB LPDDR5 RAM (comes with the kit)
- 64GB+ microSD card or NVMe SSD
- USB-C power supply (included)
- Ethernet cable or WiFi adapter
- Computer with SSH access

---

## Step 1: Flash JetPack 6.2

### Download JetPack

1. Go to [NVIDIA JetPack Downloads](https://developer.nvidia.com/embedded/jetpack)
2. Download **JetPack 6.2** for Jetson Orin Nano
3. Use [balenaEtcher](https://www.balena.io/etcher/) to flash to SD card

### First Boot

1. Insert SD card into Jetson
2. Connect power, Ethernet, and HDMI (for setup)
3. Follow NVIDIA setup wizard
4. Create user account (remember username/password)
5. Enable SSH when prompted

### Verify Installation

```bash
# SSH into your Jetson
ssh your-username@jetson-ip

# Check JetPack version
cat /etc/nv_tegra_release

# Check GPU
nvidia-smi

# Check RAM
free -h
```

Expected output:
```
# R36 (release), REVISION: 4.3
# 8GB total RAM
```

---

## Step 2: Install Docker with NVIDIA Runtime

Docker containers run LLMs without polluting your system.

```bash
# Install Docker
sudo apt-get update
sudo apt-get install -y docker.io

# Add yourself to docker group (no more sudo)
sudo usermod -aG docker $USER
newgrp docker

# Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# Verify NVIDIA runtime works
docker run --rm --runtime nvidia --gpus all nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi
```

Expected: GPU info displayed without errors.

---

## Step 3: Download the LLM Server Image

This image contains llama.cpp optimized for Jetson.

```bash
# Pull the pre-built image (contains llama-server)
docker pull ghcr.io/nvidia-ai-iot/llama_cpp:latest-jetson-orin

# Create model cache directory
mkdir -p ~/models/llama-cache
```

---

## Step 4: Download Your First Model

Start with a small, fast model to verify everything works.

```bash
# Download Qwen3-1.7B (1.7GB, fast, good for testing)
curl -L -o ~/models/llama-cache/Qwen3-1.7B-Q8_0.gguf \
  "https://huggingface.co/unsloth/Qwen3-1.7B-GGUF/resolve/main/Qwen3-1.7B-Q8_0.gguf"

# Verify download
ls -lh ~/models/llama-cache/
```

---

## Step 5: Run Your First Model

```bash
# Start the model server
docker run -d \
  --name llm-server \
  --runtime nvidia \
  --gpus all \
  -v ~/models/llama-cache:/models \
  -p 8000:8000 \
  ghcr.io/nvidia-ai-iot/llama_cpp:latest-jetson-orin \
  /usr/local/bin/llama-server \
  --model /models/Qwen3-1.7B-Q8_0.gguf \
  --host 0.0.0.0 \
  --port 8000 \
  --ctx-size 4096 \
  --n-gpu-layers 99 \
  --flash-attn on \
  --mlock \
  --no-mmap \
  --threads 4

# Wait for model to load (watch logs)
docker logs -f llm-server

# You'll see "llama server listening" when ready
# Press Ctrl+C to stop watching logs
```

---

## Step 6: Test the Model

### Option A: Using curl

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen3-1.7B-Q8_0.gguf",
    "messages": [{"role": "user", "content": "Hello! What are you?"}],
    "max_tokens": 100,
    "temperature": 0.6
  }'
```

### Option B: Using Python

```python
import requests
import json

response = requests.post(
    "http://localhost:8000/v1/chat/completions",
    json={
        "model": "Qwen3-1.7B-Q8_0.gguf",
        "messages": [{"role": "user", "content": "Hello! What are you?"}],
        "max_tokens": 100,
        "temperature": 0.6
    }
)

print(response.json()["choices"][0]["message"]["content"])
```

---

## Step 7: Run a Benchmark

```bash
# Clone this repository
git clone https://github.com/SmartEst74/jetson-benchmarks.git
cd jetson-benchmarks

# Run the speed benchmark
python3 scripts/quick-speed-test.py

# Run role benchmarks
python3 scripts/bench-roles-live.py
```

---

## Understanding the Commands

### What Each Flag Does

| Flag | Purpose | Recommended |
|------|---------|-------------|
| `--runtime nvidia` | Use NVIDIA GPU runtime | Required |
| `--gpus all` | Give container access to all GPUs | Required |
| `-v ~/models:/models` | Mount model directory | Required |
| `--ctx-size 4096` | Context window (tokens) | 2048-8192 |
| `--n-gpu-layers 99` | Offload all layers to GPU | 99 = all |
| `--flash-attn on` | Use flash attention | Always on |
| `--mlock` | Lock model in RAM | Prevents swap |
| `--no-mmap` | Don't memory-map model | Faster loading |
| `--threads 4` | CPU threads | 4 for 6-core |

### Why These Settings?

**Memory is the bottleneck.** The Jetson has 8GB shared between CPU and GPU. When the model is loaded, there's limited headroom for KV cache (the memory used during generation).

- `--flash-attn on`: Reduces memory usage by 30-50%
- `--mlock`: Prevents the model from being swapped to disk
- `--ctx-size 4096`: Balances memory usage vs. conversation length

---

## Common Issues

### "Out of memory" when loading

Your model is too large for the context size. Try:
```bash
--ctx-size 2048  # Reduce from 4096
```

### Slow generation (< 5 tok/s)

Check if the model fits in GPU memory:
```bash
# Watch GPU memory while model is running
watch -n 1 nvidia-smi
```

If GPU memory is full, the model is being offloaded to CPU (much slower).

### "Model not found" error

Check your model path:
```bash
docker exec llm-server ls /models/
```

The model file must be in `~/models/llama-cache/` (mounted as `/models` in container).

---

## Next Steps

1. **Try different models**: See [data/jetson-models.json](../data/jetson-models.json) for tested models
2. **Run benchmarks**: Use the scripts in `scripts/` to test performance
3. **Optimize settings**: See [docs/methodology.md](methodology.md) for tuning parameters
4. **Set up hot-swap**: Use [api/hot-swap.py](../api/hot-swap.py) to switch models for different tasks

---

## Getting Help

- **Issues**: https://github.com/SmartEst74/jetson-benchmarks/issues
- **NVIDIA Forums**: https://forums.developer.nvidia.com/c/agx-autonomous-machines/jetson-embedded-systems/
- **llama.cpp**: https://github.com/ggerganov/llama.cpp

---

*Last updated: 2026-03-24*