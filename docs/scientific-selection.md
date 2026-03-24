# Methodical Model Selection

This project selects models using two evidence classes:

1. Hardware-measured metrics on Jetson
- generation tokens/sec
- prompt tokens/sec
- memory/swap behavior
- thermal behavior

2. External benchmark signals
- BFCL (tool/function-calling capability)
- Provider-reported evals (e.g., LiveCodeBench, GPQA, IFEval)

## Why Qwen3.5-4B Q8_0 was selected

- Highest practical capability-per-GB for this 8GB device profile
- Verified >8 tok/s floor while preserving coding/tool quality
- Strong BFCL + provider metrics relative to tested alternatives

## About "loss" values

Provider model cards and BFCL typically publish task/eval scores rather than direct comparable training loss values. This repo therefore uses standardized public eval scores as scientific comparators, and reports measured runtime performance separately.

If a model provider publishes reproducible held-out loss with matching conditions, we can add those columns.
