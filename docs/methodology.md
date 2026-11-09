# Reproducing a Jetson benchmark

Use this procedure for new comparisons. The [historical catalogue](../BENCHMARKS.md) describes the different procedures actually used for archived runs.

## Record the environment

Use the [NVIDIA developer kit setup guide](https://docs.nvidia.com/jetson/orin-nano-devkit/user-guide/latest/setup_bsp.html) if the Jetson needs provisioning. Choose a CUDA-enabled arm64 runtime compatible with your installed Jetson Linux release and exact GGUF format. Prefer a container pinned by digest if you use Docker. For a source build, record the commit, CUDA build flags, and compiler. [JetPack release mapping](https://developer.nvidia.com/embedded/jetpack-archive) · [llama.cpp CUDA build instructions](https://github.com/ggml-org/llama.cpp/blob/master/docs/build.md#cuda)

On the Jetson, capture the release, power mode, and memory baseline. For a containerized server, run the version command inside the container. Power-mode IDs vary by configuration. Record the selected mode and whether clocks are locked. Hold the power mode, cooling, and clock policy constant across runs. [NVIDIA power and performance guide](https://docs.nvidia.com/jetson/archives/r36.5/DeveloperGuide/SD/PlatformPowerAndPerformance/JetsonOrinNanoSeriesJetsonOrinNxSeriesAndJetsonAgxOrinSeries.html)

```bash
cat /etc/nv_tegra_release
sudo nvpmodel -q
free -h
llama-server --version
```

Record the board and RAM variant, JetPack/L4T, cooling, model file and SHA-256, quantization, runtime commit or image digest, and full launch command. Note the idle temperature, initial available RAM, and swap configuration. Run the [memory preflight](memory.md#before-loading-a-model) when switching profiles.

## Launch a local test server

The example assumes a compatible `llama-server` and an existing GGUF. Set `MODEL` to the actual file path, inside the container if applicable. Verify these flags against your build's `--help`. Run the client in the same network namespace, or configure loopback-only port publishing for a containerized test. Check the startup log for GPU offload and buffer allocations. [llama.cpp server reference](https://github.com/ggml-org/llama.cpp/tree/master/tools/server)

```bash
MODEL=/path/to/model.gguf
llama-server --model "$MODEL" --alias benchmark-model \
  --host 127.0.0.1 --port 8080 \
  --ctx-size 4096 --parallel 1 --n-gpu-layers 999
```

From another shell with access to that endpoint, verify readiness and save a sample response. This example uses a fixed request. Repeat with the same inputs and record actual output tokens and finish reason, since a model can stop before the output cap.

```bash
curl --fail --silent --show-error http://127.0.0.1:8080/health

curl --fail --silent --show-error http://127.0.0.1:8080/v1/chat/completions \
  -H 'Content-Type: application/json' \
  --data '{
    "model": "benchmark-model",
    "messages": [{"role": "user", "content": "Write a Python binary search for a sorted integer list. Include edge-case tests."}],
    "temperature": 0,
    "max_tokens": 512,
    "stream": false,
    "cache_prompt": false
  }' > run-01.json
```

## Measure and report

1. **Separate load from inference.** Measure process start to ready for model load. Declare whether the filesystem and prompt caches are warm. Check your build's prompt-cache options and keep the reuse policy consistent. Record a warm-up and exclude it from the timed set.
2. **Run at least three timed repeats per configuration.** Use the same prompt, context, batch, decoding settings, concurrency, and output budget. Record tokenizer-specific prompt length, generation length, finish reason, and whether a visible answer completed. Compare at a representative context depth as well as on short prompts if long contexts matter.
3. **Keep timing metrics separate.** Where returned, report server `timings.prompt_per_second` and `timings.predicted_per_second` as prefill and decode rates. For client measurements, label completion tokens divided by full request duration as end-to-end throughput. Measure time to first token with a streaming client and specify whether the first token can be reasoning or must be visible answer text. Report the median and range across repeats.
4. **Record resource use and failures.** Sample `tegrastats` through loading and generation. Record peak RAM and swap, temperatures, power mode, and any throttling, truncation, load failure, or crash. Include failed attempts in the report.
5. **Test usefulness separately.** For tool calling, check parsed tool name, arguments, and task completion. For coding, test the answer on the same cases. Keep local quality observations separate from provider and leaderboard scores. [Role prompts and rubrics](../ROLES.md)

For controlled prefill and decode microbenchmarks, use the matching build's `llama-bench`. Its `pp` and `tg` results describe different operations, and its internal repetitions report a mean and standard deviation. Keep these results separate from server request timings. [llama-bench documentation](https://github.com/ggml-org/llama.cpp/tree/master/tools/llama-bench)

Save raw responses and resource logs before adding a result. [Submission checklist](../CONTRIBUTING.md)
