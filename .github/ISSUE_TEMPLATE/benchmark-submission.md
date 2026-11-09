---
name: Benchmark Submission
about: Submit reproducible Jetson benchmark results
title: "benchmark: <device> <model> <quant>"
labels: benchmark
---

## Hardware and software

- Device / RAM / storage:
- Power mode / clock policy / cooling:
- JetPack / L4T:
- Runtime build or image digest:
- GGUF filename, quantization, source and SHA-256:

## Configuration

Paste the launch command with credentials and private host details removed.

- Prompt or fixture revision:
- Context / concurrency / batch:
- Thinking mode / output cap / sampling settings:
- Warm-up and cache policy:

## Results

- Individual run timings (at least three), median and range:
- Prefill and decode tok/s, or clearly labeled client throughput:
- Actual token counts, finish reasons and visible answer completion:
- Peak RAM and swap, temperatures and any throttling:
- Failed loads, OOMs or interrupted runs:

Attach sanitized timing JSON, startup logs, and tegrastats samples.
