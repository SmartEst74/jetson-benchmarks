#!/usr/bin/env python3
"""
Full benchmark suite for Ternary-Bonsai-8B Q2_0 on Jetson Orin Nano Super 8GB.

Phases:
  1. Speed tests — 3 runs each, think + no_think, median reported
  2. Role benchmarks — 8 roles × 2 modes (think / no_think), 4096 tokens
  3. Hardware stats — tegrastats snapshot via SSH at peak load

API expected at http://localhost:8001/v1  (SSH tunnel to Jetson:8001)
Jetson SSH target: jetson@192.168.1.163

Usage:
  python3 bench-ternary-bonsai.py [--phases speed,roles,hw] [--out /tmp/tb-results]
"""

import json
import time
import subprocess
import sys
import os
import argparse
from statistics import median, mean, stdev

# ── Config ────────────────────────────────────────────────────────────────────
API      = "http://localhost:8001/v1/chat/completions"
MODELS   = "http://localhost:8001/v1/models"
HEALTH   = "http://localhost:8001/health"
MODEL    = "ternary-bonsai-8b"
JETSON   = "jetson@192.168.1.163"
OUT      = "/tmp/tb-results"
SPEED_RUNS = 3

# ── Prompts ───────────────────────────────────────────────────────────────────
SPEED_PROMPT = (
    "Write a Python function that implements a binary search tree with insert, "
    "delete, and search operations. Include type hints and docstrings."
)

ROLES = {
    "frontend_developer": (
        "Build a React TypeScript component for a virtualized data table with 10,000+ rows. "
        "Requirements: sortable columns (click header to toggle asc/desc), filterable with "
        "search input, proper ARIA labels, keyboard navigation between rows, responsive "
        "(stacks on mobile). Use @tanstack/react-virtual. Include full component code with types."
    ),
    "backend_architect": (
        "Design a PostgreSQL schema for a multi-tenant SaaS project management tool. "
        "Requirements: tenant isolation via row-level security, projects with tasks "
        "(nested subtasks), team members with roles (admin/manager/member), activity "
        "audit log. Include CREATE TABLE statements with proper types, indexes for common "
        "queries, and RLS policies."
    ),
    "code_reviewer": (
        "Review this Python endpoint for ALL issues. Use priority markers (blocker/suggestion/nit):\n\n"
        "@app.route('/api/query', methods=['POST'])\n"
        "def query():\n"
        "    data = request.json\n"
        "    sql = f\"SELECT * FROM users WHERE name = '{data['name']}' AND role = '{data['role']}'\"\n"
        "    result = db.execute(sql)\n"
        "    token = jwt.encode({'user': data['name']}, 'secret123', algorithm='HS256')\n"
        "    response = make_response(jsonify({'data': result.fetchall(), 'token': token}))\n"
        "    response.headers['Access-Control-Allow-Origin'] = '*'\n"
        "    return response"
    ),
    "security_engineer": (
        "Perform a STRIDE threat model for this architecture: A Jetson edge device runs an "
        "LLM inference API (HTTP, port 8000) on a local network. Users SSH in to manage models. "
        "A hot-swap API (port 8001) switches models. Models stored on NVMe. No firewall configured. "
        "IoT devices on same subnet. For each STRIDE category, identify at least 2 threats with "
        "severity and mitigations."
    ),
    "technical_writer": (
        "Write a README.md for a tool called jetson-bench. Include: project title, one-line "
        "description, badge placeholders, prerequisites (JetPack 6.2+, Docker, 8GB+ RAM), "
        "install section, usage with 3 example commands and output, configuration table "
        "(6+ options), troubleshooting with 3 issues, contributing link, MIT license. Under 180 lines."
    ),
    "ai_engineer": (
        "Design an inference optimization pipeline for a 4B parameter LLM on Jetson Orin Nano "
        "Super (8GB unified RAM, 1024 CUDA cores SM 8.7, 68 GB/s bandwidth). Cover: quantization "
        "strategy (GPTQ vs AWQ vs GGUF), KV cache management for 8K context, batching strategy, "
        "thermal management, memory budget breakdown with specific numbers."
    ),
    "performance_benchmarker": (
        "Analyze LLM inference data: Jetson Orin Nano 8GB, Qwen3.5-4B Q8_0 (4.48GB), llama.cpp. "
        "5 runs: Gen 10.2-10.6 tok/s, Prompt 245-261 tok/s, RAM 6.1 GiB, Temp 58-65C. "
        "Theoretical limit 15.2 tok/s, actual efficiency 68.4%. Explain the efficiency gap, "
        "bottleneck, thermal trend, and optimization recommendations."
    ),
    "api_tester": (
        "Generate a pytest test suite for an OpenAI-compatible LLM API at localhost:8000/v1. "
        "Endpoints: POST /v1/chat/completions, GET /v1/models. Cover: happy path, input "
        "validation (missing messages, invalid model, empty array), error handling, performance "
        "(response under 30s), security (proper headers). Use pytest with clear names."
    ),
}

# ── Helpers ───────────────────────────────────────────────────────────────────
import urllib.request

def api_post(messages, max_tokens=512, temperature=0.6):
    payload = json.dumps({
        "model": MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False
    }).encode()
    req = urllib.request.Request(
        API, data=payload, headers={"Content-Type": "application/json"}
    )
    t0 = time.monotonic()
    with urllib.request.urlopen(req, timeout=600) as resp:
        data = json.loads(resp.read())
    wall = time.monotonic() - t0
    return data, wall


def extract_metrics(data, wall):
    timings = data.get("timings", {})
    usage   = data.get("usage", {})
    choice  = data.get("choices", [{}])[0]
    msg     = choice.get("message", {})
    thinking = msg.get("reasoning_content", "") or ""
    content  = msg.get("content", "") or ""
    return {
        "gen_tok_s":    round(timings.get("predicted_per_second") or
                              (usage.get("completion_tokens", 0) / wall if wall else 0), 2),
        "prompt_tok_s": round(timings.get("prompt_per_second") or 0, 2),
        "gen_tokens":   timings.get("predicted_n") or usage.get("completion_tokens", 0),
        "prompt_tokens": timings.get("prompt_n") or usage.get("prompt_tokens", 0),
        "wall_s":       round(wall, 2),
        "finish_reason": choice.get("finish_reason", "unknown"),
        "thinking_chars": len(thinking),
        "response_chars": len(content),
        "thinking_preview": thinking[:800],
        "response_preview": content[:800],
    }


def ssh_cmd(cmd, timeout=15):
    r = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", JETSON, cmd],
        capture_output=True, text=True, timeout=timeout
    )
    return r.returncode, r.stdout.strip()


def banner(msg, width=60):
    print(f"\n{'='*width}")
    print(f"  {msg}")
    print(f"{'='*width}")


# ── Phase 1: Speed tests ──────────────────────────────────────────────────────
def run_speed_tests(out_dir):
    banner("PHASE 1 — Speed Tests")
    results = {"think": [], "no_think": []}

    for mode in ("think", "no_think"):
        print(f"\n  Mode: {mode}  ({SPEED_RUNS} runs)")
        for run_i in range(SPEED_RUNS):
            prompt = SPEED_PROMPT if mode == "think" else f"/no_think\n\n{SPEED_PROMPT}"
            try:
                data, wall = api_post(
                    [{"role": "user", "content": prompt}], max_tokens=512
                )
                m = extract_metrics(data, wall)
                results[mode].append(m)
                print(f"    run {run_i+1}: gen={m['gen_tok_s']} tok/s  "
                      f"prompt={m['prompt_tok_s']} tok/s  "
                      f"tokens={m['gen_tokens']}  wall={m['wall_s']}s  "
                      f"finish={m['finish_reason']}")
            except Exception as e:
                print(f"    run {run_i+1}: ERROR — {e}")
                results[mode].append({"error": str(e)})

    summary = {}
    for mode in ("think", "no_think"):
        good = [r for r in results[mode] if "error" not in r]
        if good:
            gens = [r["gen_tok_s"] for r in good]
            prompts = [r["prompt_tok_s"] for r in good]
            summary[mode] = {
                "gen_tok_s_median":  round(median(gens), 2),
                "gen_tok_s_mean":    round(mean(gens), 2),
                "gen_tok_s_stdev":   round(stdev(gens), 3) if len(gens) > 1 else 0,
                "prompt_tok_s_median": round(median(prompts), 2),
                "runs": len(good),
            }
            print(f"\n  {mode} MEDIAN:  gen={summary[mode]['gen_tok_s_median']} tok/s  "
                  f"prompt={summary[mode]['prompt_tok_s_median']} tok/s  "
                  f"(stdev={summary[mode]['gen_tok_s_stdev']})")

    with open(f"{out_dir}/speed_tests.json", "w") as f:
        json.dump({"raw": results, "summary": summary}, f, indent=2)
    print(f"\n  Speed results → {out_dir}/speed_tests.json")
    return summary


# ── Phase 2: Role benchmarks ──────────────────────────────────────────────────
def run_role_benchmarks(out_dir):
    banner("PHASE 2 — Role Benchmarks (8 roles × 2 modes)")
    all_results = []

    for role_i, (role, prompt) in enumerate(ROLES.items()):
        print(f"\n  [{role_i+1}/{len(ROLES)}] {role}")
        role_data = {"role": role}

        for mode in ("think", "no_think"):
            user_msg = prompt if mode == "think" else f"/no_think\n\n{prompt}"
            msgs = [
                {"role": "system", "content": "You are a helpful assistant acting as a specialized agent."},
                {"role": "user",   "content": user_msg},
            ]
            print(f"    {mode:<10} ...", end="", flush=True)
            try:
                data, wall = api_post(msgs, max_tokens=4096)
                m = extract_metrics(data, wall)
                m["role"] = role
                m["mode"] = mode
                role_data[mode] = m
                print(f" {m['gen_tok_s']} tok/s  thinking={m['thinking_chars']}ch  "
                      f"response={m['response_chars']}ch  {m['finish_reason']}")

                # Save full response text
                with open(f"{out_dir}/{role}_{mode}.txt", "w") as f:
                    if m["thinking_preview"]:
                        f.write("=== THINKING ===\n")
                        f.write(m["thinking_preview"] + "\n\n")
                    f.write("=== RESPONSE ===\n")
                    f.write(m["response_preview"])
                with open(f"{out_dir}/{role}_{mode}.json", "w") as f:
                    json.dump(m, f, indent=2)
            except Exception as e:
                print(f" ERROR — {e}")
                role_data[mode] = {"error": str(e), "role": role, "mode": mode}

        all_results.append(role_data)

    with open(f"{out_dir}/roles_all.json", "w") as f:
        json.dump({"model": MODEL, "date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                   "results": all_results}, f, indent=2)
    print(f"\n  Role results → {out_dir}/roles_all.json")
    return all_results


# ── Phase 3: Hardware stats ───────────────────────────────────────────────────
def capture_hw_stats(out_dir):
    banner("PHASE 3 — Hardware Stats (tegrastats snapshot)")
    hw = {}

    # Trigger a generation request in background to load GPU, then sample
    def start_bg():
        try:
            api_post([{"role": "user", "content":
                "Write a detailed 500-word essay about transformer architecture."}],
                max_tokens=300)
        except:
            pass

    import threading
    t = threading.Thread(target=start_bg, daemon=True)
    t.start()
    time.sleep(4)  # let it warm up

    # tegrastats snapshot (5 samples, 1s apart)
    code, out = ssh_cmd(
        "timeout 5 tegrastats --interval 1000 2>/dev/null | head -5", timeout=12
    )
    hw["tegrastats_raw"] = out if code == 0 else None

    # RAM
    code, out = ssh_cmd("free -m | grep Mem")
    if code == 0 and out:
        parts = out.split()
        hw["ram_total_mb"]  = int(parts[1]) if len(parts) > 1 else None
        hw["ram_used_mb"]   = int(parts[2]) if len(parts) > 2 else None
        hw["ram_avail_mb"]  = int(parts[6]) if len(parts) > 6 else None

    # GPU temp
    code, out = ssh_cmd("cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null")
    if code == 0 and out:
        try: hw["gpu_temp_c"] = int(out) / 1000
        except: pass

    # Swap
    code, out = ssh_cmd("free -m | grep Swap")
    if code == 0 and out:
        parts = out.split()
        hw["swap_total_mb"] = int(parts[1]) if len(parts) > 1 else None
        hw["swap_used_mb"]  = int(parts[2]) if len(parts) > 2 else None

    # llama-server process RAM
    code, out = ssh_cmd(
        "ps -o pid,rss,vsz,comm -p $(pgrep -f 'llama-server.*8001' | head -1) 2>/dev/null | tail -1"
    )
    hw["server_process"] = out if code == 0 else None

    t.join(timeout=30)

    with open(f"{out_dir}/hw_stats.json", "w") as f:
        json.dump(hw, f, indent=2)

    print(f"  RAM used:    {hw.get('ram_used_mb', '?')} / {hw.get('ram_total_mb', '?')} MB")
    print(f"  Swap used:   {hw.get('swap_used_mb', '?')} MB")
    print(f"  GPU temp:    {hw.get('gpu_temp_c', '?')} °C")
    if hw.get("server_process"):
        print(f"  Server proc: {hw['server_process']}")
    print(f"  HW stats → {out_dir}/hw_stats.json")
    return hw


# ── Summary printer ───────────────────────────────────────────────────────────
def print_summary(speed_summary, role_results, hw):
    banner("BENCHMARK COMPLETE — SUMMARY")

    print(f"\n  Model:   {MODEL}")
    print(f"  Date:    {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}")
    print(f"  Device:  Jetson Orin Nano Super 8GB | JetPack 6.2")
    print(f"  Runtime: PrismML llama.cpp fork (GPU -ngl 999, flash-attn on)")

    if speed_summary:
        print(f"\n  SPEED (3-run median, BST prompt, 512 tokens)")
        for mode, s in speed_summary.items():
            print(f"    {mode:<10}: gen={s['gen_tok_s_median']} tok/s  "
                  f"prompt={s['prompt_tok_s_median']} tok/s")

    print(f"\n  ROLE BENCHMARKS (tok/s generation)")
    print(f"  {'Role':<25} {'Think':>10} {'No-Think':>10} {'Think resp':>12} {'NoThink resp':>12}")
    print(f"  {'-'*25} {'-'*10} {'-'*10} {'-'*12} {'-'*12}")
    for rd in role_results:
        role = rd["role"]
        t = rd.get("think", {})
        nt = rd.get("no_think", {})
        tg = f"{t.get('gen_tok_s', '?')}" if "error" not in t else "ERR"
        ntg = f"{nt.get('gen_tok_s', '?')}" if "error" not in nt else "ERR"
        tr = f"{t.get('response_chars', 0)}" if "error" not in t else "-"
        ntr = f"{nt.get('response_chars', 0)}" if "error" not in nt else "-"
        print(f"  {role:<25} {tg:>10} {ntg:>10} {tr:>12} {ntr:>12}")

    if hw:
        print(f"\n  HARDWARE (peak load)")
        print(f"    RAM:  {hw.get('ram_used_mb', '?')} MB used / "
              f"{hw.get('ram_total_mb', '?')} MB total")
        print(f"    Swap: {hw.get('swap_used_mb', '?')} MB used")
        print(f"    Temp: {hw.get('gpu_temp_c', '?')} °C")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phases", default="speed,roles,hw",
                    help="Comma-separated phases: speed,roles,hw")
    ap.add_argument("--out", default=OUT)
    args = ap.parse_args()

    phases = [p.strip() for p in args.phases.split(",")]
    out_dir = args.out
    os.makedirs(out_dir, exist_ok=True)

    # Health check
    try:
        req = urllib.request.Request(HEALTH)
        with urllib.request.urlopen(req, timeout=5) as resp:
            h = json.loads(resp.read())
        print(f"Health: {h}")
    except Exception as e:
        print(f"ERROR: Cannot reach {HEALTH} — {e}")
        print("Make sure SSH tunnel is active: ssh -f -N -L 8001:localhost:8001 jetson@192.168.1.163")
        sys.exit(1)

    speed_summary = {}
    role_results  = []
    hw            = {}

    if "speed" in phases:
        speed_summary = run_speed_tests(out_dir)

    if "roles" in phases:
        role_results = run_role_benchmarks(out_dir)

    if "hw" in phases:
        hw = capture_hw_stats(out_dir)

    print_summary(speed_summary, role_results, hw)

    # Save master summary
    with open(f"{out_dir}/summary.json", "w") as f:
        json.dump({
            "model": MODEL,
            "date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "speed": speed_summary,
            "hw": hw,
        }, f, indent=2)
    print(f"\n  All results in {out_dir}/")


if __name__ == "__main__":
    main()
