# Working in this repository

- **Choosing a model or citing a result** — Read [BENCHMARKS.md](BENCHMARKS.md). Keep the model, quantization, workload, runtime, and measurement method attached to each number. Treat external quality scores as separate evidence.
- **Loading or switching models** — Follow [memory preflight](docs/memory.md) before starting the replacement. Inspect the workload owner and memory headroom before acting on a Jetson.
- **Rebuilding Bonsai or adding runtime setup** — Follow the [Bonsai rebuild recipe](docs/bonsai-rebuild.md). Track pins, checksums, and commands. Keep weights and build products outside Git.
- **Running or adding a benchmark** — Follow [methodology](docs/methodology.md) and [submission requirements](CONTRIBUTING.md). Preserve the source link, measurement method, and failure outcome for each result.
- **Working on role tests** — Read [ROLES.md](ROLES.md) for the archived prompts, rubrics, and result links.
