#!/usr/bin/env python3
"""Run role-based benchmarks with proper thinking/content capture.
Tests each role with BOTH thinking and no_think modes.
Captures thinking_chars AND response_chars for each.
"""
import json, time, urllib.request, os, sys

API = "http://localhost:8000/v1/chat/completions"
MODEL = os.environ.get("MODEL", "Qwen3.5-4B-Q8_0.gguf")
OUT = "/tmp/bench-results"
os.makedirs(OUT, exist_ok=True)

ROLES = {
    "frontend_developer": "Build a React TypeScript component for a virtualized data table with 10,000+ rows. Requirements: sortable columns (click header to toggle asc/desc), filterable with search input, proper ARIA labels, keyboard navigation between rows, responsive (stacks on mobile). Use @tanstack/react-virtual. Include full component code with types.",
    
    "backend_architect": "Design a PostgreSQL schema for a multi-tenant SaaS project management tool. Requirements: tenant isolation via row-level security, projects with tasks (nested subtasks), team members with roles (admin/manager/member), activity audit log. Include CREATE TABLE statements with proper types, indexes for common queries, and RLS policies.",
    
    "code_reviewer": 'Review this Python endpoint for ALL issues. Use priority markers (blocker/suggestion/nit):\n\n@app.route(\'/api/query\', methods=[\'POST\'])\ndef query():\n    data = request.json\n    sql = f"SELECT * FROM users WHERE name = \'{data[\'name\']}\' AND role = \'{data[\'role\']}\'"\n    result = db.execute(sql)\n    token = jwt.encode({\'user\': data[\'name\']}, \'secret123\', algorithm=\'HS256\')\n    response = make_response(jsonify({\'data\': result.fetchall(), \'token\': token}))\n    response.headers[\'Access-Control-Allow-Origin\'] = \'*\'\n    return response',
    
    "security_engineer": "Perform a STRIDE threat model for this architecture: A Jetson edge device runs an LLM inference API (HTTP, port 8000) on a local network. Users SSH in to manage models. A hot-swap API (port 8001) switches models. Models stored on NVMe. No firewall configured. IoT devices on same subnet. For each STRIDE category, identify at least 2 threats with severity and mitigations.",
    
    "technical_writer": "Write a README.md for a tool called jetson-bench. Include: project title, one-line description, badge placeholders, prerequisites (JetPack 6.2+, Docker, 8GB+ RAM), install section, usage with 3 example commands and output, configuration table (6+ options), troubleshooting with 3 issues, contributing link, MIT license. Under 180 lines.",
    
    "ai_engineer": "Design an inference optimization pipeline for a 4B parameter LLM on Jetson Orin Nano Super (8GB unified RAM, 1024 CUDA cores SM 8.7, 68 GB/s bandwidth). Cover: quantization strategy (GPTQ vs AWQ vs GGUF), KV cache management for 8K context, batching strategy, thermal management, memory budget breakdown with specific numbers.",
    
    "performance_benchmarker": "Analyze LLM inference data: Jetson Orin Nano 8GB, Qwen3.5-4B Q8_0 (4.48GB), llama.cpp. 5 runs: Gen 10.2-10.6 tok/s, Prompt 245-261 tok/s, RAM 6.1 GiB, Temp 58-65C. Theoretical limit 15.2 tok/s, actual efficiency 68.4%. Explain the efficiency gap, bottleneck, thermal trend, and optimization recommendations.",
    
    "api_tester": "Generate a pytest test suite for an OpenAI-compatible LLM API at localhost:8000/v1. Endpoints: POST /v1/chat/completions, GET /v1/models. Cover: happy path, input validation (missing messages, invalid model, empty array), error handling, performance (response under 30s), security (proper headers). Use pytest with clear names.",
}

def run_test(role, prompt, mode="think", max_tokens=4096):
    """Run a single role test and capture thinking + response content."""
    # Build messages based on mode
    system_msg = "You are a helpful assistant acting as a specialized agent."
    user_msg = prompt
    
    if mode == "no_think":
        user_msg = "/no_think\n\n" + prompt
    
    payload = json.dumps({
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg}
        ],
        "temperature": 0.6,
        "max_tokens": max_tokens,
        "stream": False
    }).encode()
    
    req = urllib.request.Request(API, data=payload, headers={"Content-Type": "application/json"})
    
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            raw = json.loads(resp.read())
    except Exception as e:
        return {"error": str(e)}
    wall_ms = int((time.time() - t0) * 1000)
    
    timings = raw.get("timings", {})
    usage = raw.get("usage", {})
    choice = raw.get("choices", [{}])[0]
    msg = choice.get("message", {})
    
    thinking_content = msg.get("reasoning_content", "") or ""
    response_content = msg.get("content", "") or ""
    
    return {
        "role": role,
        "model": MODEL,
        "mode": mode,
        "max_tokens": max_tokens,
        "gen_tok_s": round(timings.get("predicted_per_second", 0), 2),
        "prompt_tok_s": round(timings.get("prompt_per_second", 0), 2),
        "gen_tokens": timings.get("predicted_n", usage.get("completion_tokens", 0)),
        "prompt_tokens": timings.get("prompt_n", usage.get("prompt_tokens", 0)),
        "wall_time_ms": wall_ms,
        "finish_reason": choice.get("finish_reason", "unknown"),
        "thinking_used": bool(thinking_content),
        "thinking_chars": len(thinking_content),
        "response_chars": len(response_content),
        "thinking_content": thinking_content[:500],  # First 500 chars for preview
        "response_preview": response_content[:500],
    }

print(f"=== Jetson Role Benchmark (Enhanced) ===")
print(f"Model: {MODEL}")
print(f"Date: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
print(f"Roles: {len(ROLES)}")
print(f"Modes: think (4096 tokens), no_think (4096 tokens)")
print()

all_results = []

for role, prompt in ROLES.items():
    print(f"\n{'='*60}")
    print(f"Role: {role}")
    print(f"{'='*60}")
    
    role_results = {"role": role, "tests": []}
    
    # Test with thinking mode
    print(f"  Running THINK mode (4096 tokens)...", flush=True)
    think_result = run_test(role, prompt, mode="think", max_tokens=4096)
    if "error" not in think_result:
        role_results["think"] = think_result
        print(f"    Result: {think_result['gen_tok_s']} tok/s, thinking={think_result['thinking_chars']} chars, response={think_result['response_chars']} chars")
    else:
        print(f"    ERROR: {think_result['error'][:100]}")
    
    # Test with no_think mode
    print(f"  Running NO_THINK mode (4096 tokens)...", flush=True)
    nothink_result = run_test(role, prompt, mode="no_think", max_tokens=4096)
    if "error" not in nothink_result:
        role_results["no_think"] = nothink_result
        print(f"    Result: {nothink_result['gen_tok_s']} tok/s, thinking={nothink_result['thinking_chars']} chars, response={nothink_result['response_chars']} chars")
    else:
        print(f"    ERROR: {nothink_result['error'][:100]}")
    
    all_results.append(role_results)
    
    # Save individual role results
    with open(f"{OUT}/{role}_think.json", "w") as f:
        json.dump(think_result, f, indent=2)
    with open(f"{OUT}/{role}_nothink.json", "w") as f:
        json.dump(nothink_result, f, indent=2)
    with open(f"{OUT}/{role}_think_response.txt", "w") as f:
        if "error" not in think_result:
            if think_result["thinking_content"]:
                f.write("=== THINKING ===\n")
                f.write(think_result["thinking_content"] + "\n\n")
            f.write("=== RESPONSE ===\n")
            f.write(think_result["response_preview"])
    with open(f"{OUT}/{role}_nothink_response.txt", "w") as f:
        if "error" not in nothink_result:
            if nothink_result["thinking_content"]:
                f.write("=== THINKING ===\n")
                f.write(nothink_result["thinking_content"] + "\n\n")
            f.write("=== RESPONSE ===\n")
            f.write(nothink_result["response_preview"])

# Summary
print(f"\n{'='*60}")
print("SUMMARY")
print(f"{'='*60}")

print(f"\n{'Role':<25} {'Mode':<10} {'Gen tok/s':>10} {'Thinking':>10} {'Response':>10} {'Wall s':>8}")
print("-" * 75)

for result in all_results:
    role = result["role"]
    
    # Think mode
    if "think" in result:
        t = result["think"]
        wall_s = round(t["wall_time_ms"] / 1000, 1)
        thinking = t["thinking_chars"]
        response = t["response_chars"]
        status = "✅" if (thinking > 0 or response > 0) else "⚠️"
        print(f"{role:<25} {'think':<10} {t['gen_tok_s']:>10.2f} {thinking:>10} {response:>10} {wall_s:>8} {status}")
    
    # No_think mode
    if "no_think" in result:
        t = result["no_think"]
        wall_s = round(t["wall_time_ms"] / 1000, 1)
        thinking = t["thinking_chars"]
        response = t["response_chars"]
        status = "✅" if (thinking > 0 or response > 0) else "⚠️"
        print(f"{'':<25} {'no_think':<10} {t['gen_tok_s']:>10.2f} {thinking:>10} {response:>10} {wall_s:>8} {status}")

# Save all results
with open(f"{OUT}/all_role_results.json", "w") as f:
    json.dump({
        "model": MODEL,
        "date": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        "results": all_results
    }, f, indent=2)

print(f"\nResults saved to {OUT}/")