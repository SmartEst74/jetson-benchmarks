# Jetson Orin Nano Super LLM benchmarks

A guide to choosing and benchmarking local language models on the **NVIDIA Jetson Orin Nano Super 8 GB**. The catalogue separates historical chat runs from on-device microbenchmarks. Start with the comparison for your workload, then use the memory checklist before loading a model.

| I want to… | Start here |
| --- | --- |
| Choose a model for speed, coding, reasoning, or low memory use | [Benchmark shortlist](BENCHMARKS.md#shortlist-by-workload) |
| Compare all recorded runs, including failures | [Jetson results](BENCHMARKS.md#jetson-results) |
| Free memory or recover from a failed load | [Memory preflight](docs/memory.md#before-loading-a-model) |
| Run a model and measure it on my Jetson | [Setup and benchmark procedure](docs/methodology.md) |
| Find the role prompts and grading rubrics | [Role benchmarks](ROLES.md) |
| Submit a result or see where evidence is missing | [Contributing](CONTRIBUTING.md) · [Roadmap](ROADMAP.md) |

## Before switching models

Stop the old inference workload through the service, container, or terminal that owns it. Check the `available` column in `free -h` and watch RAM and swap activity before loading the next model. Start with one inference slot and a small context. The CPU and integrated GPU share the same memory pool. [Memory preflight](docs/memory.md)

## Scope

The comparison covers the Super 8 GB configuration. Archived tests on other hosts are outside the comparison. The previous checkout is linked from the benchmark catalogue for exact source records. This checkout provides documentation and benchmark commands, with the inference runtime supplied separately. [Benchmark evidence](BENCHMARKS.md#evidence)
