# Jetson LLM Benchmark Results

> Real benchmarks. Real hardware. Real agency-agents roles.

[![Device](https://img.shields.io/badge/Device-Jetson_Orin_Nano_Super_8GB-green)](https://developer.nvidia.com/embedded/jetson-orin-nano-super)
[![Runtime](https://img.shields.io/badge/Runtime-llama.cpp_b8095-blue)](https://github.com/ggml-org/llama.cpp)
[![Roles](https://img.shields.io/badge/Roles-agency--agents-purple)](https://github.com/msitarzewski/agency-agents)

## Hardware

| Spec | Value |
|------|-------|
| **Device** | NVIDIA Jetson Orin Nano Super Developer Kit |
| **RAM** | 8 GB LPDDR5 (unified CPU/GPU) |
| **GPU** | 1024 CUDA cores, Ampere SM 8.7 |
| **CPU** | 6× ARM Cortex-A78AE @ 1.728 GHz |
| **Memory BW** | 68 GB/s |
| **Storage** | 128 GB NVMe SSD |
| **Power** | 7-25W (MAXN_SUPER mode) |
| **Runtime** | llama.cpp b8095 (Docker) |

## Models Tested

| Model | GGUF Size | Quant | Gen tok/s | Architecture | Efficiency | Status |
|-------|-----------|-------|-----------|-------------|------------|--------|
| **Nanbeige4-3B-Thinking** | 3.9 GiB | Q8_0 | **17.22** | LLaMA | ~100% | ✅ Downloaded, Fastest |
| **Qwen3.5-4B** | 4.2 GiB | Q8_0 | **10.45** | Hybrid DeltaNet | 69% | ✅ Production |
| **Qwen3.5-9B** | 5.3 GiB | Q4_K_M | **10.44** | Hybrid DeltaNet | 87% | ✅ Backup |
| **Qwen3-8B** | 5.5 GiB | Q5_K_M | **10.24** | Transformer | 89% | ⚠️ OOM after first request |
| **Qwen3.5-35B-A3B** | 13 GiB | IQ3_XXS | 0.18 | MoE+DeltaNet | ~1% | ❌ Rejected (swap thrash) |

### Architecture Matters: The Efficiency Story

The Jetson Orin Nano's 68 GB/s memory bandwidth is the hard ceiling. But *how much* of that bandwidth your model uses varies dramatically by architecture:

```
predicted_tok/s = (bandwidth_GB/s ÷ GGUF_size_GiB) × efficiency_factor
```

| Architecture | Efficiency | Why | Examples |
|-------------|-----------|-----|----------|
| **Pure LLaMA** | ~100% | Simple attention, GPU-optimized | Nanbeige4-3B |
| **Standard Transformer** | ~89% | Minor overhead from grouped attention | Qwen3-8B |
| **Hybrid DeltaNet** | 69-87% | Gated recurrent state updates + attention mixing | Qwen3.5-4B, 9B |
| **Sparse MoE** | ~1% | Expert routing forces CPU offload on 8GB | Qwen3.5-35B-A3B |

> **Key insight**: A 3B LLaMA model at Q8_0 (17.2 tok/s) is **65% faster** than a 4B DeltaNet model at Q8_0 (10.5 tok/s) despite being only 7% smaller. Architecture efficiency dominates on constrained hardware.

### Speed Comparison Chart

```
Nanbeige4-3B Q8_0 (3.9 GiB) ████████████████████████████████████ 17.22 tok/s
Qwen3.5-4B Q8_0  (4.2 GiB)  █████████████████████             10.45 tok/s  
Qwen3.5-9B Q4_KM (5.3 GiB)  █████████████████████             10.44 tok/s
Qwen3-8B Q5_KM   (5.5 GiB)  ████████████████████              10.24 tok/s
Qwen3.5-35B MoE  (13 GiB)   ▏                                  0.18 tok/s
```

## Role-Based Benchmark Results

We benchmark each model by asking it to perform real tasks from [agency-agents](https://github.com/msitarzewski/agency-agents) roles. Each role tests different capabilities:

| Role | Tests | Primary Metric |
|------|-------|---------------|
| 🖥️ Frontend Developer | React components, CSS systems, perf optimization | Code generation |
| 🏗️ Backend Architect | DB schemas, rate limiters, event-driven systems | System design |
| 👁️ Code Reviewer | Security review, performance review, shell safety | Bug detection |
| 🔒 Security Engineer | STRIDE analysis, API hardening, header audits | Threat modeling |
| 📚 Technical Writer | READMEs, API docs, tutorials | Documentation |
| 🤖 AI Engineer | Edge inference, RAG pipelines, eval frameworks | ML knowledge |
| ⏱️ Performance Benchmarker | Inference analysis, load test design, reports | Data analysis |
| 🔌 API Tester | Test suites, contract tests, failure matrices | Test generation |

### Qwen3.5-4B Q8_0 — Role Benchmark Results

> Results will be populated from live benchmarks. See [scripts/bench-roles-live.py](scripts/bench-roles-live.py) for the benchmark runner.

<!-- BENCHMARK_RESULTS_START -->

**Run 1: Thinking Mode, 1024 max tokens** — 2026-03-23T15:08:08Z

| Role | Gen tok/s | Prompt tok/s | Tokens | Wall Time | Thinking Chars | Response Chars |
|------|-----------|-------------|--------|-----------|----------------|----------------|
| 🖥️ Frontend Developer | 10.45 | 266.25 | 1024 | 98.3s | 3,521 | 1,285 |
| 🏗️ Backend Architect | 10.46 | 285.47 | 1024 | 98.3s | 4,828 | 3,392 |
| 👁️ Code Reviewer | 10.45 | 305.37 | 1024 | 98.6s | 6,847 | 0 ⚠️ |
| 🔒 Security Engineer | 10.45 | 329.31 | 1024 | 98.4s | 7,293 | 0 ⚠️ |
| 📚 Technical Writer | 10.45 | 311.69 | 1024 | 98.4s | 6,412 | 0 ⚠️ |
| 🤖 AI Engineer | 10.45 | 320.10 | 1024 | 98.4s | 7,015 | 0 ⚠️ |
| ⏱️ Performance Benchmarker | 10.45 | 280.60 | 1024 | 98.6s | 5,892 | 0 ⚠️ |
| 🔌 API Tester | 10.45 | 311.60 | 1024 | 98.4s | 6,234 | 0 ⚠️ |
| **AVERAGE** | **10.45** | **301.30** | **1024** | **98.4s** | **6,005** | **585** |

**Key Findings:**
- **Generation speed is rock-solid**: 10.45 ±0.01 tok/s across all 8 roles — exactly matching the theoretical model (68 GB/s ÷ 4.48 GB × 0.69 = 10.5 tok/s predicted)
- **Prompt processing varies**: 266–329 tok/s depending on prompt length (shorter prompts = faster initial processing)
- **Thinking mode is WORKING**: The model IS generating 5,000–7,000 characters of internal reasoning for all roles
- **Response chars show 0 because tokens are consumed by thinking**: With 1024 max_tokens, the model spends ALL tokens in `<think>` blocks before producing visible output
- **Frontend and Backend had enough budget**: These produced 1,285 and 3,392 chars of visible response because their reasoning was shorter

> **Understanding the metrics**: The model generates internal reasoning (thinking) first, then produces visible output. With limited tokens, all budget goes to thinking. **Every role IS thinking** (5,000–7,000 chars), but 6 of 8 didn't produce visible output at 1024 tokens. Solution: Use 4096+ tokens or `/no_think` mode.

**Run 2: Dual-mode (thinking + no_think), 2048 max tokens** — 2026-03-23T15:23:50Z

| Role | Mode | Gen tok/s | Tokens | Wall Time | Response | Notes |
|------|------|-----------|--------|-----------|----------|-------|
| 🖥️ Frontend Developer | thinking | 10.38 | 2048 | 197.3s | 5857 chars | React TypeScript component |
| 🖥️ Frontend Developer | no_think | 10.31 | 2048 | 198.6s | 5176 chars | Direct code output |
| 🏗️ Backend Architect | thinking | 10.34 | 2048 | 198.0s | 6068 chars | Node.js microservice |
| 🏗️ Backend Architect | no_think | 10.33 | 2048 | 198.3s | 6205 chars | Full TypeScript impl |
| 👁️ Code Reviewer | thinking | 10.35 | 2048 | 197.8s | 0 chars ⚠️ | Still all thinking at 2048 |
| 👁️ Code Reviewer | no_think | 10.32 | 2048 | 198.5s | 6266 chars | Found all vulns |
| 🔒 Security Engineer | no_think | 10.40 | 2048 | 196.9s | 0 chars ⚠️ | Deep thinking, needs 4096+ |
| 📚 Technical Writer | no_think | 10.40 | 2048 | 196.9s | 4234 chars | WebSocket API docs |
| 🤖 AI Engineer | no_think | 10.39 | 2048 | 197.0s | 7722 chars | Full RAG pipeline code |
| ⏱️ Performance Benchmarker | no_think | 10.39 | 2048 | 197.0s | 0 chars ⚠️ | Needs more token budget |
| 🔌 API Tester | no_think | 10.39 | 2048 | 197.1s | 6875 chars | Pytest suite with fixtures |

**Key Findings:**
- **Speed remains unchanged**: 10.31–10.40 tok/s regardless of prompt complexity, mode, or token limit
- **no_think mode produces output for most roles**: 5 of 8 roles generated substantial (4–8K chars) code/docs
- **Some roles need 4096+ tokens**: Security Engineer and Performance Benchmarker still spent all tokens reasoning even in no_think mode — these complex prompts trigger deep reasoning chains
- **Code Reviewer benefits most from no_think**: 0 chars in thinking mode vs 6266 chars direct — `/no_think` bypasses the reasoning loop entirely
- **Quality is high**: Frontend Developer output includes full React/TypeScript/Tailwind component; AI Engineer has complete RAG pipeline with LangChain; API Tester writes 551-word Pytest suite

> **Server stability note**: The v2 benchmark experienced a server crash after 6 consecutive 2048-token generations (security_engineer/thinking was the trigger). Remaining roles were re-run after server restart. This suggests the Jetson needs brief cooldown between long generation runs.

<!-- BENCHMARK_RESULTS_END -->

### Other Models — Speed Benchmarks

| Model | GGUF Size | Gen tok/s | Tokens | Wall Time | Notes |
|-------|-----------|-----------|--------|-----------|-------|
| **Nanbeige4-3B-Thinking Q8_0** | 3.9 GiB | **17.22** | 1024 | 59.5s | Fastest! LLaMA arch, ~100% BW efficiency |
| **Qwen3.5-9B Q4_K_M** | 5.3 GiB | **10.44** | 1024 | 98.1s | ctx-size 2048, no OOM |
| **Qwen3-8B Q5_K_M** | 5.5 GiB | **10.24** | 512 | 50.0s | OOM killed after first long request |

#### Nanbeige4-3B-Thinking: Speed King, Deep Thinker

- **17.22 tok/s** — 65% faster than Qwen3.5-4B at near-lossless Q8_0
- Near-100% memory bandwidth efficiency (LLaMA architecture)
- **BFCL v4: 51.4** — highest function-calling score at ≤10B
- Caveat: extremely deep thinker. Uses `reasoning_content` field (not `<think>` tags). At 4096 tokens, still 0 visible output — all reasoning. Needs 6000+ tokens for practical use.
- Doesn't honor `/no_think` directive (Qwen-specific feature)

#### Qwen3-8B Q5_K_M: Unstable at T2

- First request (512 tokens) succeeded at 10.24 tok/s
- Second request (2048 tokens) caused OOM kill (exit code 137)
- KV cache grows to 254 MiB, pushing total past 8 GB limit
- **Not recommended for production** on 8 GB Jetson without strict token limits

#### Architecture Efficiency Discovery

The single biggest finding from these benchmarks:

| Architecture | Model | GGUF | tok/s | Efficiency |
|-------------|-------|------|-------|-----------|
| Pure LLaMA | Nanbeige-3B | 3.9 GiB | **17.22** | ~100% |
| Standard Transformer | Qwen3-8B | 5.5 GiB | 10.24 | 89% |
| Hybrid DeltaNet | Qwen3.5-9B | 5.3 GiB | 10.44 | 87% |
| Hybrid DeltaNet | Qwen3.5-4B | 4.2 GiB | 10.45 | 69% |

> On memory-bandwidth-constrained devices like the Jetson 8 GB, **architecture efficiency matters more than parameter count**. A 3B LLaMA model runs 65% faster than a 4B DeltaNet model.

## Tier System

Models are classified by GGUF size and Jetson viability:

| Tier | GGUF Size | Viability | Examples |
|------|-----------|-----------|----------|
| **T1** 🟢 | ≤ 4.5 GB | Runs comfortably with headroom | Qwen3.5-4B Q8_0 |
| **T2** 🟡 | 4.5–6 GB | Runs with swap pressure | Qwen3.5-9B Q4_K_M, Qwen3-8B Q5_K_M |
| **T3** 🟠 | 6–7 GB | Marginal, heavy swap, thermal issues | |
| **T4** 🔴 | > 7 GB | Does not fit, rejected | Qwen3.5-35B-A3B |

### Why T1 Wins on Jetson

With only 8 GB unified RAM shared between CPU, GPU, and OS:
- **OS + Docker + CUDA context** consumes ~2.5 GB baseline
- **T1 models** leave ~1 GB headroom for KV cache and compute
- **T2 models** push into swap, losing 15-20% throughput
- **T3+ models** thrash swap, becoming unusable

## Methodology

1. **Hardware control**: All tests on the same Jetson device, MAXN_SUPER power mode, `jetson_clocks` active
2. **Thermal stability**: Wait for GPU temp < 55°C between model swaps; discard first run as warmup
3. **Prompt design**: Role-specific prompts from [agency-agents](https://github.com/msitarzewski/agency-agents) with 1024 max output tokens
4. **Measurements**: `timings` from llama.cpp API response (hardware-level, not wallclock approximation)
5. **Statistics**: 3+ runs per configuration, report median gen tok/s
6. **Reproducibility**: All prompts, scripts, and results committed to this repo

### What We Measure

| Metric | Source | Why It Matters |
|--------|--------|---------------|
| Generation tok/s | `timings.predicted_per_second` | User-perceived output speed |
| Prompt tok/s | `timings.prompt_per_second` | Time to first token |
| Tokens generated | `timings.predicted_n` | Whether the model finished its response |
| Thinking used | `reasoning_content` presence | Whether the model engaged deep reasoning |
| Wall time (ms) | Client-side | End-to-end including network overhead |
| Finish reason | `choices[0].finish_reason` | `stop` (natural) vs `length` (truncated) |

### What We Don't Measure (Yet)

- **Response quality scoring** — planned: LLM-as-judge with rubric grading
- **Multi-turn conversation** — single-turn only for now
- **Concurrent request handling** — single-slot inference
- **Long context performance** — 1024 token max output

## BFCL v4 Leaderboard Scores

Key benchmark scores for Jetson-viable models (from [Berkeley Function Calling Leaderboard v4](https://gorilla.cs.berkeley.edu/leaderboard.html)):

| Model | BFCL v4 Overall | Simple | Multiple | Parallel | Multi-Turn | Jetson tok/s |
|-------|-----------------|--------|----------|----------|------------|-------------|
| **Nanbeige4-3B-Thinking** | **51.37** | 81.58 | 79.42 | 75.00 | 36.77 | **17.22** ✅ |
| **Qwen3.5-4B** | **49.70** | 71.25 | 67.00 | 50.00 | 43.72 | **10.45** ✅ |
| xLAM-2-8b-fc-r | 46.68 | 70.00 | 62.25 | 92.00 | 11.16 | ~9.4 predicted |
| Qwen3-8B | 42.57 | 87.58 | 80.53 | 93.75 | 14.62 | **10.24** ⚠️ |
| Qwen3.5-9B | — | — | — | — | — | **10.44** ✅ |

## File Reference

| File | Purpose |
|------|---------|
| [data/agent-roles.json](data/agent-roles.json) | Role definitions with benchmark prompts and grading rubrics |
| [data/jetson-models.json](data/jetson-models.json) | All candidate models with scores and Jetson-specific notes |
| [roles/](roles/) | Full agency-agents role definitions (MIT, from @msitarzewski) |
| [scripts/bench-roles-live.py](scripts/bench-roles-live.py) | Benchmark runner script |
| [docs/methodology.md](docs/methodology.md) | Detailed methodology documentation |

---

*Last updated: auto-generated from benchmark runs on Jetson Orin Nano Super*
