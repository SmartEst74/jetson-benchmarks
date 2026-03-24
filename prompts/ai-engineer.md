# AI Engineer — Benchmark Prompts

**Purpose**: Test a model's ability to design ML pipelines, optimize inference, and architect AI systems.

**Scoring**: Each prompt is graded on correctness (30%), completeness (25%), code quality (20%), robustness (15%), documentation (10%).

---

## Prompt AI-1: Inference Optimization (Complexity: ★★★★☆)

**Tests**: Model optimization, hardware constraints, deployment

```
Design an inference optimization pipeline for a 4B parameter LLM on Jetson Orin Nano Super.

Hardware specs:
- 8GB unified RAM
- 1024 CUDA cores, SM 8.7
- 68 GB/s memory bandwidth

Cover:
- Quantization strategy (GPTQ vs AWQ vs GGUF)
- KV cache management for 8K context
- Batching strategy
- Thermal management
- Memory budget breakdown with specific numbers
```

**Expected**: Memory calculations, quantization comparison, KV cache sizing, thermal throttling strategy.

---

## Prompt AI-2: RAG Pipeline (Complexity: ★★★☆☆)

**Tests**: Retrieval augmented generation, vector search, chunking

```
Design a RAG (Retrieval Augmented Generation) pipeline for a codebase documentation system.

Requirements:
- Index 500 markdown files (avg 2KB each)
- Support semantic search and keyword search
- Handle code snippets with syntax highlighting
- Incremental updates when files change
- Run on Jetson with 8GB RAM

Include: embedding model choice, chunking strategy, vector DB selection, retrieval logic, prompt construction.
```

**Expected**: Practical choices for edge deployment, chunking strategy, hybrid search, caching.

---

## Prompt AI-3: Fine-Tuning Strategy (Complexity: ★★★★★)

**Tests**: Training methodology, evaluation, deployment

```
Design a fine-tuning pipeline to create a Jetson-optimized model from Llama 3.1 8B.

Requirements:
- Domain: code review and security analysis
- Training data: 10,000 code review examples
- Hardware: single A100 GPU, 40GB VRAM
- Target: Q4_K_M GGUF for Jetson deployment
- Evaluation: code review quality metrics

Cover:
- LoRA vs QLoRA configuration
- Data preprocessing and tokenization
- Training hyperparameters
- Evaluation methodology
- Export to GGUF format
```

**Expected**: LoRA config, data format, training script, evaluation suite, GGUF conversion.
