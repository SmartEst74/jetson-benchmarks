# Rebuild Bonsai on a clean Jetson

This recipe recreates the text-only Ternary-Bonsai-2-27B PTQ1_0 setup from public sources. The recorded baseline was Jetson Orin Nano Super 8 GB, Jetson Linux R36.5.2, and CUDA 12.6. Use the JetPack release and CUDA toolkit appropriate to the board. Treat JetPack 7 results as a new baseline until the build and smoke test pass there. [NVIDIA setup guide](https://docs.nvidia.com/jetson/orin-nano-devkit/user-guide/setup_bsp.html) · [Recorded run](results/2026-11-09-bonsai2-27b.md)

## Build the pinned runtime

On the provisioned Jetson, install Git, CMake, a C/C++ toolchain, curl, and OpenSSL headers through the system package manager. Check that the installed JetPack CUDA toolkit provides `nvcc` before configuring the build. The commands assume the toolkit is at `/usr/local/cuda` and the runtime directory is new. The CUDA architecture `87` targets Orin. [PrismML source revision](https://github.com/PrismML-Eng/llama.cpp/tree/1a07bfa5f4144274c8f1c9963821dd9d9a51854b)

```bash
sudo apt install git cmake build-essential curl libssl-dev
/usr/local/cuda/bin/nvcc --version

RUNTIME="$HOME/jetson-runtimes/prism-bonsai2"
mkdir -p "$(dirname "$RUNTIME")"
git clone --filter=blob:none https://github.com/PrismML-Eng/llama.cpp.git "$RUNTIME"
git -C "$RUNTIME" checkout --detach 1a07bfa5f4144274c8f1c9963821dd9d9a51854b
cmake -S "$RUNTIME" -B "$RUNTIME/build" \
  -DCMAKE_BUILD_TYPE=Release -DGGML_CUDA=ON \
  -DCMAKE_CUDA_ARCHITECTURES=87 -DCMAKE_CUDA_COMPILER=/usr/local/cuda/bin/nvcc
cmake --build "$RUNTIME/build" --target llama-server llama-bench --parallel 2
"$RUNTIME/build/bin/llama-server" --version
```

## Download the exact model outside Git

The upstream file is about 5.95 GB. The published SHA-256 matches the file used in the recorded run. Download it on the Jetson when needed. The standard file is sufficient for this recipe. [Pinned GGUF file](https://huggingface.co/prism-ml/Ternary-Bonsai-2-27B-gguf/blob/839bd57023c1558945afea70a74fa83c054f35f9/Ternary-Bonsai-2-27B-PTQ1_0.gguf)

```bash
MODEL_DIR="$HOME/jetson-models/bonsai2"
MODEL="$MODEL_DIR/Ternary-Bonsai-2-27B-PTQ1_0.gguf"
mkdir -p "$MODEL_DIR"
curl --fail --location --continue-at - --output "$MODEL.partial" \
  'https://huggingface.co/prism-ml/Ternary-Bonsai-2-27B-gguf/resolve/839bd57023c1558945afea70a74fa83c054f35f9/Ternary-Bonsai-2-27B-PTQ1_0.gguf' &&
  printf '%s  %s\n' '53107f530aa52eb00912263ab1ee29bd199261c87cd7b4ad4ca1318c1fe33ee3' "$MODEL.partial" |
  sha256sum --check --strict && mv -- "$MODEL.partial" "$MODEL"
```

## Verify the recreated setup

Run the [memory preflight](memory.md#before-loading-a-model). With the same `RUNTIME` and `MODEL` values, run a short benchmark with one model loaded and inspect the output for CUDA and three completed repetitions. Keep any new timings separate from the historical record. [Recorded command and measurements](results/2026-11-09-bonsai2-27b.md#command)

```bash
timeout -k 5s 150s "$RUNTIME/build/bin/llama-bench" -m "$MODEL" \
  -p 0 -n 32 -b 128 -ub 128 -t 6 -ctk f16 -ctv f16 -fa auto \
  -fitt 512 -fitc 512 -r 3 -o json --progress
```

For chat tests, start a loopback-only server with one slot and a 512-token context. Use the [local test procedure](methodology.md#launch-a-local-test-server) to check readiness and send a sample request. Measure headroom before increasing context. The historical run measured the benchmark executable, so verify the server profile separately.

```bash
"$RUNTIME/build/bin/llama-server" --model "$MODEL" --alias benchmark-model \
  --host 127.0.0.1 --port 8080 --ctx-size 512 --parallel 1 \
  --batch-size 128 --ubatch-size 128 --cache-ram 0 --fit on --fit-target 512
```

Benchmark prompts, version pins, and launch settings belong in this repository. Keep model weights, compiled runtimes, credentials, and machine-specific network settings outside it.
