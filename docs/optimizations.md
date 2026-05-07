# Optimization Guide: Getting the Most Out of 8GB Jetson Memory

## Production Baseline

This configuration is **validated on real hardware** with zero regressions:

```bash
--ctx-size 65536              # Full model context (65K tokens)
--flash-attn on               # Enables memory-efficient attention
--cache-type-k q4_0           # Quantized KV cache (K matrix)
--cache-type-v q4_0           # Quantized KV cache (V matrix)
--n-gpu-layers 999            # Offload all layers to GPU
--parallel 1                  # Single inference slot (multi-slot causes OOM)
--mlock                       # Lock model in physical RAM (prevent swapping)
--no-mmap                     # Disable memory mapping (consistent perf)
--cache-ram 0                 # Don't use RAM cache layer
```

**Why Each Flag Matters on 8GB:**

| Flag | What It Does | Impact | Why |
|------|--------------|--------|-----|
| `--ctx-size 65536` | Full context window | 2.6 GB KV cache (at max) | Model's native limit; enables long documents/reasoning |
| `--flash-attn on` | Memory-efficient attention | −30% KV memory | Enables 65K context without OOM |
| `--cache-type-k q4_0` | Quantize K cache | −75% memory (vs. f16) | 8GB can't support unquantized KV at 65K tokens |
| `--cache-type-v q4_0` | Quantize V cache | −75% memory (vs. f16) | Critical for large context on constrained hardware |
| `--n-gpu-layers 999` | All layers on GPU | +100% speed | Jetson GPU is fast; CPU offload is 10x slower |
| `--parallel 1` | Single slot | Fits in memory | 2+ slots = OOM (each slot = full KV cache) |
| `--mlock` | Pin model in RAM | Prevents NVMe thrashing | Without it, model partially swaps to disk (10-100x slower) |
| `--no-mmap` | No memory mapping | Stable perf, predictable | Consistent generation speed across runs |

## System Guardrails (Automatic)

These are handled by systemd service on production Jetson:

```bash
Power Mode:        MAXN_SUPER (nvpmodel -m 2 + jetson_clocks)
GPU Clock:         1020 MHz (max performance)
CPU Affinity:      Cores isolated for model server
Memory Preflight:  ExecStartPre hook runs on every service start
LimitMEMLOCK:      infinity (allows full model pinning)
OOMScoreAdjust:    -1000 (protect model process from OOM killer)
```

**Memory Preflight (What Runs Automatically Before Model Starts):**

```bash
# 1. Kill any lingering process on port 8001
fuser -k 8001/tcp

# 2. Sync buffers and drop all caches
sync && echo 3 | tee /proc/sys/vm/drop_caches >/dev/null

# 3. Hard cycle swap (clears stale swap entries)
swapoff -a && swapon -a
```

This ensures maximum free memory before each model restart.

## Context Size vs. Performance Trade-off

**The trade-off is pure memory, not speed:**

```
Context Size    KV Cache    Total Memory    Gen Speed    Use Case
8,192 tokens    ~350 MB     ~3.8 GB         ~12.5 tok/s  Short tasks, fastest
16,384 tokens   ~600 MB     ~4.1 GB         ~12.2 tok/s  Balanced (recommended)
32,768 tokens   ~1.3 GB     ~5.3 GB         ~12.0 tok/s  Long documents
65,536 tokens   ~2.6 GB     ~6.2 GB         ~11.8 tok/s  Extended reasoning (prod)
```

**No speed regression.** Going from 8K to 65K context costs only 200ms per generation (~1.8% slower).

## KV Cache Quantization: Why q4_0?

We tested 4 KV quantization profiles on real hardware:

| Profile | Gen tok/s | KV Memory (65K ctx) | Stability | Notes |
|---------|-----------|-------------------|-----------|-------|
| **q4_0** | **11.83** | **2.6 GB** | ✅ Rock solid | **CHOSEN** — fastest, most stable |
| q4_1 | 11.79 | 2.7 GB | ✅ Good | Marginal difference (no benefit) |
| q5_0 | 11.75 | 3.3 GB | ✅ Good | Uses more memory for same quality |
| iq4_nl | 11.71 | 2.6 GB | ⚠️ Edge cases | Occasionally stalls on large context |

**TurboQuant (true 2-bit KV)**: Not available in this Prism build. q4_0 is the best available equivalent and performs identically.

## Safe Optimizations to Explore (Advanced)

These have been identified but not yet validated to improve speed without regression:

- **Thread count tuning** (`--threads 5,6`): Test if CPU threads affect generation speed (currently fixed at model process defaults)
- **Batch size optimization**: Currently `parallel 1`; can we do 2+ slots if we reduce context to 16K?
- **RoPE scaling above 65K**: If you need >65K context, test if YaRN scaling works cleanly (model was trained on 65K; going higher is experimental)
- **CPU pinning**: Bind llama-server to specific cores to reduce context switching

**Decision rule:** Only deploy changes that improve speed AND maintain coding/tool quality metrics on role benchmarks.

## What NOT to Change

**These are proven to break or regress performance:**

- ❌ `--parallel > 1`: Causes OOM (each slot needs full KV cache)
- ❌ Disabling `--mlock`: Model swaps to NVMe, loses 10-100x speed
- ❌ `--cache-type-k f16`: Unquantized KV at 65K = immediate OOM
- ❌ Disabling `--flash-attn`: Can't fit 65K context without it
- ❌ Reducing `--n-gpu-layers` below 99: Moves compute to slow ARM CPU

## Memory Leak Diagnosis

If memory usage grows over time:

1. **Check if it's the model process or OS cache:**
   ```bash
   free -h
   ps aux | grep llama-server
   ```

2. **If llama-server is eating >3GB despite 2GB model:**
   - KV cache is growing (expected at high context)
   - Or: Multiple models running (check `systemctl status jetson-bonsai-llm.service`)

3. **If OS buffers are growing:**
   - This is normal; `drop_caches` will clear it
   - Systemd runs this automatically every service restart

4. **If swap is being used heavily:**
   - `--mlock` isn't working (check: `cat /proc/meminfo | grep Mlocked`)
   - Or: Model is larger than expected (check GGUF file size)

## Next Steps

**For beginners:** Stick with the production baseline. It's tuned and tested.

**For researchers:** See [benchmarks/current-performance.md](../benchmarks/current-performance.md) for detailed measurements.

**For developers:** Check [scripts/start-ternary-bonsai.sh](../scripts/start-ternary-bonsai.sh) for how to override individual settings.
