# Benchmark Results

## Ternary-Bonsai-8B Q2_0 (Ternary Model) — Verified 2026-05-05

This model uses **1.58-bit ternary weights** ({-1, 0, +1}), stored as Q2_0 GGUF with group size 128.
Based on Qwen3-8B (8.19B params), trained by [PrismML](https://huggingface.co/prism-ml/Ternary-Bonsai-8B-gguf).
Requires the [PrismML llama.cpp fork](https://github.com/PrismML-Eng/llama.cpp) — not in mainline llama.cpp.

### Speed (llama-server API, flash-attn on, -ngl 999)

| Mode | GPU Clock | Prompt tok/s | Generation tok/s | Notes |
|------|---:|---:|---:|---|
| CPU-only (-ngl 0) | — | 4.8 | 3.9 | Prior CLI test |
| **GPU** | **~1020 MHz (MAXN)** | **171–205** | **12.12** | Verified 2026-05-05, 3-run median |
| GPU | 612 MHz (15W) | 122–126 | 7.4 | 2026-05-06 tuning session |

> **GPU frequency is the dominant performance lever** — see [Optimization Findings](#optimization-findings-2026-05-06) below.

- **Generation (MAXN)**: 12.12 tok/s median (3 runs, BST prompt, 512 tokens)
- **Prompt (cold)**: 171–205 tok/s on first request
- **Prompt (warm)**: ~11.6 tok/s when KV cache reuses context

### Role Benchmark Results (8 roles × think + no_think, max_tokens=4096)

| Role | Think gen tok/s | Think response | No-Think gen tok/s | No-Think response | Finish |
|------|---:|---:|---:|---:|---|
| frontend_developer   | 11.82 | 10 704 ch | 11.87 | 9 302 ch | stop |
| backend_architect    | 11.93 |  7 546 ch | 11.91 | 7 565 ch | stop |
| code_reviewer        | 11.98 |  5 117 ch | 11.80 | 7 407 ch | stop |
| security_engineer    | 11.70 |  7 877 ch | 11.62 | 8 272 ch | stop |
| technical_writer     | 10.99 |  1 643 ch | 10.12 | 4 344 ch | stop |
| ai_engineer          |  4.95¹|  9 152 ch | 11.91 | 6 962 ch | stop |
| performance_benchmarker | 11.90 | 7 814 ch | 11.96 | 6 301 ch | length |
| api_tester           | 11.91 |  8 890 ch | 11.90 | 7 667 ch | length |
| **Median** | **11.88** | | **11.89** | | |

¹ *ai_engineer think mode ran on ctx=8192 server before restart; anomalous due to near-context-limit pressure. Subsequent runs at ctx=4096 show normal 11.9 tok/s.*

**Thinking mode**: Ternary-Bonsai-8B Q2_0 does not produce `reasoning_content` via the PrismML fork — `/think` and `/no_think` prefixes are accepted but generate identical direct responses (0 thinking chars in all tests).

### Hardware During Generation (tegrastats, MAXN mode, 2026-05-05)

| Metric | Value |
|--------|---------|
| RAM used | 5 036–5 037 MB / 7 607 MB (66%) |
| Swap used | 0 MB |
| GPU utilization | 96–99% |
| GPU temp | 65.0–65.5 °C |
| CPU temp | ~62 °C |
| Total power | ~17.2 W |
| CPU+GPU+CV power | ~8.5 W |
| Server RSS | ~4 678 MB |

### Theoretical Analysis

- **Model size**: 2.18 GB (Q2_0 ternary)
- **Memory bandwidth**: 68 GB/s unified (CPU/GPU shared)
- **Theoretical max** (2.18 GB / 68 GB/s): ~**31 tok/s**
- **15W / 612 MHz**: 7.4 / 31 = **24%** bandwidth efficiency
- **MAXN / ~1020 MHz**: 12.1 / 31 = **39%** bandwidth efficiency
- **Comparison to Qwen3.5-4B Q8_0** (10.5 tok/s): Ternary-Bonsai-8B is **+15% faster** with 2× params at half the disk footprint

### Reproduce

```bash
# (Optional) Enable MAXN_SUPER for peak performance — on Jetson:
sudo nvpmodel -m 2

# Server (on Jetson via start script)
bash scripts/start-ternary-bonsai.sh

# Tunnel (local)
ssh -f -N -L 8001:localhost:8001 jetson@192.168.1.163

# Benchmark
python3 scripts/bench-ternary-bonsai.py --out /tmp/tb-results
```

### Notes
- GPU gives **3× gen speedup** and **44× prompt speedup** over CPU-only
- 15W boot state (default) limits GPU to 612 MHz → ~7 tok/s; `sudo nvpmodel -m 2` needed for 12+ tok/s
- Ternary models require the PrismML fork — see [docs/jetson-setup.md](../docs/jetson-setup.md#ternary-models-prismml-fork)
- `ctx-size 8192` with `-ctk q4_0 -ctv q4_0` KV is safe (no OOM); fp16 KV at 8192 causes crash

---

## Optimization Findings (2026-05-06)

### GPU Frequency: The Primary Performance Driver

nvpmodel power mode controls GPU clock — the single largest performance lever:

| nvpmodel Mode | GPU Max Freq | Estimated Gen Speed | How to Enable |
|---|---:|---:|---|
| 0 — 15W (default after boot) | 612 MHz | ~7 tok/s | (current default) |
| 1 — 25W | 918 MHz | ~11 tok/s | `sudo nvpmodel -m 1` |
| 2 — MAXN_SUPER (no cap) | 1020 MHz | ~12-13 tok/s | `sudo nvpmodel -m 2` |

The 2026-05-05 benchmarks were captured in MAXN_SUPER mode (~1020 MHz, 17.2W). After reboot the default 15W mode reduces speed ~40%.

**To restore peak performance on Jetson:**
```bash
sudo nvpmodel -m 2          # MAXN_SUPER — persists across reboots
# Optionally lock all clocks to maximum:
sudo jetson_clocks
```

### Software Flag Tests (2026-05-06, 15W, 612 MHz GPU)

All results are within measurement noise — performance is hardware-frequency-bound:

| Config | Ctx | KV | Gen tok/s | Notes |
|--------|----:|----|----------:|-------|
| baseline (`-fa on`) | 4096 | fp16 | 7.37 | Reference |
| `--mlock --no-mmap` | 4096 | fp16 | 7.37 | No gain at 612 MHz |
| `--mlock --no-mmap -ctk q8_0 -ctv q8_0` | 4096 | q8_0 | 7.20 | Marginal regression |
| `--mlock --no-mmap -ctk q4_0 -ctv q4_0` | 4096 | q4_0 | 7.18 | Marginal regression |
| `--mlock --no-mmap -ctk q4_0 -ctv q4_0` | **8192** | q4_0 | 7.18 | **8K ctx without OOM ✓** |
| above + `-b 2048 -ub 256` | 8192 | q4_0 | 7.18 | Batch tuning: no gain |
| No flash attention | 4096 | fp16 | 7.39 | FA on/off: no difference |

**Key finding**: The `--mlock --no-mmap` technique from the [Codacus video](https://www.youtube.com/watch?v=8F_5pdcD3HY) shows large gains for CPU-offloaded or mmap-paged models. Here the model is fully on-GPU with unified memory already wired. KV `q4_0` enables **8K context without OOM** — a useful capability gain even without a speed improvement.

### Path to 20 tok/s

1. **Enable MAXN_SUPER** (`sudo nvpmodel -m 2`) → ~12-13 tok/s baseline
2. **At MAXN, retest** `--mlock --no-mmap` and KV quantization (may differ at 1020 MHz)
3. **Investigate PrismML kernel efficiency** — ternary dequant kernels may be optimizable
4. **Consider Q4_K format** (if PrismML adds support) — more bandwidth-efficient than ternary Q2_0

---

## Qwen3.5-9B Q4_K_M (Current Production)

### Token Generation
- **Prompt processing**: 47 tok/s (21ms/token)
- **Generation**: 8.8 tok/s (113ms/token)
- **Theoretical max**: 12.8 tok/s (5.3GB / 68 GB/s bandwidth)
- **Efficiency**: 69% of bandwidth limit

### During Generation (tegrastats)
- GPU utilization: 83-99% @ 1015 MHz
- GPU temp: ~60°C (well within limits)
- RAM: 7232/7607 MB (95%)
- Swap: 1199 MB used
- Power: ~21W

### Analysis
- 113ms per token breakdown:
  - Theoretical minimum (bandwidth): 78ms (5.3GB / 68 GB/s)
  - Actual overhead: 35ms (45% overhead above minimum)
  - Sources: CUDA kernel launch, DeltaNet recurrence, memory access patterns
  - GPU not always 100% → some CPU-bound work between GPU dispatches

## Qwen3.5-35B-A3B IQ3_XXS (Testing)

### Predictions
- Model size: 12.18 GB (5.25 GB will overflow to swap)
- Active weight read per token: ~1.4 GB (MoE optimization)
- If MoE-optimized (only active experts read):
  - Theoretical: 1.4GB / 68 GB/s = 20.6ms = 48 tok/s
  - With 45% overhead: ~33 tok/s
- If dense-read (all weights read per token):
  - In-RAM portion: 6.93 GB at 68 GB/s = 102ms
  - Swap portion: 5.25 GB at 779 MB/s = 6.7s (!!!)
  - Total: ~6.8s per token = 0.15 tok/s (unusable)
- Reality will be somewhere in between depending on expert caching

### Key Variables
1. Does llama.cpp b8095 do MoE-optimized reads? (only active experts)
2. How does unified memory handle page faults for swapped experts?
3. Does --mmap help or hurt with MoE on unified memory?
4. Can --cpu-moe help if some experts are in swap?
