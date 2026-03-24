# Model Selection Rationale

## Selected Default: Qwen3.5-4B Q8_0

Why this won on Orin Nano Super 8GB:
- Best quality/perf tradeoff under strict memory limits
- Sustained >8 tok/s floor (measured 10.5 tok/s)
- Excellent coding output quality and tool-call behavior
- Near-lossless quant (`Q8_0`) preserves quality

## Why Not Qwen3-8B Q4_K_M

Although larger parameter count, it underperformed in practical agentic/coding quality for this hardware profile and quant budget.

## Why Not 35B-A3B MoE

Empirically tested and rejected:
- CPU-MoE mode: ~0.18 tok/s
- Partial GPU offload: severe latency / swap pressure

Conclusion: On 8GB unified memory, dense 4B Q8_0 is the practical winner.
