# Contributing

Thanks for helping Jetson users get better local LLM performance.

## Before You Contribute

**First time?** Read [docs/GETTING-STARTED.md](docs/GETTING-STARTED.md) to understand the project structure.

**Want to add a model?** Follow [docs/methodology.md](docs/methodology.md) for measurement rigor.

**Found a bug?** Check [docs/QUICK-START.md#if-something-goes-wrong](docs/QUICK-START.md#if-something-goes-wrong) first.

---

## Contribution Types

### 1. Add a New Model Benchmark

**What to do:**
1. Download the GGUF to your Jetson
2. Follow [docs/methodology.md](docs/methodology.md) exactly
3. Run the benchmarks using [scripts/bench-roles-live.py](scripts/bench-roles-live.py)
4. Record results in [benchmarks/current-performance.md](benchmarks/current-performance.md)
5. Submit a PR with:
   - Model name, GGUF size, quantization level
   - Generation speed (tok/s) with 3-run median
   - Temperature, context size, max tokens used
   - Role benchmark results (if applicable)
   - Hardware: Jetson model, JetPack version, power mode

**Checklist:**
- [ ] Model actually runs on 8GB without OOM
- [ ] Speed measured on clean state (service restarted, caches dropped)
- [ ] Temperature/thermal stability verified
- [ ] Measurement follows [docs/methodology.md](docs/methodology.md)
- [ ] Results reproducible (clear startup command + flags)

### 2. Improve Documentation

**What to do:**
1. Identify unclear, missing, or outdated sections
2. Improve the documentation following these principles:
   - **Beginner-friendly**: Explain *why* things matter, not just what to do
   - **Examples**: Include curl/Python examples when relevant
   - **Troubleshooting**: Add solutions to common problems
   - **Links**: Reference other docs that might be helpful

**Good documentation PR examples:**
- Add missing context to [docs/optimizations.md](docs/optimizations.md)
- Clarify a confusing section in [docs/methodology.md](docs/methodology.md)
- Add FAQ to [docs/QUICK-START.md](docs/QUICK-START.md)
- Update [docs/jetson-setup.md](docs/jetson-setup.md) for new JetPack versions

### 3. Fix a Bug or Performance Issue

**What to do:**
1. **Reproduce**: Follow [docs/methodology.md](docs/methodology.md) to verify the issue
2. **Root cause**: Identify the problem (check logs with `sudo journalctl -u jetson-bonsai-llm.service -f`)
3. **Fix**: Make the minimal change to fix it
4. **Validate**: Run benchmarks before/after to ensure no regression
5. **Submit PR** with:
   - Clear description of the bug
   - Before/after benchmark results
   - Steps to reproduce

**Common issues to fix:**
- Memory management (see [docs/optimizations.md#memory-leak-diagnosis](docs/optimizations.md#memory-leak-diagnosis))
- Context sizing (see [docs/optimizations.md#context-size-vs-performance-trade-off](docs/optimizations.md#context-size-vs-performance-trade-off))
- Docker/systemd integration issues

### 4. Contribute Scripts or Tools

**What to do:**
1. Script must solve a real problem (e.g., automated benchmarking, model switcher)
2. Must work on Jetson Orin Nano Super 8GB out of the box
3. Must follow shell best practices (no `curl | bash`, no opaque commands)
4. Must include comments explaining what it does
5. Must have error handling and clear failure messages
6. Add documentation to [docs/GETTING-STARTED.md](docs/GETTING-STARTED.md) or README.md

**Example:**
- ✅ [scripts/bench-roles-live.py](scripts/bench-roles-live.py) — Automated role benchmarking
- ✅ [scripts/start-ternary-bonsai.sh](scripts/start-ternary-bonsai.sh) — Standardized startup
- ❌ `curl api.example.com/setup.sh | bash` — Unsafe
- ❌ Undocumented Python script with no error handling

### 5. Optimize Performance (Advanced)

**Rules:**
- ✅ Must improve speed **without regressing quality metrics** on role benchmarks
- ✅ Must be reproducible on real hardware (Jetson Orin Nano Super 8GB)
- ✅ Must explain why the optimization works (not just \"I tried this and it was faster\")
- ✅ Document as \"Safe Next Optimizations\" in [docs/optimizations.md](docs/optimizations.md)
- ❌ GPU overclocking (not reproducible across units)
- ❌ Changes that improve speed but break tool-use accuracy
- ❌ Undocumented flags or configurations

**Optimization PR template:**
```
Title: [OPTIMIZATION] Brief description

Before:
- Speed: X tok/s
- Quality: [role scores]
- Memory: Y GB

After:
- Speed: X' tok/s (+Z%)
- Quality: [role scores]
- Memory: Y' GB

Mechanism:
- Explain why this works

Command:
[exact startup command with all flags]

Validation:
- Run 1: ...
- Run 2: ...
- Run 3: ...
- Median: ...
```

---

## Code Standards

### Shell Scripts

**DO:**
- Use `set -e` to exit on errors
- Quote variables: `\"$var\"`
- Comment complex logic
- Include usage/help text
- Handle missing files gracefully

**DON'T:**
- Use `curl | bash` or similar
- Hide what commands are doing
- Assume specific directory structure
- Ignore errors silently

### Python Scripts

**DO:**
- Use type hints
- Include docstrings
- Handle exceptions
- Use argparse for CLI tools
- Log clearly with timestamps

**DON'T:**
- Use global state
- Make assumptions about paths
- Ignore stderr
- Print debugging to stdout

### Documentation

**DO:**
- Use clear headings
- Include examples (curl, Python, bash)
- Link to related docs
- Explain the \"why\" not just the \"how\"
- Include troubleshooting sections

**DON'T:**
- Assume reader's skill level (explain terms)
- Use passive voice excessively
- Leave broken links
- Include outdated information

---

## Benchmark PR Checklist

Before submitting a benchmark PR, verify:

- [ ] **Device**: Jetson Orin Nano Super 8GB (or clearly note if different)
- [ ] **JetPack**: Version 6.2 (or note version used)
- [ ] **Startup command**: Full, reproducible command with all flags
- [ ] **Memory state**: Service restarted before benchmarking
- [ ] **Temperature**: GPU < 60°C during measurement
- [ ] **Thermal stability**: No throttling observed (check `nvidia-smi`)
- [ ] **Clean state**: `free -h` shows expected memory, no swap usage
- [ ] **Measurements**: 3 runs, report median
- [ ] **Speed metric**: Generation tokens/sec (from llama.cpp `timings`)
- [ ] **Power mode**: MAXN_SUPER (`sudo nvpmodel -m 2 && sudo jetson_clocks`)
- [ ] **Model hash**: Include GGUF SHA256 or URL
- [ ] **Role scores**: If applicable, full role benchmark results
- [ ] **Rollback path**: Clear if something needs reverting

---

## How to Submit a PR

1. **Fork** the repository
2. **Create a branch**: `git checkout -b feature/your-feature-name`
3. **Make changes**: Edit files, add benchmarks, etc.
4. **Validate**: Run `bash -n scripts/*.sh` for syntax checks
5. **Test**: Verify on actual Jetson if possible
6. **Commit**: Clear commit messages (`Add Qwen3.5-4B benchmark results`)
7. **Push**: `git push origin feature/your-feature-name`
8. **Open PR**: Include:
   - What you changed and why
   - Benchmark results (if applicable)
   - Any known limitations

---

## Getting Help

- **Setup questions**: See [docs/GETTING-STARTED.md](docs/GETTING-STARTED.md)
- **Benchmark methodology**: See [docs/methodology.md](docs/methodology.md)
- **Performance tuning**: See [docs/optimizations.md](docs/optimizations.md)
- **Quick troubleshooting**: See [docs/QUICK-START.md#if-something-goes-wrong](docs/QUICK-START.md#if-something-goes-wrong)
- **Project structure**: See [README.md](README.md#platform-features)

---

## License

By contributing, you agree that your contributions will be licensed under the same license as the repository.

---

## Safety & Ethics

- ✅ Focus on real hardware performance measurement
- ✅ Include evidence for all claims
- ✅ Document failure modes and limitations
- ✅ Prioritize user safety over benchmark gains
- ❌ No dangerous defaults (e.g., elevated privileges without explanation)
- ❌ No claims unsupported by data
- ❌ No contributions that bypass safety guardrails
