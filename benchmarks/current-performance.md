# Benchmark Results

## Qwen3.5-9B Q4_K_M (Current Production)

### Token Generation
- **Prompt processing**: 47 tok/s (21ms/token)
- **Generation**: 8.8 tok/s (113ms/token)
- **Theoretical max**: 12.8 tok/s (5.3GB / 68 GB/s bandwidth)
- **Efficiency**: 69% of bandwidth limit

### During Generation (tegrastats)
- GPU utilization: 83-99% @ 1015 MHz
- GPU temp: ~60°C (well within limits)
- RAM: 7232/7607 MB (95%)
- Swap: 1199 MB used
- Power: ~21W

### Analysis
- 113ms per token breakdown:
  - Theoretical minimum (bandwidth): 78ms (5.3GB / 68 GB/s)
  - Actual overhead: 35ms (45% overhead above minimum)
  - Sources: CUDA kernel launch, DeltaNet recurrence, memory access patterns
  - GPU not always 100% → some CPU-bound work between GPU dispatches

## Qwen3.5-35B-A3B IQ3_XXS (Testing)

### Predictions
- Model size: 12.18 GB (5.25 GB will overflow to swap)
- Active weight read per token: ~1.4 GB (MoE optimization)
- If MoE-optimized (only active experts read):
  - Theoretical: 1.4GB / 68 GB/s = 20.6ms = 48 tok/s
  - With 45% overhead: ~33 tok/s
- If dense-read (all weights read per token):
  - In-RAM portion: 6.93 GB at 68 GB/s = 102ms
  - Swap portion: 5.25 GB at 779 MB/s = 6.7s (!!!)
  - Total: ~6.8s per token = 0.15 tok/s (unusable)
- Reality will be somewhere in between depending on expert caching

### Key Variables
1. Does llama.cpp b8095 do MoE-optimized reads? (only active experts)
2. How does unified memory handle page faults for swapped experts?
3. Does --mmap help or hurt with MoE on unified memory?
4. Can --cpu-moe help if some experts are in swap?
