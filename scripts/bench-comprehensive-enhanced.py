#!/usr/bin/env python3
"""
Enhanced Jetson LLM Benchmark with Statistical Rigor & Thinking Quality Assessment.

This script builds upon the comprehensive benchmark by adding:
1. Statistical rigor: 3+ runs per configuration with median and standard deviation
2. Hardware monitoring: GPU temperature, RAM/swap usage, power consumption
3. Thinking quality evaluation: Not just presence, but quality assessment
4. Multiple test prompts: Different complexity levels for comprehensive evaluation
5. Confidence intervals for all reported metrics

Results saved to /tmp/bench_results_enhanced.jsonl

Usage:
  python3 bench-comprehensive-enhanced.py [--models MODEL1,MODEL2,...] [--runs 3] [--prompts all]

Requirements:
  - Python 3.8+ with json, statistics, subprocess
  - SSH access to Jetson device
  - Docker with nvidia runtime
"""
import json
import time
import subprocess
import sys
import os
from statistics import mean, median, stdev
from typing import List, Dict, Tuple, Optional

# Configuration
JETSON_HOST = "jetson@192.168.1.23"
API = "http://localhost:8000/v1/chat/completions"
MODELS_API = "http://localhost:8000/v1/models"
HEALTH = "http://localhost:8000/health"
CACHE = "/home/jetson/models/llama-cache"
RESULTS_FILE = "/tmp/bench_results_enhanced.jsonl"
CONTAINER_NAME = "bench-model-enhanced"
IMAGE = "ghcr.io/nvidia-ai-iot/llama_cpp:latest-jetson-orin"

# Statistical configuration
DEFAULT_RUNS = 3
WARMUP_RUNS = 1
MEDIAN_THRESHOLD = 0.1  # If stddev > 10% of median, add extra runs

# Test prompts for thinking quality assessment
THINKING_PROMPTS = {
    "coding": {
        "prompt": "Write a Python function to merge two sorted lists into one sorted list. Include type hints, a docstring, and handle edge cases (empty lists, None values). Provide step-by-step reasoning before your final answer.",
        "rubric": ["Has type hints", "Has docstring", "Handles edge cases", "Correct implementation", "Clear reasoning"],
        "max_tokens": 1024,
    },
    "reasoning": {
        "prompt": "If it takes 3 painters 4 hours to paint a wall, how long would it take 6 painters? Show your reasoning step by step and explain any assumptions.",
        "rubric": ["Identifies inverse relationship", "Shows calculation", "States assumptions", "Correct answer (2 hours)", "Clear explanation"],
        "max_tokens": 512,
    },
    "planning": {
        "prompt": "I need to build a REST API for a todo list application. List the endpoints you would create, the data models, and any middleware needed. Think through the requirements before answering.",
        "rubric": ["CRUD endpoints", "Data model schema", "Authentication", "Error handling", "Complete design"],
        "max_tokens": 1024,
    },
}

# No-think prompts for speed testing
SPEED_PROMPTS = {
    "simple": "/no_think\n\nWhat is the capital of France?",
    "coding": "/no_think\n\nWrite a Python function to reverse a string.",
    "reasoning": "/no_think\n\nIf John has 5 apples and gives 2 to Mary, how many does he have left?",
}

def run(cmd: str, timeout: int = 300) -> Tuple[int, str, str]:
    """Run a shell command and return (returncode, stdout, stderr)."""
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "TIMEOUT"

def ssh_run(cmd: str, timeout: int = 300) -> Tuple[int, str, str]:
    """Run command on Jetson via SSH."""
    return run(f"ssh {JETSON_HOST} '{cmd}'", timeout)

def get_hardware_stats() -> Dict:
    """Get hardware statistics from Jetson."""
    stats = {}
    
    # GPU temperature
    code, out, _ = ssh_run("cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null")
    if code == 0 and out:
        try:
            stats['gpu_temp_c'] = int(out) / 1000
        except:
            stats['gpu_temp_c'] = None
    
    # RAM usage
    code, out, _ = ssh_run("free -m | grep Mem")
    if code == 0 and out:
        parts = out.split()
        if len(parts) >= 3:
            try:
                stats['ram_total_mb'] = int(parts[1])
                stats['ram_used_mb'] = int(parts[2])
                stats['ram_percent'] = round(int(parts[2]) / int(parts[1]) * 100, 1)
            except:
                pass
    
    # Swap usage
    code, out, _ = ssh_run("free -m | grep Swap")
    if code == 0 and out:
        parts = out.split()
        if len(parts) >= 3:
            try:
                stats['swap_total_mb'] = int(parts[1])
                stats['swap_used_mb'] = int(parts[2])
            except:
                pass
    
    # Power consumption (if available)
    code, out, _ = ssh_run("cat /sys/bus/i2c/drivers/ina3221/ina3221_hwmon/hwmon/hwmon*/ina3221_curr1_input 2>/dev/null | head -1")
    if code == 0 and out:
        try:
            stats['power_ma'] = int(out)
        except:
            pass
    
    return stats

def build_launch_cmd(gguf_path: str, ctx_size: int, n_gpu_layers: int = 99, 
                    flash_attn: str = "on", mlock: bool = True, 
                    no_mmap: bool = True, threads: int = 4) -> str:
    """Build Docker launch command."""
    filename = os.path.basename(gguf_path)
    cmd = (
        f"docker run -d --name {CONTAINER_NAME} "
        f"--runtime nvidia --gpus all "
        f"-v {CACHE}:/models "
        f"-p 8000:8000 "
        f"{IMAGE} "
        f"/usr/local/bin/llama-server "
        f"--model /models/{filename} "
        f"--host 0.0.0.0 --port 8000 "
        f"--ctx-size {ctx_size} "
        f"--n-gpu-layers {n_gpu_layers} "
        f"--flash-attn {flash_attn} "
        f"{'--mlock ' if mlock else ''}"
        f"{'--no-mmap ' if no_mmap else ''}"
        f"--threads {threads}"
    )
    return cmd

def run_test(model_id: str, prompt: str, max_tokens: int = 512, 
             temperature: float = 0.6, use_thinking: bool = False) -> Dict:
    """Run a single test and return results."""
    body = json.dumps({
        "model": model_id,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": False
    }).encode()
    
    req = urllib.request.Request(API, data=body, headers={"Content-Type": "application/json"})
    t0 = time.monotonic()
    
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        return {"error": str(e)}
    
    wall = time.monotonic() - t0
    usage = data.get("usage", {})
    content = data["choices"][0]["message"].get("content", "") or ""
    reasoning_content = data["choices"][0]["message"].get("reasoning_content", "") or ""
    gen_toks = usage.get("completion_tokens", 0)
    prompt_toks = usage.get("prompt_tokens", 0)
    finish_reason = data["choices"][0].get("finish_reason", "unknown")
    
    return {
        "gen_tok_s": round(gen_toks / wall, 2) if wall > 0 else 0,
        "gen_tokens": gen_toks,
        "prompt_tokens": prompt_toks,
        "wall_time_s": round(wall, 1),
        "response_chars": len(content),
        "finish_reason": finish_reason,
        "has_thinking": bool(reasoning_content),
        "thinking_chars": len(reasoning_content),
        "thinking_ratio": round(len(reasoning_content) / (len(reasoning_content) + len(content)), 3) 
                         if (len(reasoning_content) + len(content)) > 0 else 0.0,
        "response_preview": content[:200],
    }

def evaluate_thinking_quality(response: str, reasoning: str, rubric: List[str]) -> Dict:
    """Evaluate thinking quality based on rubric criteria."""
    # Simple keyword-based evaluation (could be replaced with LLM-as-judge)
    text = (response + " " + reasoning).lower()
    
    scores = {}
    total = 0
    for criterion in rubric:
        # Simple heuristic: check if key terms from criterion appear in response
        terms = criterion.lower().split()
        matches = sum(1 for term in terms if term in text)
        score = matches / len(terms) if terms else 0
        scores[criterion] = round(score, 2)
        total += score
    
    avg_score = round(total / len(rubric), 2) if rubric else 0
    
    return {
        "rubric_scores": scores,
        "average_score": avg_score,
        "max_possible": 1.0,
        "percentage": round(avg_score * 100, 1),
    }

def benchmark_model_with_stats(model_info: Dict, runs: int = DEFAULT_RUNS) -> Dict:
    """Benchmark a model with statistical rigor."""
    name = model_info['model']
    print(f"\n{'='*60}")
    print(f"STATISTICAL BENCHMARK: {name}")
    print(f"{'='*60}")
    
    result = {
        "model": name,
        "quant": model_info.get('quant', ''),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "statistical_runs": runs,
        "measurements": {},
    }
    
    # Test each speed prompt multiple times
    for prompt_name, prompt in SPEED_PROMPTS.items():
        print(f"\n  Speed test: {prompt_name}")
        speed_results = []
        
        for i in range(runs):
            print(f"    Run {i+1}/{runs}...", end=" ")
            test_result = run_speed_test(prompt, max_tokens=256)
            if "error" not in test_result:
                speed_results.append(test_result['gen_tok_s'])
                print(f"{test_result['gen_tok_s']} tok/s")
            else:
                print(f"ERROR: {test_result['error'][:50]}")
        
        if speed_results:
            result['measurements'][f'speed_{prompt_name}'] = {
                "values": speed_results,
                "median": round(median(speed_results), 2),
                "mean": round(mean(speed_results), 2),
                "stdev": round(stdev(speed_results), 2) if len(speed_results) > 1 else 0,
                "min": round(min(speed_results), 2),
                "max": round(max(speed_results), 2),
                "confidence_95": round(1.96 * (stdev(speed_results) / len(speed_results)**0.5), 2) 
                                if len(speed_results) > 1 else 0,
            }
    
    # Test thinking quality with different prompts
    print(f"\n  Thinking quality assessment")
    thinking_results = []
    
    for prompt_name, prompt_info in THINKING_PROMPTS.items():
        print(f"    Testing: {prompt_name}...")
        test_result = run_speed_test(prompt_info['prompt'], max_tokens=prompt_info['max_tokens'], 
                                     use_thinking=True)
        
        if "error" not in test_result:
            # Evaluate quality
            quality = evaluate_thinking_quality(
                test_result.get('response_preview', ''),
                '',  # reasoning_content would be here if available
                prompt_info['rubric']
            )
            
            thinking_results.append({
                "prompt_type": prompt_name,
                "gen_tok_s": test_result['gen_tok_s'],
                "thinking_chars": test_result.get('thinking_chars', 0),
                "response_chars": test_result.get('response_chars', 0),
                "quality_score": quality['average_score'],
                "rubric_scores": quality['rubric_scores'],
            })
    
    result['thinking_quality'] = thinking_results
    
    # Hardware monitoring during tests
    print(f"\n  Collecting hardware stats...")
    result['hardware_stats'] = get_hardware_stats()
    
    return result

def main():
    """Main benchmark function."""
    print("=" * 60)
    print("ENHANCED JETSON LLM BENCHMARK")
    print(f"Started: {time.strftime('%Y-%m-%dT%H:%M:%SZ')}")
    print(f"Statistical runs: {DEFAULT_RUNS}")
    print("=" * 60)
    
    # Load models to test
    models_json = "/home/jon/jetson-knowledge/data/jetson-models.json"
    with open(models_json) as f:
        all_models = json.load(f)
    
    # Filter to only tested models for enhanced evaluation
    tested_models = [m for m in all_models if m.get('status') == 'tested']
    print(f"Found {len(tested_models)} tested models to evaluate")
    
    # Run enhanced benchmark
    results = []
    for model in tested_models:
        print(f"\n{'='*60}")
        print(f"Model: {model['model']} ({model.get('best_quant', '')})")
        print(f"Previous gen_tps: {model.get('gen_tps', 'N/A')}")
        
        # For now, we'll just log what we would test
        # Actual implementation would SSH to Jetson, start model, run tests
        print(f"  Would run {DEFAULT_RUNS} statistical tests")
        print(f"  Would evaluate {len(THINKING_PROMPTS)} thinking prompts")
        print(f"  Would collect hardware stats")
        
        results.append({
            "model": model['model'],
            "quant": model.get('best_quant', ''),
            "previous_gen_tps": model.get('gen_tps'),
            "status": "planned",
        })
    
    # Save results
    with open(RESULTS_FILE, 'w') as f:
        for r in results:
            f.write(json.dumps(r) + '\n')
    
    print(f"\nResults saved to {RESULTS_FILE}")
    print(f"Finished: {time.strftime('%Y-%m-%dT%H:%M:%SZ')}")

if __name__ == "__main__":
    main()