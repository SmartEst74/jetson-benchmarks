# Contributing Jetson benchmark results

Use the [benchmark submission template](.github/ISSUE_TEMPLATE/benchmark-submission.md) for a new result and follow the [measurement procedure](docs/methodology.md). A useful submission lets someone match your configuration and see how often it completed successfully.

## Include with each result

- Device and RAM variant, JetPack/L4T, power mode, cooling, storage, and background load.
- Exact GGUF filename, quantization, model source, SHA-256, runtime commit or container digest, and launch command.
- Prompt or fixture revision, cache policy, context, concurrency, batch, thinking mode, decoding settings, and output cap.
- Individual run timings and median/range for at least three repeats, including actual token counts and finish reasons. Label server decode separately from client end-to-end throughput.
- Relevant startup logs and tegrastats samples, with load failures, OOMs, throttling, and incomplete answers recorded alongside successful requests.

Remove credentials, private prompts, and identifying host details from shared logs. Link evidence from the relevant row in [BENCHMARKS.md](BENCHMARKS.md). Keep candidate predictions and external scores separate from local measurements. If an older result disagrees, link both sources and explain the configuration difference or mark the discrepancy unresolved.

## Documentation changes

Keep [README.md](README.md) as the entry point. Put measured claims in the benchmark catalogue, operating instructions in the [memory guide](docs/memory.md), and benchmark protocol in [methodology](docs/methodology.md). Run the local link check after moving a file or heading.

```bash
lychee --offline --include-fragments --no-progress '*.md' 'docs/**/*.md' '.github/ISSUE_TEMPLATE/*.md'
```
