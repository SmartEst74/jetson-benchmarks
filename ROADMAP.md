# Benchmark roadmap

The priorities below are open work. Completed and failed runs are listed in the [benchmark catalogue](BENCHMARKS.md).

| Priority | Experiment | Evidence to publish |
| --- | --- | --- |
| 1 | Rerun the shortlist with one pinned CUDA runtime per compatible GGUF format and a matched request set | Per-run timings, visible-answer completion, wall time, first-token latency, and peak memory |
| 2 | Sweep context and KV cache settings, beginning at 2K or 4K | Startup allocations, long-prompt and long-generation stability, and confirmed context depth |
| 3 | Score coding and tool use on-device | Prompt revisions, tests or rubrics, parsed tool calls, and recorded failure reasons |
| 4 | Measure power-mode and thermal effects | Repeatable throughput and tegrastats samples for each named mode |

The previous [candidate list](https://github.com/SmartEst74/jetson-benchmarks/blob/1c4196c794a39dc206453428593fffdf164e68bb/data/jetson-models.json) mixes local observations, external scores, and predictions. Treat candidate entries as leads for new runs and consult the [current catalogue](BENCHMARKS.md) for the curated historical comparison.
