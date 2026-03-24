# Benchmark Sources (DYOR)

This file maps each public benchmark signal in the repo to its upstream source.

## Core Sources

- BFCL v4 (function-calling):
  - https://gorilla.cs.berkeley.edu/leaderboard.html

- Qwen3.5-4B model card (provider-reported evals: LiveCodeBench/GPQA/IFEval):
  - https://huggingface.co/Qwen/Qwen3.5-4B

- Qwen3-8B model card:
  - https://huggingface.co/Qwen/Qwen3-8B

- Qwen3.5-30B-A3B-Instruct-2507 model card (used as nearest public provider signal in prior MoE analysis context):
  - https://huggingface.co/Qwen/Qwen3.5-30B-A3B-Instruct-2507

- Quant file references:
  - https://huggingface.co/unsloth/Qwen3.5-4B-GGUF
  - https://huggingface.co/unsloth/Qwen3-8B-GGUF

## Method Notes

- Public leaderboards and model-card benchmarks are not always directly comparable across prompt templates, decoding settings, and evaluation harnesses.
- This repo pairs those public scores with local hardware-measured throughput to drive decisions.
- If a source updates values, submit a PR with:
  - source URL
  - date retrieved
  - old value -> new value
