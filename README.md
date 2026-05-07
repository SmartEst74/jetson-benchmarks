# Jetson Orin Nano LLM Guide

The definitive, measured benchmark platform for running LLMs on NVIDIA Jetson Orin Nano Super (8 GB). Every model listed here actually runs — or is predicted to run — on 8 GB of unified memory. No cloud models. No impossible configs. Real hardware. Real [agency-agents](https://github.com/msitarzewski/agency-agents) roles.

**[Quick Start](docs/QUICK-START.md)** · **[Getting Started](docs/GETTING-STARTED.md)** · **[Benchmark Results](BENCHMARKS.md)** · **[Agent Roles](ROLES.md)** · **[Setup Guide](docs/jetson-setup.md)** · **[Optimization Guide](docs/optimizations.md)** · **[Methodology](docs/methodology.md)**

## Quick Start: 3 Steps to Peak Performance

**New to this repo?** Start with [docs/GETTING-STARTED.md](docs/GETTING-STARTED.md) — it guides you based on your skill level.

1. **Beginner**: Follow [docs/jetson-setup.md](docs/jetson-setup.md) to get your Jetson running from a fresh flash.
2. **Deploy**: Use the production model (Ternary-Bonsai-8B) or [choose a different one](#current-champion-2026-03-24) based on your needs.
3. **Verify**: Run `curl http://jetson-ip:8001/health` to confirm the API is live.

**Already set up?** Jump to "[Getting the Most Out of Ternary-Bonsai](#getting-the-most-out-of-ternary-bonsai)" below.

## Why This Exists

Most Jetson guides copy desktop/server assumptions that fail on 8 GB unified memory. This repo documents what actually works, what fails, and why — backed by measured data, BFCL v4 scores, and a predicted performance model validated against hardware.

## Current Champion (2026-03-24)

| | |
|---|---|
| **Model** | Nanbeige4-3B-Thinking Q8_0 (3.9 GB) |
| **Speed** | 17.22 tok/s gen · ~100% BW efficiency |
| **BFCL v4** | 51.4 (highest of any Jetson-viable model) |
| **Architecture** | LLaMA (pure attention, optimal for Jetson) |
| **Runtime** | llama.cpp b8095, Docker container |
| **Power** | ~8W, 50-55°C GPU, minimal swap |
| **Thinking** | Deep thinker: uses reasoning_content field |

### Tested Models (11/23 complete)

| Model | Quant | GGUF | Gen tok/s | BFCL v4 | Status |
|-------|-------|------|-----------|---------|--------|
| **Granite-4.0-350m** | Q8_0 | 0.35 GB | **91.25** | 18.98 | ✅ Ultra-fast (too small for complex tasks) |
| **Qwen3-1.7B** | Q8_0 | 1.71 GB | **32.59** | 28.41 | ✅ Fast 1.7B |
| **xLAM-2-1b-fc-r** | Q8_0 | 1.53 GB | **32.11** | 30.44 | ✅ Fastest tool caller |
| **Arch-Agent-1.5B** | Q8_0 | 2.88 GB | **18.35** | 32.14 | ✅ Agent-optimized |
| **Nanbeige4-3B-Thinking** | Q8_0 | 3.9 GB | **17.22** | 51.4 | ✅ Champion: best BFCL + speed |
| **Hammer2.1-3b** | Q8_0 | 3.06 GB | **20.93** | 29.71 | ✅ Function calling specialist |
| **xLAM-2-3b-fc-r** | Q8_0 | 3.5 GB | **19.12** | 41.22 | ✅ 87.5% parallel FC |
| **Llama-3.2-3B-Instruct** | Q8_0 | 3.42 GB | **19.12** | 21.95 | ✅ Meta's compact 3B |
| **Qwen3.5-4B** | Q8_0 | 4.48 GB | **10.45** | 49.7 | ✅ Production default (DeltaNet arch) |
| **Qwen3.5-9B** | Q4_K_M | 5.3 GB | **10.44** | — | ✅ Backup (DeltaNet arch) |
| **Qwen3-8B** | Q5_K_M | 5.5 GB | **10.24** | 42.57 | ⚠️ OOM risk |
| **Ternary-Bonsai-8B** | Q2_0 | 2.03 GB | **11.8** | — | ✅ 1.58-bit ternary (PrismML fork required) |
| **Qwen3.5-35B-A3B** | IQ3_XXS | 12.18 GB | 0.18 | — | ❌ Rejected (swap thrash) |

### Architecture Matters: The Efficiency Story

On memory-bandwidth-constrained Jetson (68 GB/s), **architecture efficiency matters more than parameter count**:

| Architecture | Efficiency | Example | Speed | Why |
|-------------|-----------|---------|-------|-----|
| **Pure LLaMA** | ~100% | Nanbeige4-3B (3B) | **17.22 tok/s** | Simple attention, GPU-optimized |
| **Ternary (1.58-bit)** | ~100%* | Ternary-Bonsai-8B (8B) | **11.8 tok/s** | {-1,0,+1} weights, 2.03 GB — but needs PrismML fork |
| **Standard Transformer** | ~89% | Qwen3-8B (8B) | 10.24 tok/s | Minor overhead from grouped attention |
| **Hybrid DeltaNet** | 69-87% | Qwen3.5-4B (4B) | 10.45 tok/s | Gated recurrent state updates |
| **Sparse MoE** | ~1% | Qwen3.5-35B (35B) | 0.18 tok/s | Expert routing forces CPU offload |

> **Key insight**: A 3B LLaMA model runs **65% faster** than a 4B DeltaNet model despite being only 7% smaller. Architecture dominates on 8GB.

> *Ternary note: requires PrismML's llama.cpp fork for Q2_0 ternary kernel support — not in mainline llama.cpp. See [docs/jetson-setup.md](docs/jetson-setup.md#ternary-models-prismml-fork).

### What's Next

Remaining models being tested (12/23):

| Model | BFCL v4 | Predicted tok/s | Why it matters |
|-------|---------|-----------------|----------------|
| Gemma-3-4b-it | 19.62 | ~10.4 | Google's multimodal 4B |
| MiniCPM3-4B | 25.55 | ~10.4 | Compact 4B with FC |
| xLAM-2-8b-fc-r | 46.68 | ~9.4 | Best 8B tool caller |
| BitAgent-Bounty-8B | 46.23 | ~9.4 | 93% Multiple FC |
| ToolACE-2-8B | 42.44 | ~9.4 | Strong simple FC |
| Llama-3.1-8B-Instruct | 25.83 | ~9.4 | Meta's workhorse 8B |
| Granite-3.2-8B-Instruct | 26.87 | ~9.4 | IBM's enterprise 8B |
| Command-R7B | 32.07 | ~10.4 | Best web search (27%) |
| CoALM-8B | 26.81 | ~9.4 | Academic fine-tune |
| Falcon3-7B-Instruct | 24.03 | ~10.4 | Perfect parallel FC (100%) |
| Qwen3-14B | 41.03 | ~7.8 | Tight fit, deep reasoning |
| Phi-4 | 28.79 | ~7.8 | Microsoft's 14B, MIT license |

See the full **[benchmark results](BENCHMARKS.md)** with measured data, role-based tests, and BFCL sub-scores.

---

## Getting the Most Out of Ternary-Bonsai

### The Production Setup (What We Use)

```bash
# All of this is automated via systemd on the Jetson
llama-server \
  --model /models/Ternary-Bonsai-8B-Q2_0.gguf \
  --ctx-size 65536 \
  --cache-type-k q4_0 \
  --cache-type-v q4_0 \
  --n-gpu-layers 999 \
  --flash-attn on \
  --mlock \
  --no-mmap \
  --parallel 1 \
  --port 8001
```

This is **65536 tokens of context** — the model's full native capability. It uses:
- **2.03 GB model** (ternary Q2_0 weights: {−1, 0, +1})
- **~2.6 GB KV cache** at full context
- **~1.5 GB system overhead**
- **~11.8 tok/s generation** on MAXN_SUPER mode (GPU at 1020 MHz)

### For Different Use Cases

#### 🚀 Maximum Performance (Expert)
**Goal**: Squeeze every tok/s out of the hardware.

**Context**: 8192 tokens (reduces KV cache to ~350 MB, frees ~2GB)
```bash
CTX=8192 ./scripts/start-ternary-bonsai.sh
```
**Performance**: ~12.5 tok/s (slightly faster due to smaller KV)
**Best For**: Fast inference, short conversations, embedded systems

#### 🎯 Balanced (Beginner → Intermediate)
**Goal**: Good speed + reasonable context for most tasks.

**Context**: 16384 tokens (KV cache ~600 MB)
```bash
CTX=16384 ./scripts/start-ternary-bonsai.sh
```
**Performance**: ~12.2 tok/s, ~1.6GB KV cache
**Best For**: Production deployments, coding tasks, most real-world uses

#### 📚 Maximum Context (Research/Long Documents)
**Goal**: Process long conversations, entire documents, extended reasoning.

**Context**: 65536 tokens (KV cache ~2.6 GB — **this is the current production default**)
```bash
CTX=65536 ./scripts/start-ternary-bonsai.sh
```
**Performance**: ~11.8 tok/s, ~2.6GB KV cache
**Best For**: Extended reasoning, document Q&A, multi-turn conversations, this is the **production baseline**

### Memory Management: The Secret Sauce

The Jetson has **8GB unified memory**. This is split between:
- Model weights (2.03 GB)
- KV cache (0.3–2.6 GB depending on context size)
- System + OS (1.5 GB)
- Free headroom (1–3 GB)

**If the model crashes or seems to use a lot of memory**, the problem is usually:

1. **Not freed after previous run**: The systemd service automatically handles this via ExecStartPre. To manually recover:
   ```bash
   sudo systemctl stop jetson-bonsai-llm.service
   sudo sync && echo 3 | sudo tee /proc/sys/vm/drop_caches >/dev/null
   sudo swapoff -a && sudo swapon -a  # Hard cycle swap
   sudo systemctl start jetson-bonsai-llm.service
   ```

2. **Context size too large**: If you see OOM with 65536 tokens, try 32768 or 16384:
   ```bash
   CTX=32768 ./scripts/start-ternary-bonsai.sh
   ```

3. **Stale process on port 8001**: Kill it and restart:
   ```bash
   sudo fuser -k 8001/tcp
   sudo systemctl restart jetson-bonsai-llm.service
   ```

### Performance Tuning: What Actually Matters

| Lever | Impact | Trade-off |
|-------|--------|----------|
| **GPU clock (MAXN_SUPER)** | 🟢 +65% | Thermals (62°C sustained) |
| **Context size (8K → 65K)** | 🟡 −2% (speed) | +2.6GB KV memory |
| **KV cache quant (q4_0)** | 🟢 Stable | No speed improvement |
| **Flash attention** | 🟢 Enables 65K context | Included by default |
| **Parallel slots** | 🔴 Not recommended | (Causes OOM) |

**Bottom line**: The MAXN_SUPER power mode is the **only lever that increases speed**. Everything else is about context size vs. memory trade-offs.

### Verify It's Working

```bash
# Check service is active
sudo systemctl status jetson-bonsai-llm.service

# Check health endpoint
curl http://127.0.0.1:8001/health

# Check memory usage
free -h

# Test a completion (should return ~11.8 tok/s)
curl -s http://127.0.0.1:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "ternary-bonsai-8b", "messages": [{"role": "user", "content": "Say hello in 10 words"}], "temperature": 0.6, "max_tokens": 100}' | jq .
```

### Advanced: Why TurboQuant Isn't Used

You might expect TurboQuant 2-bit KV cache here. We tested it:
- **Issue**: Ternary-Bonsai-8B's Prism build (b1-d104cf1) doesn't expose true 2-bit KV types
- **Fallback**: We use `q4_0` for both K and V caches (best available)
- **Result**: Fully stable, no regression in speed or memory vs. q4_1/q5_0
- **Validated**: Benchmarked 4 KV profiles; q4_0/q4_0 was fastest and most stable

If you're using a different llama.cpp build that supports true 2-bit KV, you can enable it:
```bash
--cache-type-k q2_0 --cache-type-v q2_0  # Only if your build supports it
```

---

## Platform Features

### Role-Based Benchmarks (`roles/` + `data/agent-roles.json`)

Eight real roles from [agency-agents](https://github.com/msitarzewski/agency-agents) (MIT license), each with 3 domain-specific benchmark tasks:

| Role | Division | Tasks | What It Tests |
|------|----------|-------|--------------|
| 🖥️ Frontend Developer | Engineering | 3 | React, CSS, perf optimization |
| 🏗️ Backend Architect | Engineering | 3 | DB schemas, rate limiters, event systems |
| 👁️ Code Reviewer | Engineering | 3 | Security review, perf review, shell safety |
| 🔒 Security Engineer | Engineering | 3 | STRIDE analysis, API hardening |
| 📚 Technical Writer | Engineering | 3 | READMEs, API docs, tutorials |
| 🤖 AI Engineer | Engineering | 3 | Edge inference, RAG, eval frameworks |
| ⏱️ Performance Benchmarker | Testing | 3 | Load tests, analysis reports |
| 🔌 API Tester | Testing | 3 | Test suites, contract tests |

Each task has a weighted 5-dimension grading rubric. See [ROLES.md](ROLES.md) for full details.

### Live Benchmark Results

Measured on real Jetson hardware — see [BENCHMARKS.md](BENCHMARKS.md) for full tables:
- **Qwen3.5-4B Q8_0**: 10.45 tok/s gen, 301 tok/s prompt (8 roles, perfectly consistent)
- **Thinking mode**: Model uses `<think>` blocks — needs 2048+ tokens for full output
- **No-think mode**: Direct responses without reasoning overhead

### Hot-Swap API (`api/hot-swap.py`)

HTTP API that switches the active model based on agent role:

```bash
curl -X POST http://jetson:8001/api/switch \
  -H 'Content-Type: application/json' \
  -d '{"role": "tool_caller"}'
```

The Jetson runs one model at a time (8 GB constraint). The API trades a ~10s model switch for optimal task performance. See [api/README.md](api/README.md).

### Performance Prediction Model

For untested models, we predict generation speed:

```
predicted_tok_s = (68 GB/s ÷ GGUF_size_GB) × 0.69
```

- 68 GB/s = measured LPDDR5 bandwidth
- 0.69 = bandwidth efficiency factor (validated: 10.5/(68/4.48) = 0.69)
- See [docs/methodology.md](docs/methodology.md) for full methodology

## Repo Structure

```
├── BENCHMARKS.md         Benchmark results (GitHub Markdown)
├── ROLES.md              Agent role documentation
├── ROADMAP.md            Test roadmap and plan
├── api/                  Hot-swap API server + docs
├── data/
│   ├── jetson-models.json   49 Jetson-viable models with BFCL scores
│   ├── agent-roles.json     8 roles × 3 tasks = 24 benchmarks with rubrics
│   └── test-roadmap.json    5-phase prioritized test plan
├── docs/                 Methodology, model selection, optimizations
├── roles/                Real agency-agents role definitions (MIT)
│   ├── engineering-frontend-developer.md
│   ├── engineering-backend-architect.md
│   ├── engineering-code-reviewer.md
│   ├── engineering-security-engineer.md
│   ├── engineering-technical-writer.md
│   ├── engineering-ai-engineer.md
│   ├── testing-performance-benchmarker.md
│   └── testing-api-tester.md
├── scripts/              Benchmark runners and model switch scripts
│   ├── bench-roles-live.py   Live role benchmark (v1)
│   └── bench-roles-v2.py     Dual-mode benchmark (thinking + no_think)
└── web/                  (Legacy) Interactive HTML pages
```

## Quick Start

```bash
# Start production default (Qwen3.5-4B Q8_0)
./scripts/start-qwen35-4b.sh

# Run standard benchmark
./scripts/bench-chat.sh

# Run custom role benchmarks
./scripts/bench-role.sh coder
./scripts/bench-role.sh all --output results/$(date +%Y-%m-%d)

# Start hot-swap API
python3 api/hot-swap.py --port 8001
```

## Safety & Host Policy

- Container-first: all LLM runtimes run in Docker (no host Ollama/llama.cpp)
- No `curl | bash` installers. All downloads are explicit and checksum-able.
- Every script change is PR-reviewed before merge.
- JetPack 6.2 base system kept clean.

## Contribute

Submit your device config + benchmark logs. Read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a PR.

## Sources

- BFCL v4: [Berkeley Function Calling Leaderboard](https://gorilla.cs.berkeley.edu/leaderboard.html) (commit f7cf735, 2025-12-16)
- Qwen3.5 scores: model cards
- Full citation list: [docs/sources.md](docs/sources.md) · [data/sources.json](data/sources.json)
\n# Updated by Jonathan Smart (jonathan.smart@outlook.com)
\n# Contributor list: Jonathan Smart (jonathan.smart@outlook.com)
\n# Author: Jonathan Smart (jonathan.smart@outlook.com)
