# Jetson Orin Nano Super 8 GB benchmark results

## Shortlist by workload

| Workload | First profile to try | Why |
| --- | --- | --- |
| Small, latency-sensitive tasks | Granite-4.0-350m Q8_0 | **88.92 tok/s**, the highest rate in the March short-request sweep. Validate output quality on your task. [GGUF][granite-gguf] |
| Coding and general chat on the recorded mainline runtime | Qwen3.5-4B Q8_0 | **10.45 tok/s** average across eight role prompts. At a 1,024-token budget, six of eight thinking-mode requests returned zero visible answer characters. [GGUF][qwen-gguf] |
| Function calling | xLAM-2-1b-fc-r Q8_0 or xLAM-2-3b-fc-r Q8_0 | **31.23** and **20.27 tok/s** in the short-request sweep. The 3B variant has a higher archived BFCL score. Test actual tool calls with the quantized model. [1B GGUF][xlam1-gguf] · [3B GGUF][xlam3-gguf] |
| Reasoning | Nanbeige4-3B-Thinking Q8_0 | **17.22 tok/s** in a historical speed test. A separate 4,096-token trial was reported to yield no visible answer, so measure time to a usable response. [GGUF][nanbeige-gguf] |
| Compact 8B weights | Ternary-Bonsai-8B Q2_0 (g128) | **12.12 tok/s** median at 4,096 context in MAXN_SUPER mode. The exact legacy GGUF and compatible PrismML fork matter. [GGUF][bonsai-gguf] |

These are starting points from the repository's historical evidence. The sweep reports the best single client-observed rate across tested configurations. The role average and Bonsai median use different workloads and statistics. For interactive use, compare first-token latency, answer completion, and memory headroom alongside token rates. The GGUF links identify current files for the named quantizations. Several historical runs lack model hashes for byte-level matching.

## Jetson results

Dates, settings, and rates below are as recorded. A dash means the relevant source lacks the value. Configured context is the server limit. It does not establish how much context a request exercised. Use the [reproduction procedure](docs/methodology.md) for a matched comparison.

### Short-request sweep

The March 24 sweep used a 512-token output cap. Rates are completion tokens divided by client wall time, including prompt handling. Each row is the best successful configuration for that model in the sweep. The archived runner's prompt-rate calculation is unsuitable for measuring prefill, so these rows report completion throughput only. [Sweep data][sweep-data] · [Timing code][sweep-runner]

| Model | Quant | Context | Completion tok/s |
| --- | --- | ---: | ---: |
| Granite-4.0-350m | Q8_0 | 4,096 | **88.92** |
| Qwen3-1.7B | Q8_0 | 2,048 | 32.30 |
| xLAM-2-1b-fc-r | Q8_0 | 2,048 | 31.23 |
| xLAM-2-3b-fc-r | Q8_0 | 2,048 | 20.27 |
| Arch-Agent-1.5B | Q8_0 | 2,048 | 18.11 |
| MiniCPM3-4B | Q4_K_M | 2,048 | 11.03 |

The archived README listed different speeds for five of these models. The sweep data and its commit agree on the rates above. The MiniCPM record's `best_quant` says Q8_0, but both its launch command and the runner specify the Q4_K_M file. [Older README][old-readme] · [Sweep commit][sweep-commit] · [Model files in the runner][sweep-files]

### Other throughput runs

| Model | Quant | Context | Generation tok/s | Prompt tok/s | Workload and outcome |
| --- | --- | ---: | ---: | ---: | --- |
| Hammer2.1-3b | Q8_0 | 4,096 | 20.93 | — | March speed result, repetitions unspecified. [Model records][models] |
| Llama-3.2-3B-Instruct | Q8_0 | 4,096 | 19.12 | — | March speed result, repetitions unspecified. [Model records][models] |
| Nanbeige4-3B-Thinking | Q8_0 | — | 17.22 | — | 1,024 generated tokens in 59.5 s. Reasoning output can dominate. [March summary][old-speeds] |
| Ternary-Bonsai-8B | Q2_0 g128 | 4,096 | **12.12** | 171–205 | May 5, MAXN_SUPER, 512-token binary-search-tree task, median of three generation runs. Prompt range is from cold requests. [May results][may-results] · [Run table][run-table] |
| Ternary-Bonsai-8B | Q2_0 g128 | — | 11.8 | 38.4 | Separate 200-token GPU run. The reported CPU-only comparison was 3.9 generation and 4.8 prompt tok/s. The date in this subsection conflicts with the archive's update date. [200-token comparison][bonsai-200] |
| Ternary-Bonsai-8B | Q2_0 g128 | 4,096 | 7.37 | 122–126 | May 6, 15W profile, 612 MHz GPU cap. [Run table][run-table] |
| Qwen3.5-4B | Q8_0 | — | 10.45 | 301.30 | Mean across eight role prompts, 1,024-token output cap. [Role results][role-results] |
| Qwen3.5-4B | Q8_0 | 8,192 | 10.5 | 257 | Separate March 23 run. [Run table][run-table] |
| Qwen3.5-9B | Q4_K_M | 2,048 | 10.44 | — | 1,024-token request completed. [March summary][old-speeds] |
| Qwen3.5-9B | Q4_K_M | 8,192 | 8.8 | 70–85 | March 22 run-table prompt range. Another archived snapshot reports 47 prompt tok/s at the same generation rate and 1,199 MB swap in use. [Run table][run-table] · [Memory snapshot][may-results] |

The Bonsai sweep also reports an **8,192-token configuration** using `q4_0` for both KV caches at 15W. A historical 65,536-token server profile exists, but the 12.12 tok/s median comes from the 4,096 configuration. Full-window throughput and stability need a separate run. The recorded GGUF is the legacy 2.03 GiB file with group size 128. For that file, use the recorded compatible build rather than assuming the latest fork accepts it. [May results][may-results] · [Recorded PrismML build][prism-build] · [PrismML format compatibility][prism-formats]

### Failed or unstable profiles

| Model | Quant | Reported rate | Failure |
| --- | --- | ---: | --- |
| Qwen3-8B | Q5_K_M | 10.24 tok/s | A 512-token request succeeded. A subsequent longer request was reported killed under memory pressure. [March summary][old-speeds] · [Model record][models] |
| Qwen3.5-35B-A3B | IQ3_XXS | 0.18 tok/s | The archived CPU-MoE profile was rejected. The records also report swap thrashing with partial GPU offload. [Run table][run-table] · [Model record][models] |

### On-device microbenchmark

On 9 November 2026, **Ternary-Bonsai-2-27B PTQ1_0** completed synthetic prefill at **41.80 tok/s** (`pp512`) and short decode at **4.57 tok/s** (`tg32`), each averaged over three repetitions. The first invocation timed out during the 128-token decode test and reached 7,011 MB sampled RAM use. Compare these results with other `llama-bench` runs at matching settings. [Run details and timing records](docs/results/2026-11-09-bonsai2-27b.md)

## External function-calling scores

These are historical scores transcribed in the project. They describe published evaluations of the models and are separate from the GGUF runs on Jetson. The current leaderboard may contain a different snapshot, and the archived Qwen3.5-4B model record labels its source as a card score. [Archived scores][old-scores] · [Archived model records][models] · [Berkeley BFCL leaderboard](https://gorilla.cs.berkeley.edu/leaderboard.html)

| Model | Archived BFCL v4 overall |
| --- | ---: |
| Nanbeige4-3B-Thinking | 51.37 |
| Qwen3.5-4B | 49.70 |
| xLAM-2-3b-fc-r | 41.22 |
| xLAM-2-1b-fc-r | 30.44 |
| Granite-4.0-350m | 18.98 |

## Evidence

- The March sources report llama.cpp b8095 and the May Bonsai sources report PrismML b1-d104cf1. The archived sweep used a Docker tag without a recorded digest. For the rows tagged L4T 36.5.0, NVIDIA maps that release to JetPack 6.2.2. [Run table][run-table] · [Sweep runner][sweep-runner] · [NVIDIA JetPack archive](https://developer.nvidia.com/embedded/jetpack-archive)
- NVIDIA lists 8 GB LPDDR5 and up to **102 GB/s** for the Super kit, up from 68 GB/s. The older documents' 68 GB/s model is a heuristic assumption. Without measured memory traffic and matched test settings, it cannot establish achieved bandwidth efficiency. [NVIDIA specifications](https://www.nvidia.com/en-us/autonomous-machines/embedded-systems/jetson-orin/nano-super-developer-kit/)
- The retained evidence is primarily summary tables, scripts, and model metadata. Raw per-run responses, exact image digests, or complete environment details are unavailable for several rows. [Archived tree][archive]
- For the historical prompts and reported response behaviour, see [role benchmarks](ROLES.md). For untested candidates and gaps, see the [roadmap](ROADMAP.md).

[archive]: https://github.com/SmartEst74/jetson-benchmarks/tree/1c4196c794a39dc206453428593fffdf164e68bb
[models]: https://github.com/SmartEst74/jetson-benchmarks/blob/1c4196c794a39dc206453428593fffdf164e68bb/data/jetson-models.json
[sweep-data]: https://github.com/SmartEst74/jetson-benchmarks/blob/770c62723c033b46f6be734e7bacdd474e93ad39/data/jetson-models.json
[sweep-runner]: https://github.com/SmartEst74/jetson-benchmarks/blob/770c62723c033b46f6be734e7bacdd474e93ad39/scripts/bench-max-util.py#L169
[sweep-files]: https://github.com/SmartEst74/jetson-benchmarks/blob/770c62723c033b46f6be734e7bacdd474e93ad39/scripts/bench-max-util.py#L21-L38
[sweep-commit]: https://github.com/SmartEst74/jetson-benchmarks/commit/770c62723c033b46f6be734e7bacdd474e93ad39
[old-readme]: https://github.com/SmartEst74/jetson-benchmarks/blob/1c4196c794a39dc206453428593fffdf164e68bb/README.md#tested-models-1123-complete
[old-speeds]: https://github.com/SmartEst74/jetson-benchmarks/blob/1c4196c794a39dc206453428593fffdf164e68bb/BENCHMARKS.md#other-models--speed-benchmarks
[role-results]: https://github.com/SmartEst74/jetson-benchmarks/blob/1c4196c794a39dc206453428593fffdf164e68bb/BENCHMARKS.md#qwen35-4b-q8_0--role-benchmark-results
[bonsai-200]: https://github.com/SmartEst74/jetson-benchmarks/blob/1c4196c794a39dc206453428593fffdf164e68bb/BENCHMARKS.md#ternary-bonsai-8b-q2_0--gpu-benchmark-results
[run-table]: https://github.com/SmartEst74/jetson-benchmarks/blob/1c4196c794a39dc206453428593fffdf164e68bb/benchmarks/benchmark-table.md
[may-results]: https://github.com/SmartEst74/jetson-benchmarks/blob/1c4196c794a39dc206453428593fffdf164e68bb/benchmarks/current-performance.md
[old-scores]: https://github.com/SmartEst74/jetson-benchmarks/blob/1c4196c794a39dc206453428593fffdf164e68bb/BENCHMARKS.md#bfcl-v4-leaderboard-scores
[prism-build]: https://github.com/PrismML-Eng/llama.cpp/tree/d104cf1b639a909ddea521d61f7cb023c6e41f57
[prism-formats]: https://github.com/PrismML-Eng/llama.cpp#readme
[granite-gguf]: https://huggingface.co/mrutkows/granite-4.0-350m-GGUF/blob/a2c45e0e8c65cb4a7c6021f1904ac018c442cfa7/granite-4.0-350m-Q8_0.gguf
[qwen-gguf]: https://huggingface.co/unsloth/Qwen3.5-4B-GGUF/blob/e87f176479d0855a907a41277aca2f8ee7a09523/Qwen3.5-4B-Q8_0.gguf
[xlam1-gguf]: https://huggingface.co/Salesforce/xLAM-2-1b-fc-r-gguf/blob/5c28181eb7be2575173dc18e54e09e3efaf2ed25/xLAM-2-1B-fc-r-Q8_0.gguf
[xlam3-gguf]: https://huggingface.co/Salesforce/xLAM-2-3b-fc-r-gguf/blob/a40e82c22c3f2b40410186d56c76e3005a1d4813/xLAM-2-3B-fc-r-Q8_0.gguf
[nanbeige-gguf]: https://huggingface.co/bartowski/Nanbeige_Nanbeige4-3B-Thinking-2511-GGUF/blob/16bb1fbc22aca1d48574567145ffa8094646173a/Nanbeige_Nanbeige4-3B-Thinking-2511-Q8_0.gguf
[bonsai-gguf]: https://huggingface.co/prism-ml/Ternary-Bonsai-8B-gguf/blob/c2aefbeb4b24469cd11579c3384b990404c17a30/Ternary-Bonsai-8B-Q2_0.gguf
