#!/usr/bin/env python3
"""Jetson Role Benchmark v2 — Dual-mode (thinking + no_think), higher token limit."""

import json, time, urllib.request, urllib.error, os, sys
from datetime import datetime, timezone

API = "http://localhost:8000/v1/chat/completions"
OUTDIR = "/tmp/bench-results-v2"
os.makedirs(OUTDIR, exist_ok=True)

# --- Role prompts (one coding task per role) ---
ROLE_PROMPTS = {
    "frontend_developer": "Build a React TypeScript component: a virtualized data table with 10,000+ rows, column sorting, search filtering, keyboard navigation. Use @tanstack/react-virtual. Include ARIA attributes and responsive design with Tailwind CSS.",
    "backend_architect": "Design a Node.js microservice for a rate-limited payment processing queue. Include: Bull/BullMQ job queue, Redis connection pooling, circuit breaker pattern, structured logging, health check endpoint, graceful shutdown. Provide complete TypeScript implementation.",
    "code_reviewer": "Review this code and identify all issues:\n```python\nimport pickle, os, subprocess\ndef process(data):\n    obj = pickle.loads(data)\n    cmd = f'echo {obj[\"name\"]}'\n    result = subprocess.call(cmd, shell=True)\n    with open('/tmp/' + obj['file'], 'w') as f:\n        f.write(str(result))\n    return eval(obj.get('expr', '1+1'))\n```\nList every security vulnerability, bug, and code smell. Provide severity ratings and fixed code.",
    "security_engineer": "Write a comprehensive OWASP Top 10 security audit checklist for a REST API built with Express.js and PostgreSQL. For each vulnerability class, provide: specific test cases, example attack payloads, detection methods, and remediation code snippets.",
    "technical_writer": "Write API documentation for a WebSocket-based real-time collaboration service. Include: connection lifecycle, authentication flow, message formats (JSON schemas), error codes, reconnection strategy, rate limits, and code examples in JavaScript and Python.",
    "ai_engineer": "Implement a Python RAG (Retrieval-Augmented Generation) pipeline using LangChain. Include: document loading from PDF, recursive text splitting, FAISS vector store with OpenAI embeddings, retrieval chain with source citations, streaming output. Provide complete working code with type hints.",
    "performance_benchmarker": "Write a comprehensive k6 load testing script for an e-commerce API. Test scenarios: browse products (GET), add to cart (POST), checkout flow (POST sequence), search with filters. Include: ramp-up/down stages, custom metrics, thresholds, tag-based filtering, and HTML report generation.",
    "api_tester": "Write a complete Pytest test suite for a REST API user management system. Cover: CRUD operations, authentication (JWT), authorization (roles), input validation, pagination, error responses, rate limiting. Use fixtures, parametrize, and async client. Include both happy path and edge cases."
}

def call_api(prompt, max_tokens=2048, no_think=False):
    """Send a chat completion request. If no_think, prefix with /no_think."""
    user_msg = f"/no_think\n\n{prompt}" if no_think else prompt
    body = json.dumps({
        "model": "Qwen3.5-4B-Q8_0.gguf",
        "messages": [{"role": "user", "content": user_msg}],
        "max_tokens": max_tokens,
        "temperature": 0.6,
        "stream": False
    }).encode()

    req = urllib.request.Request(API, data=body, headers={"Content-Type": "application/json"})
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=600) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        return {"error": str(e), "wall_time_ms": int((time.monotonic()-t0)*1000)}
    wall = int((time.monotonic()-t0)*1000)

    choice = data["choices"][0]
    usage = data.get("usage", {})
    content = choice["message"]["content"] or ""

    # Split thinking vs response
    think_text = ""
    resp_text = content
    if "<think>" in content:
        parts = content.split("</think>", 1)
        if len(parts) == 2:
            think_text = parts[0].replace("<think>", "").strip()
            resp_text = parts[1].strip()
        else:
            think_text = content.replace("<think>", "").strip()
            resp_text = ""

    gen_toks = usage.get("completion_tokens", 0)
    prompt_toks = usage.get("prompt_tokens", 0)

    return {
        "gen_tok_s": round(gen_toks / (wall/1000), 2) if wall > 0 else 0,
        "prompt_tok_s": round(prompt_toks / (data.get("usage",{}).get("prompt_eval_duration_ms", wall)/1000), 2) if prompt_toks else 0,
        "gen_tokens": gen_toks,
        "prompt_tokens": prompt_toks,
        "wall_time_ms": wall,
        "finish_reason": choice.get("finish_reason", "unknown"),
        "thinking_used": bool(think_text),
        "think_tokens_approx": len(think_text.split()) if think_text else 0,
        "response_chars": len(resp_text),
        "response_words": len(resp_text.split()) if resp_text else 0,
        "think_text": think_text,
        "response_text": resp_text
    }

def detect_model():
    """Get the model name from the API."""
    try:
        req = urllib.request.Request("http://localhost:8000/v1/models")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return data["data"][0]["id"]
    except:
        return "unknown"

def run_benchmark():
    model = detect_model()
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"=== Jetson Role Benchmark v2 ===")
    print(f"Model: {model}")
    print(f"Date: {timestamp}")
    print(f"Modes: thinking (2048 tok) + no_think (2048 tok)")
    print(f"Roles: {len(ROLE_PROMPTS)}\n")

    all_results = []

    for role, prompt in ROLE_PROMPTS.items():
        for mode in ["thinking", "no_think"]:
            no_think = (mode == "no_think")
            label = f"{role}/{mode}"
            print(f"--- {label} ---")
            sys.stdout.flush()

            result = call_api(prompt, max_tokens=2048, no_think=no_think)

            # Save response text separately
            think_text = result.pop("think_text", "")
            resp_text = result.pop("response_text", "")

            result["role"] = role
            result["mode"] = mode
            result["model"] = model

            fname = f"{role}_{mode}"
            with open(f"{OUTDIR}/{fname}_response.txt", "w") as f:
                if think_text:
                    f.write("=== THINKING ===\n")
                    f.write(think_text + "\n\n")
                f.write("=== RESPONSE ===\n")
                f.write(resp_text + "\n")

            with open(f"{OUTDIR}/{fname}_metrics.json", "w") as f:
                json.dump(result, f, indent=2)

            all_results.append(result)
            print(json.dumps(result, indent=2))
            print()
            sys.stdout.flush()

    # Summary table
    print("\n=== SUMMARY ===")
    print(f"{'Role':<28} {'Mode':<10} {'Gen t/s':>8} {'Prompt t/s':>11} {'Tokens':>7} {'Wall ms':>9} {'RespChars':>10} {'Think':>6}")
    print("-" * 100)
    for r in all_results:
        print(f"{r['role']:<28} {r['mode']:<10} {r['gen_tok_s']:>8.2f} {r['prompt_tok_s']:>11.2f} {r['gen_tokens']:>7} {r['wall_time_ms']:>9} {r['response_chars']:>10} {str(r['thinking_used']):>6}")
    print("-" * 100)

    think_results = [r for r in all_results if r["mode"] == "thinking"]
    nothink_results = [r for r in all_results if r["mode"] == "no_think"]

    for label, subset in [("thinking", think_results), ("no_think", nothink_results)]:
        avg_gen = sum(r["gen_tok_s"] for r in subset) / len(subset) if subset else 0
        avg_prompt = sum(r["prompt_tok_s"] for r in subset) / len(subset) if subset else 0
        total_toks = sum(r["gen_tokens"] for r in subset)
        avg_chars = sum(r["response_chars"] for r in subset) / len(subset) if subset else 0
        print(f"AVG {label:<24} {'':10} {avg_gen:>8.2f} {avg_prompt:>11.2f} {total_toks:>7} {'':>9} {avg_chars:>10.0f}")

    # Save all
    with open(f"{OUTDIR}/all_results.json", "w") as f:
        json.dump({"model": model, "date": timestamp, "results": all_results}, f, indent=2)

    print(f"\nResults saved to {OUTDIR}/")

if __name__ == "__main__":
    run_benchmark()
