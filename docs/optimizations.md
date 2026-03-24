# Optimization Notes (No Benchmark Regression)

## Baseline (Production)
- `--ctx-size 8192`
- `--flash-attn on`
- `--cache-type-k q8_0 --cache-type-v q8_0`
- `--n-gpu-layers 999`
- `--mlock --no-mmap`

## System Guardrails
- MAXN_SUPER mode
- jetson_clocks enabled
- cache drop before launch
- SSH OOM protection (`OOMScoreAdjust=-1000`, `vm.min_free_kbytes=65536`)

## Safe Next Optimizations to Test
- Thread count sweep (`--threads 5,6`) with fixed prompt
- Keep context at 8192 for quality parity, avoid reducing unless measuring task impact
- Maintain q8_0 KV cache for stability

Do not merge changes that improve speed but reduce coding/tool quality.
