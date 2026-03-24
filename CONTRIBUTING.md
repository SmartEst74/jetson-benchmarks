# Contributing

Thanks for helping Jetson users get better local LLM performance.

## Rules
- No dangerous startup paths (no `curl | bash`)
- No opaque short links in scripts
- Prefer explicit, reviewable commands
- Include benchmark evidence with each tuning claim

## Benchmark PR Checklist
- [ ] Device + JetPack version included
- [ ] Full startup command included
- [ ] `timings` JSON included
- [ ] Tegrastats snapshot included
- [ ] Median of 3 runs included
- [ ] Clear rollback path

## Add a Benchmark Row
Edit `benchmarks/benchmark-table.md` and include reproducible details.
