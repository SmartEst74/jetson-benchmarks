# Prompt for planning a Jetson benchmark

Use this with an assistant when you want a plan tailored to your device.

> I am benchmarking local LLMs on a Jetson Orin Nano [RAM variant] with [JetPack/L4T] and [power mode]. My workload is [task], with typical input and output lengths of [token counts]. Use the benchmark catalogue to pick two or three exact model and quantization profiles. For each, identify the source and limits of the recorded result. Give me a memory preflight, a pinned runtime and launch configuration, and a repeatable test that measures answer completion, throughput, and peak RAM. Show host-changing commands separately for review.

For benchmark task prompts and rubrics, see [role benchmarks](ROLES.md). For the repeatable speed-test request, see [methodology](docs/methodology.md#launch-a-local-test-server).
