# Jetson Orin Nano LLM Guide

The definitive, measured benchmark platform for running LLMs on NVIDIA Jetson Orin Nano Super (8 GB). Every model listed here actually runs — or is predicted to run — on 8 GB of unified memory. No cloud models. No impossible configs. Real hardware. Real [agency-agents](https://github.com/msitarzewski/agency-agents) roles.

**[Benchmark Results](BENCHMARKS.md)** · **[Agent Roles](ROLES.md)** · **[Test Roadmap](ROADMAP.md)**

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
| **Qwen3.5-35B-A3B** | IQ3_XXS | 12.18 GB | 0.18 | — | ❌ Rejected (swap thrash) |

### Architecture Matters: The Efficiency Story

On memory-bandwidth-constrained Jetson (68 GB/s), **architecture efficiency matters more than parameter count**:

| Architecture | Efficiency | Example | Speed | Why |
|-------------|-----------|---------|-------|-----|
| **Pure LLaMA** | ~100% | Nanbeige4-3B (3B) | **17.22 tok/s** | Simple attention, GPU-optimized |
| **Standard Transformer** | ~89% | Qwen3-8B (8B) | 10.24 tok/s | Minor overhead from grouped attention |
| **Hybrid DeltaNet** | 69-87% | Qwen3.5-4B (4B) | 10.45 tok/s | Gated recurrent state updates |
| **Sparse MoE** | ~1% | Qwen3.5-35B (35B) | 0.18 tok/s | Expert routing forces CPU offload |

> **Key insight**: A 3B LLaMA model runs **65% faster** than a 4B DeltaNet model despite being only 7% smaller. Architecture dominates on 8GB.

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
