# Jetson Benchmark Table

All rows must include reproducible script + command + environment details.

## Current Verified Rows

| Date | Device | JetPack | Runtime | Model | Quant | Context | Gen tok/s | Prompt tok/s | Notes |
|---|---|---|---|---|---|---:|---:|---:|---|
| 2026-03-23 | Orin Nano Super 8GB | 6.2 / R36.5.0 | llama.cpp b8095 | Qwen3.5-4B | Q8_0 | 8192 | 10.5 | 257 | Production default |
| 2026-03-22 | Orin Nano Super 8GB | 6.2 / R36.5.0 | llama.cpp b8095 | Qwen3.5-9B | Q4_K_M | 8192 | 8.8 | 70-85 | Backup |
| 2026-03-23 | Orin Nano Super 8GB | 6.2 / R36.5.0 | llama.cpp b8095 | Qwen3.5-35B-A3B | IQ3_XXS | 2048 | 0.18 | n/a | Rejected |

## Submission Format

Add rows via PR and include:
- startup script
- full command line
- tegrastats snapshot
- response timing JSON (`timings` object)
- at least 3 runs median
