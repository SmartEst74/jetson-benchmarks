#!/usr/bin/env python3
"""Run role-based benchmarks against the Jetson LLM API."""
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

print(f"=== Jetson Role Benchmark ===")
print(f"Model: {MODEL}")
print(f"Date: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
print(f"Roles: {len(ROLES)}")
print()

results = []
for role, prompt in ROLES.items():
    print(f"--- {role} ---", flush=True)
    payload = json.dumps({
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant acting as a specialized agent."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.6,
        "max_tokens": 1024,
        "stream": False
    }).encode()
    
    req = urllib.request.Request(API, data=payload, headers={"Content-Type": "application/json"})
    
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            raw = json.loads(resp.read())
    except Exception as e:
        print(f"  ERROR: {e}")
        continue
    wall_ms = int((time.time() - t0) * 1000)
    
    timings = raw.get("timings", {})
    usage = raw.get("usage", {})
    choice = raw.get("choices", [{}])[0]
    msg = choice.get("message", {})
    
    r = {
        "role": role,
        "model": MODEL,
        "gen_tok_s": round(timings.get("predicted_per_second", 0), 2),
        "prompt_tok_s": round(timings.get("prompt_per_second", 0), 2),
        "gen_tokens": timings.get("predicted_n", usage.get("completion_tokens", 0)),
        "prompt_tokens": timings.get("prompt_n", usage.get("prompt_tokens", 0)),
        "wall_time_ms": wall_ms,
        "finish_reason": choice.get("finish_reason", "unknown"),
        "thinking_used": bool(msg.get("reasoning_content")),
        "response_chars": len(msg.get("content", "")),
    }
    results.append(r)
    print(json.dumps(r, indent=2))
    
    with open(f"{OUT}/{role}.json", "w") as f:
        json.dump(r, f, indent=2)
    with open(f"{OUT}/{role}_response.txt", "w") as f:
        if msg.get("reasoning_content"):
            f.write("=== THINKING ===\n")
            f.write(str(msg["reasoning_content"]) + "\n\n")
        f.write("=== RESPONSE ===\n")
        f.write(str(msg.get("content", "")))
    print()

print("\n=== SUMMARY ===")
if results:
    hdr = f"{'Role':<25} {'Gen tok/s':>10} {'Prompt tok/s':>12} {'Tokens':>8} {'Wall ms':>10} {'Thinking':>10}"
    print(hdr)
    print("-" * len(hdr))
    for r in results:
        print(f"{r['role']:<25} {r['gen_tok_s']:>10.2f} {r['prompt_tok_s']:>12.2f} {r['gen_tokens']:>8} {r['wall_time_ms']:>10} {str(r['thinking_used']):>10}")
    avg_gen = sum(r["gen_tok_s"] for r in results) / len(results)
    avg_prompt = sum(r["prompt_tok_s"] for r in results) / len(results)
    total_tokens = sum(r["gen_tokens"] for r in results)
    print("-" * len(hdr))
    print(f"{'AVERAGE':<25} {avg_gen:>10.2f} {avg_prompt:>12.2f} {total_tokens:>8}")

# Save all results
with open(f"{OUT}/all_results.json", "w") as f:
    json.dump({"model": MODEL, "date": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), "results": results}, f, indent=2)
print(f"\nResults saved to {OUT}/")
