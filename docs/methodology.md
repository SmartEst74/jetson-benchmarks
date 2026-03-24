# Methodology: Jetson LLM Benchmarking

This document describes the scientific methodology used for benchmarking LLMs on the Jetson Orin Nano Super 8GB.

## Hardware Configuration

| Component | Specification | Why It Matters |
|-----------|---------------|----------------|
| **Device** | NVIDIA Jetson Orin Nano Super Developer Kit | Real edge hardware, not cloud/server |
| **RAM** | 8 GB LPDDR5 (unified CPU/GPU) | Shared memory is the hard ceiling |
| **GPU** | 1024 CUDA cores, Ampere SM 8.7 | Determines compute capability |
| **CPU** | 6× ARM Cortex-A78AE @ 1.728 GHz | CPU inference fallback |
| **Memory BW** | 68 GB/s | Primary bottleneck for generation |
| **Storage** | 128 GB NVMe SSD | Fast model loading |
| **Power Mode** | MAXN_SUPER (7-25W) | Maximum performance mode |
| **JetPack** | 6.2 | Latest NVIDIA edge SDK |

## Benchmark Runner

### Environment Control

1. **Thermal Stability**: Wait for GPU temp < 55°C between model swaps
2. **Memory Cleanup**: `sudo sync && echo 3 | sudo tee /proc/sys/vm/drop_caches` before each run
3. **Container Isolation**: Each model runs in fresh Docker container
4. **No Background Load**: Production model stopped before benchmarks

### Docker Configuration

```bash
docker run -d --name bench-model \
  --runtime nvidia --gpus all \
  -v /home/jetson/models/llama-cache:/models \
  -p 8000:8000 \
  ghcr.io/nvidia-ai-iot/llama_cpp:latest-jetson-orin \
  /usr/local/bin/llama-server \
  --model /models/{MODEL}.gguf \
  --host 0.0.0.0 --port 8000 \
  --ctx-size {CTX} \
  --n-gpu-layers 99 \
  --flash-attn on \
  --mlock \
  --no-mmap \
  --threads 4
```

### Parameters That Matter

| Parameter | Value | Why |
|-----------|-------|-----|
| `--n-gpu-layers 99` | Offload all layers to GPU | Maximizes GPU utilization |
| `--flash-attn on` | Flash attention | Reduces memory usage 30-50% |
| `--mlock` | Lock model in RAM | Prevents swapping to NVMe |
| `--no-mmap` | No memory mapping | Consistent performance |
| `--threads 4` | CPU threads | Optimal for 6-core ARM |
| `--ctx-size` | 2048-8192 | Trade-off: larger = more memory |

## Measurement Methodology

### Speed Testing

1. **Warmup**: 32-token generation to stabilize GPU clocks
2. **Test Prompt**: Standardized coding task (512 max tokens)
3. **Temperature**: 0.6 (consistent across all tests)
4. **Measurement**: llama.cpp `timings` JSON (hardware-level)
5. **Repetitions**: 2 runs, report average gen_tps

### Thinking Quality Assessment

1. **Prompt Types**: Coding, reasoning, planning tasks
2. **Evaluation**: Rubric-based scoring (5 criteria per task)
3. **Metrics**: 
   - `thinking_chars`: Length of reasoning output
   - `response_chars`: Length of final answer
   - `thinking_ratio`: thinking / (thinking + response)
   - `honors_no_think`: Whether model respects `/no_think` directive

### Statistical Rigor

Currently: 2 runs per configuration (development phase)
Future: 3+ runs with median + standard deviation

## Performance Prediction Model

### Bandwidth Efficiency

```
predicted_tok/s = (bandwidth_GB/s ÷ GGUF_size_GiB) × efficiency_factor
```

- **68 GB/s**: Measured LPDDR5 bandwidth
- **0.69**: Default efficiency factor (validated: 10.5/(68/4.48) = 0.69)

### Architecture-Specific Efficiency

| Architecture | Efficiency | Validation |
|-------------|-----------|------------|
| Pure LLaMA | ~100% | Nanbeige4-3B: 17.22/(68/3.9) = 0.99 |
| Standard Transformer | ~89% | Qwen3-8B: 10.24/(68/5.5) = 0.83 |
| Hybrid DeltaNet | 69-87% | Qwen3.5-4B: 10.45/(68/4.48) = 0.69 |
| Sparse MoE | ~1% | Qwen3.5-35B: 0.18/(68/12.18) = 0.03 |

## Tier System

### Memory Budget Analysis

With 8 GB unified RAM:

| Component | Allocation |
|-----------|------------|
| OS + Docker + CUDA context | ~2.5 GB |
| Model weights | Variable |
| KV cache | ~136 MB per 1K tokens |
| Compute scratch | ~0.5 GB |
| **Available for model** | ~4.5 GB |

### Tier Classification

| Tier | GGUF Size | Viability | Example |
|------|-----------|-----------|---------|
| **T1** 🟢 | ≤ 4.5 GB | Comfortable headroom | Qwen3.5-4B Q8_0 |
| **T2** 🟡 | 4.5-6 GB | Runs with swap pressure | Qwen3.5-9B Q4_K_M |
| **T3** 🟠 | 6-7 GB | Marginal, heavy swap | — |
| **T4** 🔴 | > 7 GB | Does not fit / rejected | Qwen3.5-35B-A3B |

## Role-Based Benchmarking

### Role Selection

Eight real roles from [agency-agents](https://github.com/msitarzewski/agency-agents):

| Role | Division | Key Metric | Tests |
|------|----------|------------|-------|
| Frontend Developer | Engineering | LiveCodeBench v6 | React, CSS, perf |
| Backend Architect | Engineering | GPQA Diamond | DB schemas, APIs |
| Code Reviewer | Engineering | GPQA Diamond | Security, perf review |
| Security Engineer | Engineering | GPQA Diamond | STRIDE, hardening |
| Technical Writer | Engineering | IFEval | READMEs, docs |
| AI Engineer | Engineering | GPQA Diamond | Edge inference, RAG |
| Performance Benchmarker | Testing | GPQA Diamond | Load tests, reports |
| API Tester | Testing | BFCL v4 | Test suites, contracts |

### Task Grading

Each task uses weighted 5-dimension rubric:

| Dimension | Weight | Description |
|-----------|--------|-------------|
| Correctness | 30-35% | Does it work? |
| Completeness | 25-30% | All requirements met? |
| Code Quality | 20-25% | Clean, maintainable? |
| Robustness | 10-15% | Handles edge cases? |
| Documentation | 10% | Well-explained? |

## BFCL v4 — What It Is and Where It Comes From

### What Is BFCL v4?

**BFCL v4** = **Berkeley Function Calling Leaderboard Version 4**

It's a benchmark from UC Berkeley that tests an LLM's ability to **call functions and tools accurately**. When you ask an AI to "book a flight" or "query a database," it needs to convert your request into a valid function call. BFCL measures how well models do this.

### Source & Verification

| Resource | URL |
|----------|-----|
| **Official Leaderboard** | https://gorilla.cs.berkeley.edu/leaderboard.html |
| **GitHub Code** | https://github.com/ShishirPatil/gorilla |
| **Academic Paper** | https://proceedings.mlr.press/v267/patil25a.html |
| **Reproduce Results** | `pip install bfcl-eval==2025.12.17` |
| **Commit Reference** | f7cf735 (2025-12-16) |

### What Does BFCL v4 Test?

The benchmark evaluates 6 categories of function calling:

| Category | What It Tests | Example |
|----------|---------------|---------|
| **Simple FC** | Single function call from natural language | "What's the weather?" → `get_weather(location="NYC")` |
| **Multiple FC** | Multiple independent function calls | "Compare prices" → `get_price(item)` × 3 |
| **Parallel FC** | Parallel function execution | "Check all stores" → `check_stock(store_id)` × 5 |
| **Multi-Turn** | Multi-step conversations with tool use | "Book flight, then hotel" → 2 sequential calls |
| **Web Search** | Agentic RAG/tool use | "Research X" → search + summarize |
| **Irrelevance Detection** | Rejecting invalid/irrelevant requests | "Tell me a joke" → no function call (correct!) |

### How Is It Scored?

BFCL uses **Abstract Syntax Tree (AST) analysis** to check if the model's function call has:
1. **Correct syntax** — Is it valid code?
2. **Correct parameters** — Are the right values passed?
3. **Correct execution path** — Would this actually work?

Each category is scored 0–100. The overall BFCL score is the average across all categories.

### Score Interpretation

| Score Range | Meaning | Jetson Example |
|-------------|---------|----------------|
| 50+ | Excellent tool caller | Nanbeige4-3B (51.4) |
| 40-49 | Strong tool caller | Qwen3.5-4B (49.7) |
| 30-39 | Adequate | Qwen3-1.7B (28.4) |
| 20-29 | Basic | Granite-4.0-350m (19.0) |
| <20 | Poor | — |

### Citation

```bibtex
@InProceedings{pmlr-v267-patil25a,
  title = {The Berkeley Function Calling Leaderboard (BFCL): From Tool Use to Agentic Evaluation of Large Language Models},
  author = {Patil, Shishir G and Mao, Huanzhi and Yan, Fanjia and Ji, Charlie Cheng-Jie and Suresh, Vishnu and Stoica, Ion and Gonzalez, Joseph E},
  booktitle = {Proceedings of the 42nd International Conference on Machine Learning},
  year = {2025},
  url = {https://proceedings.mlr.press/v267/patil25a.html}
}
```

## Reproducibility

### Scripts

All benchmark scripts are in `scripts/`:

- `bench-comprehensive.py`: Full model benchmark
- `bench-roles-live.py`: Role-based benchmark
- `bench-roles-v2.py`: Dual-mode (thinking + no_think)
- `update_jetson_models.py`: Process results

### Data Files

- `data/jetson-models.json`: All models with scores
- `data/agent-roles.json`: Role definitions + tasks
- `data/test-roadmap.json`: Prioritized test plan

### Running Benchmarks

```bash
# Full comprehensive benchmark
python3 scripts/bench-comprehensive.py

# Role-based benchmark for specific model
python3 scripts/bench-roles-live.py --model Qwen3.5-4B

# Update data files with results
python3 scripts/update_jetson_models.py
```

## Limitations & Future Work

### Current Limitations

1. **Statistical rigor**: 2 runs (need 3+ for confidence intervals)
2. **Thinking quality**: Keyword-based evaluation (need LLM-as-judge)
3. **Single prompt**: One coding task per model (need multiple)
4. **No concurrent load**: Single-request testing only

### Planned Improvements

1. **Statistical rigor**: 3+ runs, median + stddev, confidence intervals
2. **Thinking quality**: LLM-as-judge with rubric scoring
3. **Multiple prompts**: Different complexity levels
4. **Hardware monitoring**: GPU temp, RAM/swap, power during tests
5. **Quality scoring**: Automated response quality evaluation

---

*Last updated: 2026-03-24*