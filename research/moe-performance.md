# llama.cpp MoE Performance Research

## Key Issues Affecting Qwen3.5-35B-A3B

### #20883 — Fused quants lose 50% TG in mixed VRAM+RAM
- **Status**: OPEN
- **Impact**: CRITICAL for us — model overflows to swap
- **Problem**: Fused gate+up expert quants (used in some GGUFs) lose ~50% token generation speed when experts split between GPU and CPU/RAM
- **Solution**: Use UNFUSED quant variants. The "UD" prefix in unsloth GGUFs may indicate unfused — need to verify
- **Takeaway**: The IQ3_XXS we're downloading has "UD" prefix = likely unfused = safe

### #20835 — 2-3x TG regression after b8323
- **Status**: OPEN
- **Impact**: We're on b8095 (pre-regression), so we're SAFE
- **Problem**: Qwen3.5-35B-A3B went from 194→62 tok/s on high-end GPU after b8323
- **Takeaway**: Do NOT update to builds between b8323 and whenever this is fixed
- **Our build b8095 is actually BETTER than latest for this model**

### #20596 — Improve --n-cpu-moe TG performance
- **Status**: OPEN
- **Impact**: 5-10% speedup pending
- **Problem**: Current --n-cpu-moe doesn't optimally schedule expert computation
- **Takeaway**: Will help when merged, but minor improvement

### #20757 — Two-tier GPU+RAM expert cache (PoC)
- **Status**: OPEN (feature request with PoC)
- **Impact**: MASSIVE — 12-14 tok/s vs 0.5-1 tok/s for swapped MoE
- **Problem**: Currently swapped experts page at NVMe speed (~779 MB/s), not cache speed
- **Takeaway**: Not yet merged. Would be game-changing for our setup.

## Strategy for 35B-A3B on 8GB Jetson

### Memory Layout
- Total RAM: 7.43 GiB
- llama.cpp overhead: ~300 MB
- KV cache (Q8_0, fewer GQA layers): ~100-150 MB
- Recurrent state (DeltaNet): ~50 MB
- Available for weights: ~6.93 GiB
- IQ3_XXS model: 12.18 GiB
- Overflow to swap: ~5.25 GiB

### MoE Weight Access Pattern
- 256 experts per layer, 9 active per token
- Expert selection varies per token → different experts hot/cold
- Active working set per token: ~1.4 GiB
- Hot set (shared + frequently used experts): ~2-3 GiB
- Cold experts: ~9 GiB (paged from NVMe on demand)

### Optimization Levers
1. **--n-gpu-layers**: Put ALL layers on GPU (unified memory handles paging)
2. **--mlock**: Lock shared weights in RAM, let OS page experts
3. **--no-mmap vs mmap**: mmap lets OS manage paging (may be better for MoE)
4. **--cpu-moe**: Run MoE expert computation on CPU instead of GPU
5. **--n-cpu-moe N**: Number of experts to run on CPU
6. **Context size**: Smaller = less KV cache = more room for weights
7. **KV Q8_0**: Reduces KV cache size
8. **ubatch-size**: Affects how many tokens processed per GPU batch

### Test Matrix
| Config | n_gpu_layers | mmap | mlock | cpu-moe | Expected Speed |
|--------|-------------|------|-------|---------|---------------|
| A: All GPU + mlock | 999 | no | yes | no | ? (baseline) |
| B: All GPU + mmap | 999 | yes | no | no | ? (OS manages paging) |
| C: Split offload | 20 | no | yes | no | ? (some layers on CPU) |
| D: CPU MoE experts | 999 | no | yes | yes | ? (experts on CPU) |
| E: Partial CPU MoE | 999 | no | yes | 128 | ? (half experts CPU) |

## Build Status
- Current: b8095 (pre-regression, SAFE)
- Latest: b8479 (has regression #20835, AVOID)
- Build from source: cmake + nvcc available in container
