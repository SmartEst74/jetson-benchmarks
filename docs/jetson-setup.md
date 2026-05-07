# Jetson Orin Nano Setup Guide — From Fresh Flash to Production LLM

**Goal**: Get your Jetson running the production Ternary-Bonsai-8B model with full 65K context, automatic memory recovery, and ~11.8 tok/s generation speed.

**Time**: ~45 minutes (hardware shipping time not included)

**Skill level**: Beginner-friendly, but assumes SSH experience

**What you'll have at the end**:
- ✅ Jetson Orin Nano Super 8GB running JetPack 6.2
- ✅ Docker installed and configured for GPU access
- ✅ Ternary-Bonsai-8B model downloaded (2.03 GB)
- ✅ systemd service running on port 8001 (HTTP API)
- ✅ OpenAI-compatible chat endpoint ready
- ✅ Automatic memory recovery on service restart

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

## Step 7: Make It Production-Ready (Optional but Recommended)

This step converts your manual Docker setup into an auto-restarting systemd service with memory recovery.

### A. Move Repository to Standard Location

```bash
# Clone the jetson-benchmarks repo
git clone https://github.com/your-org/jetson-benchmarks.git ~/jetson-benchmarks
cd ~/jetson-benchmarks
```

### B. Install systemd Service

This service automatically restarts the model if it crashes and handles memory cleanup:

```bash
# Create the service file
sudo tee /etc/systemd/system/jetson-bonsai-llm.service > /dev/null <<EOF
[Unit]
Description=Jetson Bonsai LLM Server with Auto Memory Recovery
After=network.target

[Service]
Type=simple
User=jetson
WorkingDirectory=/home/jetson/jetson-benchmarks
ExecStartPre=/usr/local/sbin/jetson-bonsai-memory-prep.sh
ExecStart=/home/jetson/jetson-benchmarks/scripts/start-ternary-bonsai.sh
Restart=always
RestartSec=3
Environment="CTX=65536"
Environment="KV_K=q4_0"
Environment="KV_V=q4_0"
Environment="CACHE_RAM=0"
Environment="SLOT_SAVE_PATH=/home/jetson/models/slot-cache"
LimitMEMLOCK=infinity
OOMScoreAdjust=-1000

[Install]
WantedBy=multi-user.target
EOF

# Create memory recovery script
sudo tee /usr/local/sbin/jetson-bonsai-memory-prep.sh > /dev/null <<'EOF'
#!/bin/bash
set -e
echo "Preparing memory for model startup..."
fuser -k 8001/tcp 2>/dev/null || true
sync && printf 3 > /proc/sys/vm/drop_caches
swapoff -a && swapon -a
echo "Memory ready."
EOF

sudo chmod +x /usr/local/sbin/jetson-bonsai-memory-prep.sh

# Reload systemd and start the service
sudo systemctl daemon-reload
sudo systemctl enable jetson-bonsai-llm.service
sudo systemctl start jetson-bonsai-llm.service

# Verify it's running
sudo systemctl status jetson-bonsai-llm.service
```

### C. Verify the Service

```bash
# Check health
curl http://localhost:8001/health

# Check logs
sudo journalctl -u jetson-bonsai-llm.service -f

# Check memory usage
free -h

# Test a completion
curl -s http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "ternary-bonsai-8b",
    "messages": [{"role": "user", "content": "What is the Jetson Orin Nano?"}],
    "max_tokens": 100
  }' | jq .choices[0].message.content
```

### D. Configure Power Mode (MAXN_SUPER)

For maximum performance:

```bash
# Set maximum performance mode (uses ~15W)
sudo nvpmodel -m 2
sudo /usr/bin/jetson_clocks

# Verify GPU clock
nvidia-smi  # Should show GPU at 1020 MHz

# Make it persistent across reboot
echo "sudo /usr/bin/jetson_clocks" | sudo tee -a /etc/rc.local
```

### E. What Happens Automatically Now

Every time the service restarts (boot, crash recovery, manual restart):

1. **Memory prep runs** (ExecStartPre)
   - Kill any stale process on port 8001
   - Clear Linux page cache
   - Hard cycle swap

2. **Model starts** (ExecStart)
   - Loads 2.03 GB Ternary-Bonsai-8B model
   - Sets context to 65536 tokens (full model capability)
   - Pins model in RAM with `--mlock`
   - Enables flash attention for memory efficiency

3. **API ready** on `http://your-jetson-ip:8001`
   - Responds to `/health` checks
   - Serves OpenAI-compatible chat completions
   - Generates at ~11.8 tok/s

---

## Ternary Models (PrismML Fork) {#ternary-models-prismml-fork}

Ternary models like **Ternary-Bonsai-8B** store weights as {−1, 0, +1} in Q2_0 GGUF format.
Mainline llama.cpp does not support the ternary Q2_0 kernel — you need the
[PrismML fork](https://github.com/PrismML-Eng/llama.cpp).

### Why Not Mainline Docker?

The `ghcr.io/nvidia-ai-iot/llama_cpp` image uses mainline llama.cpp. Attempting to load a ternary Q2_0 model will silently fall back to CPU-only or error. You must build from the PrismML fork on-device.

### Step 1: Install CUDA Build Dependencies

```bash
ssh jetson@192.168.1.163

# Install nvcc (CUDA compiler) and cuBLAS development headers
sudo apt-get install -y cuda-compiler-12-6 libcublas-dev-12-6
```

### Step 2: Clone PrismML Fork and Build with CUDA

```bash
cd ~
git clone --depth 1 https://github.com/PrismML-Eng/llama.cpp prism-llama
cd prism-llama

# Configure — SM 8.7 = Orin Ampere, lld fixes GNU ld PLT bug on aarch64
export PATH=/usr/local/cuda-12.6/bin:$PATH

cmake -B build \
  -DGGML_CUDA=ON \
  -DGGML_NATIVE=ON \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_CUDA_COMPILER=/usr/local/cuda-12.6/bin/nvcc \
  -DCMAKE_CUDA_ARCHITECTURES=87 \
  -DCMAKE_EXE_LINKER_FLAGS="-fuse-ld=lld" \
  -DCMAKE_SHARED_LINKER_FLAGS="-fuse-ld=lld"

# Build — takes 30–60 min; most time spent on flash-attention CUDA kernels
cmake --build build --target llama-cli llama-server -j4
```

> **Why lld?** GNU `ld` generates a broken `_init` function in `libllama-common.so` on aarch64 for large shared objects (bad `BL` targets inside `.rela.plt`). LLVM's `lld` does not have this bug. Install with `sudo apt-get install -y lld`.

### Step 3: Download the Ternary Model

```bash
mkdir -p ~/models/llama-cache
wget -q --show-progress \
  -O ~/models/llama-cache/Ternary-Bonsai-8B-Q2_0.gguf \
  "https://huggingface.co/prism-ml/Ternary-Bonsai-8B-gguf/resolve/main/Ternary-Bonsai-8B-Q2_0.gguf"
# 2.03 GiB download
```

### Step 4: Quick Test

```bash
cd ~/prism-llama
LD_LIBRARY_PATH=build/bin build/bin/llama-cli \
  -m ~/models/llama-cache/Ternary-Bonsai-8B-Q2_0.gguf \
  -p "Explain ternary neural networks in 3 sentences." \
  -n 200 \
  -ngl 999 \
  -fa on \
  -t 6
```

Expected output includes:
```
ggml_cuda_init: found 1 CUDA devices (Total VRAM: 7607 MiB):
  Device 0: Orin, compute capability 8.7, ...
[ Prompt: 38.4 t/s | Generation: 11.8 t/s ]
```

### Step 5: Run as OpenAI-Compatible API Server

The PrismML `llama-server` exposes a fully OpenAI-compatible REST API on any port.

```bash
cd ~/prism-llama
LD_LIBRARY_PATH=build/bin build/bin/llama-server \
  --model ~/models/llama-cache/Ternary-Bonsai-8B-Q2_0.gguf \
  --alias ternary-bonsai-8b \
  --host 0.0.0.0 \
  --port 8001 \
  -ngl 999 \
  -fa on \
  -t 6 \
  --ctx-size 8192
```

Or use the convenience script:

```bash
~/prism-llama/scripts/start-ternary-bonsai.sh
```

The server is ready when you see:
```
llama server listening at http://0.0.0.0:8001
```

### Step 6: Use the API

**curl:**

```bash
curl http://192.168.1.163:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "ternary-bonsai-8b",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 200
  }'
```

**Python (openai SDK):**

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://192.168.1.163:8001/v1",
    api_key="none"
)

response = client.chat.completions.create(
    model="ternary-bonsai-8b",
    messages=[{"role": "user", "content": "What is a ternary neural network?"}],
    max_tokens=200
)
print(response.choices[0].message.content)
```

### Performance Summary

| Mode | Prompt | Generation |
|------|--------|------------|
| CPU-only | 4.8 tok/s | 3.9 tok/s |
| **GPU (ngl 999 + FA)** | **38.4 tok/s** | **11.8 tok/s** |

Model is 2.03 GB on disk, fits entirely in VRAM. No swap required.

### Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `Illegal instruction` on launch | GNU ld PLT bug in `libllama-common.so` | Rebuild with `-DCMAKE_SHARED_LINKER_FLAGS="-fuse-ld=lld"` |
| `error: unknown value for --flash-attn` | Old `llama-cli` stale binary | Ensure `LD_LIBRARY_PATH=build/bin` and that `build/bin/llama-cli` is the PrismML build |
| `ggml_cuda_init: no CUDA devices` | CUDA libs not found | `export LD_LIBRARY_PATH=build/bin` before running |
| Model generates garbage | Q2_0 ternary not dequantized correctly | Confirm you're using the PrismML fork, not mainline llama.cpp |



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