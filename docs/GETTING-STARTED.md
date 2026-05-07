# Getting Started: Choose Your Path

This repo has **production-ready LLM benchmarking** for the Jetson Orin Nano Super 8GB. The documentation is organized by skill level and use case.

## 🚀 Quick Paths

### "I Just Got a Jetson (Fresh)" → **30 Minutes**

1. Follow [docs/jetson-setup.md](docs/jetson-setup.md) (steps 1-7)
2. By the end, you'll have Ternary-Bonsai running on port 8001
3. Test it: `curl http://localhost:8001/health`

**You'll get**: Working LLM with 65K context, 11.8 tok/s, auto-restart on crash

---

### "I Already Have a Jetson Running" → **5 Minutes**

1. Read [docs/QUICK-START.md](docs/QUICK-START.md)
2. Test: `curl http://jetson-ip:8001/health`
3. Run a completion with curl or Python

**You'll get**: Know how to use the model and troubleshoot basic issues

---

### "I Want to Optimize Performance" → **1 Hour**

1. Read [docs/optimizations.md](docs/optimizations.md) to understand the trade-offs
2. Check [docs/QUICK-START.md](docs/QUICK-START.md#performance-by-context-size) for context vs. speed trade-offs
3. Adjust `CTX` environment variable in systemd service and restart
4. Measure with [docs/QUICK-START.md](docs/QUICK-START.md#advanced-custom-context-size)

**You'll get**: Know exactly which knobs to turn and why they matter

---

### "I'm Benchmarking Models" → **2 Hours**

1. Read [BENCHMARKS.md](BENCHMARKS.md) to understand what's been tested
2. Study [docs/methodology.md](docs/methodology.md) for measurement rigor
3. Use [scripts/bench-roles-live.py](scripts/bench-roles-live.py) to test new models
4. Document results in [benchmarks/current-performance.md](benchmarks/current-performance.md)

**You'll get**: Reproducible methodology + validated measurements on hardware

---

### "I'm Contributing Code" → **Before You Start**

1. Read [CONTRIBUTING.md](CONTRIBUTING.md) for project standards
2. Check [docs/jetson-setup.md](docs/jetson-setup.md#ternary-models-prismml-fork) if touching PrismML build
3. Review [docs/optimizations.md](docs/optimizations.md#what-not-to-change) for constraints
4. Run benchmarks before/after to validate no regression

**You'll get**: Know project conventions and validation requirements

---

## 📚 Documentation Map

### By Use Case

| I Want To... | Read This | Time |
|-------------|-----------|------|
| Get started from fresh | [docs/jetson-setup.md](docs/jetson-setup.md) | 30 min |
| Use the model today | [docs/QUICK-START.md](docs/QUICK-START.md) | 5 min |
| Squeeze more performance | [docs/optimizations.md](docs/optimizations.md) | 1 hour |
| Understand the measurements | [docs/methodology.md](docs/methodology.md) | 30 min |
| See what's been tested | [BENCHMARKS.md](BENCHMARKS.md) | 15 min |
| Understand the repo | [README.md](README.md) | 20 min |
| Deploy a new model | [scripts/bench-roles-live.py](scripts/bench-roles-live.py) + [ROADMAP.md](ROADMAP.md) | 2 hours |
| Contribute code | [CONTRIBUTING.md](CONTRIBUTING.md) | 20 min |

### By Skill Level

**Beginner:**
- Start: [docs/QUICK-START.md](docs/QUICK-START.md)
- Then: [docs/jetson-setup.md](docs/jetson-setup.md)
- Reference: [docs/optimizations.md](docs/optimizations.md#performance-tuning-what-actually-matters)

**Intermediate:**
- Start: [BENCHMARKS.md](BENCHMARKS.md)
- Then: [docs/optimizations.md](docs/optimizations.md)
- Deep dive: [docs/methodology.md](docs/methodology.md)

**Advanced:**
- Start: [docs/methodology.md](docs/methodology.md)
- Then: [scripts/bench-roles-live.py](scripts/bench-roles-live.py)
- Research: [docs/optimizations.md](docs/optimizations.md#safe-optimizations-to-explore-advanced)

---

## 🎯 Common Questions

### Q: Do I need a Jetson to use this repo?

**No.** All the documentation is public. You can:
- Read the methodology to apply it elsewhere
- Use the benchmark results to predict performance on other hardware
- Adapt the scripts for your own setup

If you don't have a Jetson yet, see [docs/jetson-setup.md](docs/jetson-setup.md#what-you-need) for hardware.

### Q: What if I have a different Jetson model (Orin NX, AGX)?

Most of this will work, but:
- **Orin NX 8GB**: Should work with 4K-8K context (less memory than Super)
- **Orin Nano 4GB**: Will need smaller models or lower context
- **AGX Orin 64GB**: Will support all models; follow the same setup

See [docs/jetson-setup.md#ternary-models-prismml-fork](docs/jetson-setup.md#ternary-models-prismml-fork) for PrismML-specific notes.

### Q: Can I use this with llama.cpp instead of Docker?

**Yes.** All the build and run instructions are in [docs/jetson-setup.md#ternary-models-prismml-fork](docs/jetson-setup.md#ternary-models-prismml-fork).

The Docker approach is simpler for beginners; llama.cpp from source is for power users.

### Q: How do I know if my setup is working correctly?

Run the validation in [docs/QUICK-START.md](docs/QUICK-START.md#verify-its-working):

```bash
curl http://jetson-ip:8001/health
sudo systemctl status jetson-bonsai-llm.service
free -h
```

All three should return healthy results.

### Q: What's the actual speed I should expect?

See [BENCHMARKS.md](BENCHMARKS.md#models-tested) for real measurements.

**TL;DR**: Ternary-Bonsai-8B runs at ~11.8 tok/s on MAXN_SUPER mode (GPU 1020 MHz).

### Q: Can I use this in production?

**Yes.** All the setup is production-ready:
- ✅ Auto-restart on crash
- ✅ Automatic memory recovery
- ✅ Health checks
- ✅ Consistent performance
- ✅ OOM protection

See [docs/jetson-setup.md#step-7-make-it-production-ready](docs/jetson-setup.md#step-7-make-it-production-ready-optional-but-recommended) for the systemd setup.

### Q: What if I want to use a different model?

1. Download a GGUF file to `~/models/llama-cache/`
2. Update `scripts/start-ternary-bonsai.sh` to point to it
3. Restart the service
4. Follow [docs/methodology.md](docs/methodology.md) to benchmark it

See [BENCHMARKS.md](BENCHMARKS.md#models-tested) for models we've already tested.

---

## 🛠 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| Service won't start | `sudo journalctl -u jetson-bonsai-llm.service -f` |
| Slow generation (< 10 tok/s) | Run `sudo nvpmodel -m 2 && sudo jetson_clocks` |
| Out of memory | `export CTX=16384` then restart |
| Connection refused on 8001 | `sudo fuser -k 8001/tcp && sudo systemctl restart jetson-bonsai-llm.service` |

For more help, see [docs/QUICK-START.md#if-something-goes-wrong](docs/QUICK-START.md#if-something-goes-wrong).

---

## 📊 What's Here

```
├── docs/
│   ├── QUICK-START.md         ← Start here (you are reading this!)
│   ├── jetson-setup.md        ← Hardware setup, 30 minutes
│   ├── optimizations.md       ← Performance tuning guide
│   ├── methodology.md         ← How we measure performance
│   ├── jetson-setup.md        ← Step-by-step hardware setup
│   └── sources.md             ← Where models come from
├── BENCHMARKS.md              ← All measured results
├── README.md                  ← Repo overview + champion models
├── ROLES.md                   ← The 8 agent roles we test
├── ROADMAP.md                 ← What's being tested next
├── CONTRIBUTING.md            ← How to contribute
├── scripts/
│   ├── start-ternary-bonsai.sh       ← Run the production model
│   ├── bench-roles-live.py           ← Benchmark all 8 roles
│   ├── bench-all-models.sh           ← Test multiple models
│   └── ... (other tools)
└── data/
    ├── agent-roles.json       ← Role definitions
    └── models.json            ← Model metadata
```

---

## 🚀 Next Steps

Pick one:

1. **Just want to test the model**: [docs/QUICK-START.md](docs/QUICK-START.md)
2. **Setting up from scratch**: [docs/jetson-setup.md](docs/jetson-setup.md)
3. **Optimizing performance**: [docs/optimizations.md](docs/optimizations.md)
4. **Understanding measurements**: [docs/methodology.md](docs/methodology.md)
5. **Exploring results**: [BENCHMARKS.md](BENCHMARKS.md)

---

## 💡 Pro Tips

- **Memory tips**: Always run `sudo systemctl restart jetson-bonsai-llm.service` before testing to get clean state. The service's ExecStartPre hook handles all memory cleanup automatically.
- **Speed tips**: Check GPU clock with `nvidia-smi` before benchmarking. Need max speed? Run `sudo nvpmodel -m 2 && sudo jetson_clocks`.
- **Context tips**: Start at 16384 tokens (balanced). If you need more reasoning, go to 65536. If you need speed, drop to 8192.
- **API tips**: The server is fully OpenAI-compatible. Use any OpenAI client library with `base_url="http://jetson-ip:8001/v1"`.

---

**Questions?** Check the relevant doc for your use case, or see [CONTRIBUTING.md](CONTRIBUTING.md#getting-help) for how to ask.
