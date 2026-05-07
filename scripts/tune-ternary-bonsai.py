#!/usr/bin/env python3
"""
Ternary-Bonsai-8B Q2_0 — llama.cpp flag optimisation tuner.

Applies the techniques from Codacus "Running a 35B AI Model on 6GB VRAM, FAST":
  • --mlock + --no-mmap  (stability & memory-lock; key 3→17 tok/s technique)
  • KV-cache quantisation  (-ctk / -ctv  q8_0 → q4_0; the "4× context trick")
  • Batch/ubatch tuning
  • RoPE context extension (yarn/linear scaling for 8K–16K ctx)

Goal: reach 20 tok/s generation with a large context window.

The script:
  1. Kills any running llama-server on port 8001
  2. Starts server with the candidate config
  3. Runs 3-run speed measurement
  4. Saves results, prints winner, updates start-ternary-bonsai.sh

Usage:
  python3 scripts/tune-ternary-bonsai.py [--target 20] [--ssh jetson@192.168.1.163]
"""

import json, time, subprocess, sys, os, argparse, urllib.request
from statistics import median

# ── Config ────────────────────────────────────────────────────────────────────
JETSON      = "jetson@192.168.1.163"
JETSON_HOME = "/home/jetson"
MODEL_PATH  = f"{JETSON_HOME}/models/llama-cache/Ternary-Bonsai-8B-Q2_0.gguf"
PRISM_DIR   = f"{JETSON_HOME}/prism-llama"
PORT       = 8001
LOCAL_API  = f"http://localhost:{PORT}/v1/chat/completions"
HEALTH     = f"http://localhost:{PORT}/health"
OUT        = "/tmp/tb-tune"
RUNS       = 3
SPEED_PROMPT = (
    "Write a Python function that implements a binary search tree with insert, "
    "delete, and search operations. Include type hints and docstrings."
)

# ── Candidate configurations ──────────────────────────────────────────────────
# Each dict is merged with BASE_FLAGS. Order matters: test cheap wins first.
BASE_FLAGS = {
    "--alias":   "ternary-bonsai-8b",
    "--host":    "0.0.0.0",
    "--port":    str(PORT),
    "--threads": "6",
    "-ngl":      "999",
    "-fa":       "on",
}

CONFIGS = [
    # 0 — baseline (current production)
    {
        "name":  "baseline",
        "notes": "Current production config (no memory flags)",
        "--ctx-size": "4096",
    },
    # 1 — mlock + no-mmap  (Codacus technique #1 — eliminates mmap page faults)
    {
        "name":   "mlock_nommap",
        "notes":  "mlock + no-mmap: prevents swapping, contiguous memory",
        "--ctx-size": "4096",
        "--mlock": None,   # flag with no value
        "--no-mmap": None,
    },
    # 2 — mlock + no-mmap + q8_0 KV cache  (Codacus technique #2)
    {
        "name":   "mlock_nommap_kv8",
        "notes":  "mlock + no-mmap + q8_0 KV: halves KV bandwidth",
        "--ctx-size": "4096",
        "--mlock": None,
        "--no-mmap": None,
        "-ctk": "q8_0",
        "-ctv": "q8_0",
    },
    # 3 — q4_0 KV cache: 4× context trick (halves memory vs q8_0)
    {
        "name":   "mlock_nommap_kv4",
        "notes":  "mlock + no-mmap + q4_0 KV: 4× KV compression",
        "--ctx-size": "4096",
        "--mlock": None,
        "--no-mmap": None,
        "-ctk": "q4_0",
        "-ctv": "q4_0",
    },
    # 4 — q4_0 KV + 8K context (enabled by KV compression)
    {
        "name":   "kv4_ctx8k",
        "notes":  "q4_0 KV + 8192 ctx: large context without OOM",
        "--ctx-size": "8192",
        "--mlock": None,
        "--no-mmap": None,
        "-ctk": "q4_0",
        "-ctv": "q4_0",
    },
    # 5 — batch tuning: larger batch for better GPU pipeline utilisation
    {
        "name":   "kv4_ctx8k_batch",
        "notes":  "8K ctx + q4_0 KV + batch-size 2048 ubatch 256",
        "--ctx-size": "8192",
        "--mlock": None,
        "--no-mmap": None,
        "-ctk": "q4_0",
        "-ctv": "q4_0",
        "-b":   "2048",
        "-ub":  "256",
    },
    # 6 — q4_0 KV + 16K context via RoPE YaRN scaling
    {
        "name":   "kv4_ctx16k_yarn",
        "notes":  "16K ctx via YaRN RoPE scaling + q4_0 KV",
        "--ctx-size": "16384",
        "--mlock": None,
        "--no-mmap": None,
        "-ctk": "q4_0",
        "-ctv": "q4_0",
        "--rope-scaling": "yarn",
        "--yarn-orig-ctx": "32768",  # Qwen3 trained on 32K
        "-b":   "2048",
        "-ub":  "256",
    },
    # 7 — q4_0 KV + 8K + fewer threads (4 big cores only)
    {
        "name":   "kv4_ctx8k_t4",
        "notes":  "8K ctx + q4_0 KV + 4 threads (big-core only)",
        "--ctx-size": "8192",
        "--mlock": None,
        "--no-mmap": None,
        "-ctk": "q4_0",
        "-ctv": "q4_0",
        "--threads": "4",
        "-b":   "2048",
        "-ub":  "256",
    },
]


# ── Helpers ───────────────────────────────────────────────────────────────────
def ssh(cmd, timeout=30):
    r = subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "ServerAliveInterval=5",
                        JETSON, cmd],
                       capture_output=True, text=True, timeout=timeout)
    return r.returncode, r.stdout.strip()


def build_server_cmd(cfg):
    flags = dict(BASE_FLAGS)
    for k, v in cfg.items():
        if k in ("name", "notes"): continue
        flags[k] = v
    parts = [f"{PRISM_DIR}/build/bin/llama-server",
             "--model", MODEL_PATH]
    for k, v in flags.items():
        parts.append(k)
        if v is not None:
            parts.append(v)
    return " ".join(parts)


def start_server(cfg):
    """Kill existing server, start new one with config, return PID."""
    # Kill by port - avoids pkill pattern matching killing the SSH session itself
    ssh("fuser -k 8001/tcp 2>/dev/null; sleep 2")
    cmd_parts = build_server_cmd(cfg).split()
    # Python start_new_session=True (setsid equivalent) properly detaches the
    # process so the SSH session closes immediately. All paths are absolute.
    launch = (
        f"python3 -c \""
        f"import subprocess; "
        f"env=dict(__import__('os').environ); "
        f"env['LD_LIBRARY_PATH']='{PRISM_DIR}/build/bin'; "
        f"logf=open('/tmp/ternary-bonsai-server.log','w'); "
        f"p=subprocess.Popen({repr(cmd_parts)}, stdin=subprocess.DEVNULL, "
        f"stdout=logf, stderr=subprocess.STDOUT, start_new_session=True, env=env); "
        f"print(p.pid)"
        f"\""
    )
    code, pid = ssh(launch, timeout=15)
    return pid.strip()


def wait_ready(timeout_s=120):
    """Poll /health until ok or timeout."""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        try:
            req = urllib.request.Request(HEALTH)
            with urllib.request.urlopen(req, timeout=3) as r:
                if b"ok" in r.read():
                    return True
        except Exception:
            pass
        time.sleep(2)
    return False


def measure_speed(mode="no_think", max_tokens=512):
    """Return gen_tok_s or None on error."""
    prompt = SPEED_PROMPT if mode == "think" else f"/no_think\n\n{SPEED_PROMPT}"
    payload = json.dumps({
        "model": "ternary-bonsai-8b",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.6,
        "max_tokens": max_tokens,
        "stream": False,
    }).encode()
    req = urllib.request.Request(
        LOCAL_API, data=payload, headers={"Content-Type": "application/json"}
    )
    try:
        t0 = time.monotonic()
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
        wall = time.monotonic() - t0
        timings = data.get("timings", {})
        usage   = data.get("usage", {})
        gen = timings.get("predicted_per_second") or \
              (usage.get("completion_tokens", 0) / wall if wall else 0)
        prompt_s = timings.get("prompt_per_second", 0)
        tokens = timings.get("predicted_n") or usage.get("completion_tokens", 0)
        return round(gen, 2), round(prompt_s, 2), tokens
    except Exception as e:
        return None, None, f"ERR: {e}"


def banner(msg, width=62):
    print(f"\n{'='*width}\n  {msg}\n{'='*width}")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", type=float, default=20.0,
                    help="Stop as soon as this gen tok/s is reached (default 20)")
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--ssh", default=JETSON)
    ap.add_argument("--configs", default="all",
                    help="Comma-separated config indices to run, or 'all'")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)

    # Make sure tunnel is up
    try:
        urllib.request.urlopen(HEALTH, timeout=3)
        print("Tunnel already active.")
    except Exception:
        print("Re-establishing SSH tunnel...")
        subprocess.run(["pkill", "-f", "ssh.*L 8001.*8001"], capture_output=True)
        subprocess.Popen(["ssh", "-f", "-N", f"-L{PORT}:localhost:{PORT}", JETSON])
        time.sleep(2)

    if args.configs == "all":
        indices = list(range(len(CONFIGS)))
    else:
        indices = [int(x) for x in args.configs.split(",")]

    all_results = []
    best = {"gen_tok_s": 0, "config": None}

    for idx in indices:
        cfg = CONFIGS[idx]
        banner(f"Config [{idx}]: {cfg['name']}")
        print(f"  {cfg['notes']}")
        print(f"  Server cmd: {build_server_cmd(cfg)}")
        print()

        # Start server
        print("  Starting server...", flush=True)
        pid = start_server(cfg)
        time.sleep(3)
        if not wait_ready(timeout_s=90):
            print("  FAILED: server did not become ready")
            # Grab log tail
            _, log = ssh("tail -10 /tmp/ternary-bonsai-server.log 2>/dev/null")
            print(f"  Log:\n{log}")
            all_results.append({"config": cfg["name"], "status": "failed_start",
                                "notes": cfg["notes"]})
            continue
        print(f"  Ready (PID {pid})", flush=True)

        # 3-run speed measurement (no_think mode for clean speed)
        runs = []
        print(f"  Measuring ({RUNS} runs, max_tokens=512, no_think) ...")
        for i in range(RUNS):
            gen, prompt_s, tokens = measure_speed(mode="no_think", max_tokens=512)
            if gen is not None:
                runs.append((gen, prompt_s))
                print(f"    run {i+1}: gen={gen} tok/s  prompt={prompt_s} tok/s  tokens={tokens}")
            else:
                print(f"    run {i+1}: FAILED — {tokens}")

        if not runs:
            print("  All runs failed.")
            all_results.append({"config": cfg["name"], "status": "all_runs_failed",
                                "notes": cfg["notes"]})
            continue

        gen_med   = round(median([r[0] for r in runs]), 2)
        prom_med  = round(median([r[1] for r in runs]), 2)
        result = {
            "config":         cfg["name"],
            "notes":          cfg["notes"],
            "ctx_size":       cfg.get("--ctx-size", "default"),
            "kv_type":        cfg.get("-ctk", "fp16"),
            "mlock":          "--mlock"   in cfg,
            "no_mmap":        "--no-mmap" in cfg,
            "gen_tok_s":      gen_med,
            "prompt_tok_s":   prom_med,
            "runs":           runs,
            "status":         "ok",
        }
        all_results.append(result)

        print(f"\n  ► MEDIAN: gen={gen_med} tok/s  prompt={prom_med} tok/s")
        if gen_med > best["gen_tok_s"]:
            best = {"gen_tok_s": gen_med, "config": cfg["name"], "result": result}
            print(f"  ★ NEW BEST")

        if gen_med >= args.target:
            print(f"\n  TARGET {args.target} tok/s REACHED!")

        # Save per-config result
        with open(f"{args.out}/tune_{cfg['name']}.json", "w") as f:
            json.dump(result, f, indent=2)

        if gen_med >= args.target:
            print("  Stopping early — target met.")
            break

    # ── Final summary ─────────────────────────────────────────────────────────
    banner("TUNING SUMMARY")
    print(f"\n  {'Config':<28} {'Ctx':>6} {'KV':>6} {'Gen tok/s':>10} {'Prompt':>8}  Status")
    print(f"  {'-'*28} {'-'*6} {'-'*6} {'-'*10} {'-'*8}  ------")
    for r in all_results:
        if r.get("status") == "ok":
            flags = ("M" if r["mlock"] else " ") + ("N" if r["no_mmap"] else " ")
            print(f"  {r['config']:<28} {r['ctx_size']:>6} {r['kv_type']:>6} "
                  f"{r['gen_tok_s']:>10.2f} {r['prompt_tok_s']:>8.1f}  {flags}")
        else:
            print(f"  {r['config']:<28}  —  FAILED ({r['status']})")

    if best["config"]:
        print(f"\n  BEST: {best['config']}  →  {best['gen_tok_s']} tok/s")
        print(f"  Target ({args.target} tok/s): "
              f"{'REACHED ✓' if best['gen_tok_s'] >= args.target else 'NOT YET'}")

    with open(f"{args.out}/tune_summary.json", "w") as f:
        json.dump({"best": best, "results": all_results}, f, indent=2)
    print(f"\n  Results → {args.out}/")

    return best


if __name__ == "__main__":
    main()
