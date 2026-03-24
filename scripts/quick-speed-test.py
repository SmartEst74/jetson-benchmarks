#!/usr/bin/env python3
"""Quick speed benchmark — single prompt, measures tok/s for current model."""

import json, time, urllib.request, sys

API = "http://localhost:8000/v1/chat/completions"
PROMPT = "Write a Python function that implements a binary search tree with insert, delete, and search operations. Include type hints and docstrings."

def detect_model():
    try:
        req = urllib.request.Request("http://localhost:8000/v1/models")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return data["data"][0]["id"]
    except:
        return "unknown"

def run_speed_test(max_tokens=512):
    model = detect_model()
    # Use /no_think for direct output
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": f"/no_think\n\n{PROMPT}"}],
        "max_tokens": max_tokens,
        "temperature": 0.6,
        "stream": False
    }).encode()

    req = urllib.request.Request(API, data=body, headers={"Content-Type": "application/json"})
    t0 = time.monotonic()
    with urllib.request.urlopen(req, timeout=300) as resp:
        data = json.loads(resp.read())
    wall = time.monotonic() - t0

    usage = data.get("usage", {})
    gen_toks = usage.get("completion_tokens", 0)
    prompt_toks = usage.get("prompt_tokens", 0)
    content = data["choices"][0]["message"]["content"] or ""

    result = {
        "model": model,
        "gen_tok_s": round(gen_toks / wall, 2),
        "gen_tokens": gen_toks,
        "prompt_tokens": prompt_toks,
        "wall_time_s": round(wall, 1),
        "response_chars": len(content),
        "finish_reason": data["choices"][0].get("finish_reason", "unknown")
    }

    print(json.dumps(result, indent=2))
    return result

if __name__ == "__main__":
    tokens = int(sys.argv[1]) if len(sys.argv) > 1 else 512
    run_speed_test(tokens)
