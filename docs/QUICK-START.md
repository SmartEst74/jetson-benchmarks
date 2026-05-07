# Quick Start: Ternary-Bonsai on Jetson Orin Nano

## TL;DR: Just Works™

The Jetson is running Ternary-Bonsai-8B with full 65K context. The model:

```
✅ Generates at ~11.8 tok/s
✅ Uses 2.03 GB (tiny for an 8B model)
✅ Understands 65,536 tokens of context
✅ Auto-restarts with memory cleanup
✅ Speaks OpenAI API
```

**Test it:**

```bash
curl http://jetson-ip:8001/health
```

Should return `{"status":"ok"}`.

---

## Three Quick Commands

### 1. Check Status

```bash
# Is the service running?
sudo systemctl status jetson-bonsai-llm.service

# Is it healthy?
curl http://localhost:8001/health

# How much memory is it using?
ps aux | grep llama-server
free -h
```

### 2. Run a Completion

```bash
curl http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "ternary-bonsai-8b",
    "messages": [
      {"role": "user", "content": "Explain quantum computing in 50 words"}
    ],
    "temperature": 0.6,
    "max_tokens": 200
  }' | jq .choices[0].message.content
```

### 3. Check Performance

```bash
# Check generation speed (should show ~11.8 tok/s at end)
curl -s -w "\n" http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "ternary-bonsai-8b",
    "messages": [{"role": "user", "content": "Generate a 500-word essay on artificial intelligence."}],
    "max_tokens": 500
  }' 2>&1 | tail -5
```

---

## If Something Goes Wrong

### Model is Slow (< 10 tok/s)

1. **Check GPU clock**:
   ```bash
   nvidia-smi  # Should show GPU at 1020 MHz
   
   # If not, set MAXN_SUPER mode:
   sudo nvpmodel -m 2
   sudo jetson_clocks
   ```

2. **Check if CPU is overloaded**:
   ```bash
   top -bn1 | head -10  # Look for CPU usage
   ```

### Model Crashes (Connection refused)

1. **Restart the service**:
   ```bash
   sudo systemctl restart jetson-bonsai-llm.service
   ```

2. **Check logs**:
   ```bash
   sudo journalctl -u jetson-bonsai-llm.service -f
   ```

3. **Manual recovery** (if stuck):
   ```bash
   sudo fuser -k 8001/tcp
   sudo systemctl restart jetson-bonsai-llm.service
   ```

### Out of Memory (OOM)

1. **Check memory**:
   ```bash
   free -h
   # If swap is maxed out, the model crashed:
   sudo systemctl restart jetson-bonsai-llm.service
   ```

2. **Reduce context size** (if persistent):
   ```bash
   # Stop the service
   sudo systemctl stop jetson-bonsai-llm.service
   
   # Lower context
   export CTX=32768
   
   # Restart
   sudo systemctl start jetson-bonsai-llm.service
   ```

---

## Performance by Context Size

| Context | KV Cache | Speed | Memory | Use Case |
|---------|----------|-------|--------|----------|
| 8,192 | 350 MB | ~12.5 tok/s | Tighter | Speed-focused |
| 16,384 | 600 MB | ~12.2 tok/s | Balanced | **Recommended** |
| 32,768 | 1.3 GB | ~12.0 tok/s | Generous | Long documents |
| **65,536** | **2.6 GB** | **~11.8 tok/s** | **Full** | **Current** |

**All speeds measured on MAXN_SUPER GPU mode (1020 MHz).**

---

## API Examples

### Python (OpenAI-compatible)

```python
from openai import OpenAI

client = OpenAI(
    api_key="unused",  # Model runs locally, no auth needed
    base_url="http://jetson-ip:8001/v1"
)

response = client.chat.completions.create(
    model="ternary-bonsai-8b",
    messages=[
        {"role": "user", "content": "What is a neural network?"}
    ],
    temperature=0.6,
    max_tokens=200
)

print(response.choices[0].message.content)
```

### Python (via requests)

```python
import requests

response = requests.post(
    "http://jetson-ip:8001/v1/chat/completions",
    json={
        "model": "ternary-bonsai-8b",
        "messages": [
            {"role": "user", "content": "Explain transformers"}
        ],
        "temperature": 0.6,
        "max_tokens": 200
    }
)

print(response.json()["choices"][0]["message"]["content"])
```

### JavaScript/Node.js

```javascript
const fetch = require('node-fetch');

async function chat(prompt) {
  const response = await fetch('http://jetson-ip:8001/v1/chat/completions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model: 'ternary-bonsai-8b',
      messages: [{ role: 'user', content: prompt }],
      temperature: 0.6,
      max_tokens: 200
    })
  });
  
  const data = await response.json();
  return data.choices[0].message.content;
}

chat("Hello!").then(console.log);
```

---

## Advanced: Custom Context Size

To use a different context size without editing systemd:

```bash
# Option 1: Environment variable
CTX=16384 sudo systemctl restart jetson-bonsai-llm.service

# Option 2: Edit systemd
sudo systemctl edit jetson-bonsai-llm.service
# Change: Environment="CTX=65536" to Environment="CTX=16384"
sudo systemctl daemon-reload
sudo systemctl restart jetson-bonsai-llm.service

# Verify
curl -s http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "ternary-bonsai-8b", "messages": [{"role": "user", "content": "x"}], "max_tokens": 1}' \
  | jq .
```

---

## Benchmarks & Validation

**Expected Results** (Ternary-Bonsai-8B, MAXN_SUPER mode):

| Metric | Value | Status |
|--------|-------|--------|
| Generation Speed | ~11.8 tok/s | ✅ |
| Prompt Speed | ~38 tok/s | ✅ |
| Memory Used | ~6.2 GB (at 65K ctx) | ✅ |
| Health Endpoint | `{"status":"ok"}` | ✅ |
| Thinking Capability | Full reasoning | ✅ |
| Max Context | 65,536 tokens | ✅ |

**Run the validation suite:**

```bash
# See docs/methodology.md for detailed measurement procedures
cd ~/jetson-benchmarks
./scripts/quick-speed-test.py  # Local speed test
./scripts/bench-roles-live.py  # Full role benchmark (24 tasks)
```

---

## For Developers

### Switching Models

```bash
# See what's available
ls -lh ~/models/llama-cache/

# Use the hot-swap API
curl -X POST http://localhost:8001/switch \
  -H "Content-Type: application/json" \
  -d '{"model": "Qwen3-4B"}'

# Manual: Edit /home/jetson/jetson-benchmarks/scripts/llm-switch.sh
# and restart the service
```

### Building From Source

If you want to modify llama.cpp:

```bash
cd ~/prism-llama
git pull
cmake --build build --target llama-server -j4
```

### Monitoring Long Runs

```bash
# Watch memory and temperature in real-time
while true; do
  clear
  echo "=== Memory Usage ==="
  free -h | grep -E "Mem|Swap"
  echo ""
  echo "=== GPU Temperature ==="
  nvidia-smi | grep GPU
  echo ""
  echo "=== Service Status ==="
  systemctl is-active jetson-bonsai-llm.service
  sleep 2
done
```

---

## Next Steps

1. **Beginner**: Read [docs/jetson-setup.md](jetson-setup.md) for detailed setup steps
2. **Intermediate**: See [docs/optimizations.md](optimizations.md) for tuning guides
3. **Advanced**: Check [docs/methodology.md](methodology.md) for measurement rigor
4. **Research**: View [BENCHMARKS.md](../BENCHMARKS.md) for role-based results

---

## Still Have Questions?

- **Setup issues**: See [docs/jetson-setup.md](jetson-setup.md#troubleshooting)
- **Performance**: Check [docs/optimizations.md](optimizations.md#safe-optimizations-to-explore-advanced)
- **Benchmarking**: Read [docs/methodology.md](methodology.md)
- **Repo structure**: Check [README.md](../README.md#platform-features)
