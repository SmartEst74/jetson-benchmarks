#!/usr/bin/env bash
set -euo pipefail

API="http://localhost:8000/v1/chat/completions"
MODEL="Qwen3.5-4B-Q8_0.gguf"
OUTDIR="/tmp/bench-results"
mkdir -p "$OUTDIR"

bench_role() {
    local role="$1"
    local prompt="$2"
    
    echo "--- Benchmarking: $role ---"
    
    local start_ns=$(date +%s%N)
    
    local payload
    payload=$(python3 -c "
import json
d = {
    'model': '$MODEL',
    'messages': [
        {'role': 'system', 'content': 'You are a helpful assistant acting as a specialized agent.'},
        {'role': 'user', 'content': $(python3 -c "import json; print(json.dumps('''$prompt'''))")}
    ],
    'temperature': 0.6,
    'max_tokens': 1024,
    'stream': False
}
print(json.dumps(d))
")
    
    local raw
    raw=$(curl -s --max-time 300 \
        -X POST "$API" \
        -H "Content-Type: application/json" \
        -d "$payload" 2>/dev/null) || { echo "  CURL FAILED for $role"; return; }
    
    local end_ns=$(date +%s%N)
    local wall_ms=$(( (end_ns - start_ns) / 1000000 ))
    
    python3 << PYEOF
import json

raw = json.loads('''$(echo "$raw" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read()))")''')

timings = raw.get('timings', {})
usage = raw.get('usage', {})
choice = raw.get('choices', [{}])[0]
msg = choice.get('message', {})

out = {
    'role': '$role',
    'model': '$MODEL',
    'gen_tok_s': round(timings.get('predicted_per_second', 0), 2),
    'prompt_tok_s': round(timings.get('prompt_per_second', 0), 2),
    'gen_tokens': timings.get('predicted_n', usage.get('completion_tokens', 0)),
    'prompt_tokens': timings.get('prompt_n', usage.get('prompt_tokens', 0)),
    'wall_time_ms': $wall_ms,
    'finish_reason': choice.get('finish_reason', 'unknown'),
    'thinking_used': bool(msg.get('reasoning_content')),
    'response_chars': len(msg.get('content', ''))
}
print(json.dumps(out, indent=2))

with open('$OUTDIR/${role}.json', 'w') as f:
    json.dump(out, f, indent=2)

with open('$OUTDIR/${role}_response.txt', 'w') as f:
    if msg.get('reasoning_content'):
        f.write('=== THINKING ===\\n')
        f.write(str(msg.get('reasoning_content', '')) + '\\n\\n')
    f.write('=== RESPONSE ===\\n')  
    f.write(str(msg.get('content', '')))
PYEOF
    echo ""
}

echo "=== Jetson Role Benchmark ==="
echo "Model: $MODEL"
echo "Date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

bench_role "frontend_developer" "Build a React TypeScript component for a virtualized data table with 10,000+ rows. Requirements: sortable columns (click header to toggle asc/desc), filterable with search input, proper ARIA labels, keyboard navigation between rows, responsive (stacks on mobile). Use @tanstack/react-virtual. Include full component code with types."

bench_role "backend_architect" "Design a PostgreSQL schema for a multi-tenant SaaS project management tool. Requirements: tenant isolation via row-level security, projects with tasks (nested subtasks), team members with roles (admin/manager/member), activity audit log. Include CREATE TABLE statements with proper types, indexes for common queries, and RLS policies."

bench_role "code_reviewer" "Review this Python endpoint for ALL issues. Use priority markers (blocker/suggestion/nit): @app.route('/api/query', methods=['POST']) def query(): data = request.json; sql = f\"SELECT * FROM users WHERE name = '{data[name]}'\"; result = db.execute(sql); token = jwt.encode({'user': data['name']}, 'secret123', algorithm='HS256'); response = make_response(jsonify({'data': result.fetchall(), 'token': token})); response.headers['Access-Control-Allow-Origin'] = '*'; return response"

bench_role "security_engineer" "Perform a STRIDE threat model for this architecture: A Jetson edge device runs an LLM inference API (HTTP, port 8000) on a local network. Users SSH in to manage models. A hot-swap API (port 8001) switches models. Models stored on NVMe. No firewall configured. IoT devices on same subnet. For each STRIDE category, identify at least 2 threats with severity and mitigations."

bench_role "technical_writer" "Write a README.md for a tool called jetson-bench. Include: project title, one-line description, badge placeholders, prerequisites (JetPack 6.2+, Docker, 8GB+ RAM), install section, usage with 3 example commands and output, configuration table (6+ options), troubleshooting with 3 issues, contributing link, MIT license. Under 180 lines."

bench_role "ai_engineer" "Design an inference optimization pipeline for a 4B parameter LLM on Jetson Orin Nano Super (8GB unified RAM, 1024 CUDA cores SM 8.7, 68 GB/s bandwidth). Cover: quantization strategy (GPTQ vs AWQ vs GGUF), KV cache management for 8K context, batching strategy, thermal management, memory budget breakdown with specific numbers."

bench_role "performance_benchmarker" "Analyze LLM inference data: Jetson Orin Nano 8GB, Qwen3.5-4B Q8_0 (4.48GB), llama.cpp. 5 runs: Gen 10.2-10.6 tok/s, Prompt 245-261 tok/s, RAM 6.1 GiB, Temp 58-65C. Theoretical limit 15.2 tok/s, actual efficiency 68.4%. Explain the efficiency gap, bottleneck, thermal trend, and optimization recommendations."

bench_role "api_tester" "Generate a pytest test suite for an OpenAI-compatible LLM API at localhost:8000/v1. Endpoints: POST /v1/chat/completions, GET /v1/models. Cover: happy path, input validation (missing messages, invalid model, empty array), error handling, performance (response under 30s), security (proper headers). Use pytest with clear names."

echo ""
echo "=== Summary ==="
python3 << 'SUMEOF'
import json, os, glob
results = []
for f in sorted(glob.glob('/tmp/bench-results/*.json')):
    if '_response' not in f:
        with open(f) as fh:
            results.append(json.load(fh))

if not results:
    print("No results found")
    exit(0)

fmt = "{:<25} {:>10} {:>12} {:>8} {:>10} {:>10}"
print(fmt.format('Role', 'Gen tok/s', 'Prompt tok/s', 'Tokens', 'Wall ms', 'Thinking'))
print('-' * 80)
for r in results:
    print(fmt.format(r['role'], f"{r['gen_tok_s']:.2f}", f"{r['prompt_tok_s']:.2f}", 
          str(r['gen_tokens']), str(r['wall_time_ms']), str(r['thinking_used'])))

avg_gen = sum(r['gen_tok_s'] for r in results) / len(results)
avg_prompt = sum(r['prompt_tok_s'] for r in results) / len(results)
total_tokens = sum(r['gen_tokens'] for r in results)
print('-' * 80)
print(fmt.format('AVERAGE', f"{avg_gen:.2f}", f"{avg_prompt:.2f}", str(total_tokens), '', ''))
SUMEOF
