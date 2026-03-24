#!/usr/bin/env python3
"""
Maximum Utilization Jetson LLM Benchmark
Tests multiple configurations to find the optimal settings for each model.
Targets ~95-100% GPU utilization while maintaining stability.
Captures ALL settings for reproducibility.
"""
import json
import time
import subprocess
import os
import sys
from pathlib import Path

# Configuration
JETSON_HOST = "jetson@192.168.1.23"
MODELS_CACHE = "/home/jetson/models/llama-cache"
RESULTS_FILE = "/tmp/bench_max_util.jsonl"
DOCKER_IMAGE = "ghcr.io/nvidia-ai-iot/llama_cpp:latest-jetson-orin"

# Models to benchmark with their HuggingFace repos
MODELS = [
    # Already tested - re-test with optimized settings
    ("Qwen3-1.7B", "unsloth/Qwen3-1.7B-GGUF", "Qwen3-1.7B-Q8_0.gguf", "Q8_0", 1.71, 1),
    ("xLAM-2-1b-fc-r", "Salesforce/xLAM-2-1b-fc-r-gguf", "xLAM-2-1B-fc-r-Q8_0.gguf", "Q8_0", 1.53, 1),
    ("Arch-Agent-1.5B", "katanemo/Arch-Agent-1.5B.gguf", "Arch-Agent-1.5B.gguf", "Q8_0", 2.88, 1),
    ("Granite-4.0-350m", "mrutkows/granite-4.0-350m-GGUF", "granite-4.0-350m-Q8_0.gguf", "Q8_0", 0.35, 1),
    ("Hammer2.1-3b", "Nekuromento/Hammer2.1-3b-Q8_0-GGUF", "hammer2.1-3b-q8_0.gguf", "Q8_0", 3.06, 1),
    ("xLAM-2-3b-fc-r", "Salesforce/xLAM-2-3b-fc-r-gguf", "xLAM-2-3B-fc-r-Q8_0.gguf", "Q8_0", 3.06, 1),
    ("Llama-3.2-3B-Instruct", "bartowski/Llama-3.2-3B-Instruct-GGUF", "Llama-3.2-3B-Instruct-Q8_0.gguf", "Q8_0", 3.19, 1),
    ("MiniCPM3-4B", "openbmb/MiniCPM3-4B-GGUF", "minicpm3-4b-q4_k_m.gguf", "Q4_K_M", 2.30, 1),
    
    # New models to test
    ("Arch-Agent-3B", "katanemo/Arch-Agent-3B", "Arch-Agent-3B.gguf", "Q8_0", 5.75, 2),
    ("Gemma-3-4b-it", "bartowski/gemma-3-4b-it-GGUF", "gemma-3-4b-it-Q4_K_M.gguf", "Q4_K_M", 2.68, 1),
    ("Qwen3-4B-Instruct-2507", "unsloth/Qwen3-4B-Instruct-2507-GGUF", "Qwen3-4B-Instruct-2507-Q8_0.gguf", "Q8_0", 4.2, 1),
    
    # 8B models
    ("xLAM-2-8b-fc-r", "Salesforce/Llama-xLAM-2-8b-fc-r-gguf", "Llama-xLAM-2-8B-fc-r-Q4_K_M.gguf", "Q4_K_M", 5.0, 2),
    ("Hammer2.1-7b", "bartowski/Hammer2.1-7b-GGUF", "Hammer2.1-7b-Q4_K_M.gguf", "Q4_K_M", 4.37, 1),
    ("BitAgent-Bounty-8B", "mradermacher/BitAgent-Bounty-8B-GGUF", "BitAgent-Bounty-8B.Q4_K_M.gguf", "Q4_K_M", 3.38, 2),
]

# Configurations to test - optimized for maximum GPU utilization
CONFIGS = [
    # ctx_size, n_gpu_l, threads, batch_size, cache_k, cache_v, flash_attn
    (4096, 999, 6, 512, "q8_0", "q8_0", "on"),
    (4096, 999, 4, 512, "q8_0", "q8_0", "on"),
    (4096, 999, 6, 1024, "q8_0", "q8_0", "on"),
    (2048, 999, 6, 512, "q8_0", "q8_0", "on"),
    (2048, 999, 4, 512, "q8_0", "q8_0", "on"),
    (2048, 999, 6, 1024, "q8_0", "q8_0", "on"),
    (1024, 999, 6, 256, "q8_0", "q8_0", "on"),
    (1024, 999, 4, 256, "q8_0", "q8_0", "on"),
    (8192, 999, 6, 512, "q8_0", "q8_0", "on"),  # Large context
]

# Test prompt
TEST_PROMPT = "/no_think\n\nWrite a Python function to merge two sorted lists into one sorted list. Include type hints, a docstring, and handle edge cases (empty lists, None values). Show your complete implementation."

def run_cmd(cmd, timeout=300):
    """Run command locally (or via SSH if specified)."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "TIMEOUT"

def get_gpu_stats():
    """Get GPU utilization stats."""
    code, out, _ = run_cmd("timeout 2 tegrastats 2>/dev/null | head -1")
    if code == 0 and out:
        # Parse tegrastats output
        stats = {}
        if "GR3D_FREQ" in out:
            try:
                gpu_freq = out.split("GR3D_FREQ")[1].split("%")[0].strip()
                stats["gpu_freq_pct"] = int(gpu_freq)
            except:
                pass
        if "gpu@" in out:
            try:
                gpu_temp = out.split("gpu@")[1].split("C")[0].strip()
                stats["gpu_temp_c"] = float(gpu_temp)
            except:
                pass
        if "RAM" in out:
            try:
                ram_part = out.split("RAM")[1].split("MB")[0].strip()
                used, total = ram_part.split("/")
                stats["ram_used_mb"] = int(used)
                stats["ram_total_mb"] = int(total)
            except:
                pass
        return stats
    return {}

def stop_container():
    """Stop and remove Docker container."""
    run_cmd("docker stop bench-model 2>/dev/null; docker rm bench-model 2>/dev/null", timeout=30)
    time.sleep(2)

def download_model(repo, filename):
    """Download model if not exists."""
    local_path = f"{MODELS_CACHE}/{filename}"
    code, out, _ = run_cmd(f"ls -la {local_path} 2>/dev/null")
    if code == 0 and "No such file" not in out:
        size_check = run_cmd(f"stat -c%s {local_path} 2>/dev/null || echo 0")
        if int(size_check[1]) > 1000000:
            print(f"  Model exists: {local_path}")
            return True
    
    print(f"  Downloading {filename}...")
    url = f"https://huggingface.co/{repo}/resolve/main/{filename}"
    code, out, err = run_cmd(f"curl -L --progress-bar -o '{local_path}' '{url}'", timeout=3600)
    if code != 0:
        print(f"  Download failed: {err[:200]}")
        return False
    
    size_check = run_cmd(f"stat -c%s {local_path} 2>/dev/null || echo 0")
    if int(size_check[1]) < 1000000:
        print(f"  File too small, deleting")
        run_cmd(f"rm {local_path}")
        return False
    
    print(f"  Downloaded successfully")
    return True

def start_model(filename, ctx_size, n_gpu_l, threads, batch_size, cache_k, cache_v, flash_attn):
    """Start model with specific configuration."""
    stop_container()
    run_cmd("sudo sync && echo 3 | sudo tee /proc/sys/vm/drop_caches", timeout=10)
    time.sleep(2)
    
    cmd = (
        f"docker run -d --name bench-model "
        f"--runtime nvidia --gpus all "
        f"--network host "
        f"-v {MODELS_CACHE}:/models "
        f"{DOCKER_IMAGE} "
        f"/usr/local/bin/llama-server "
        f"--model /models/{filename} "
        f"--host 0.0.0.0 --port 8000 "
        f"--ctx-size {ctx_size} "
        f"--n-gpu-layers {n_gpu_l} "
        f"--flash-attn {flash_attn} "
        f"--mlock --no-mmap "
        f"--threads {threads} "
        f"--batch-size {batch_size} "
        f"--cache-type-k {cache_k} "
        f"--cache-type-v {cache_v}"
    )
    
    code, out, err = run_cmd(cmd, timeout=120)
    if code != 0:
        return False, cmd, err
    return True, cmd, ""

def wait_for_ready(timeout=120):
    """Wait for model to be ready."""
    start = time.time()
    while time.time() - start < timeout:
        code, out, _ = run_cmd("curl -s http://localhost:8000/health 2>/dev/null")
        if code == 0 and out:
            return True
        time.sleep(3)
    return False

def run_speed_test(max_tokens=512):
    """Run speed test and capture GPU stats."""
    # Get stats before
    stats_before = get_gpu_stats()
    
    payload = json.dumps({
        "model": "test",
        "messages": [{"role": "user", "content": TEST_PROMPT}],
        "max_tokens": max_tokens,
        "temperature": 0.6,
        "stream": False
    })
    
    cmd = f"curl -s http://localhost:8000/v1/chat/completions -H 'Content-Type: application/json' -d '{payload}'"
    
    t0 = time.time()
    code, out, err = run_cmd(cmd, timeout=300)
    wall_time = time.time() - t0
    
    if code != 0:
        return {"error": err[:200]}
    
    try:
        data = json.loads(out)
    except:
        return {"error": "Failed to parse response"}
    
    # Get stats after
    stats_after = get_gpu_stats()
    
    usage = data.get("usage", {})
    gen_tokens = usage.get("completion_tokens", 0)
    prompt_tokens = usage.get("prompt_tokens", 0)
    
    # Calculate GPU utilization (average of before/after)
    gpu_before = stats_before.get("gpu_freq_pct", 0)
    gpu_after = stats_after.get("gpu_freq_pct", 0)
    gpu_util = (float(gpu_before) + float(gpu_after)) / 2
    
    gen_tps = round(gen_tokens / wall_time, 2) if wall_time > 0 else 0
    prompt_tps = round(prompt_tokens / wall_time * 1000, 2) if wall_time > 0 else 0
    
    return {
        "gen_tok_s": gen_tps,
        "prompt_tok_s": prompt_tps,
        "gen_tokens": gen_tokens,
        "prompt_tokens": prompt_tokens,
        "wall_time_s": round(wall_time, 1),
        "gpu_util_pct": round(gpu_util, 1),
        "gpu_temp_before": stats_before.get("gpu_temp_c"),
        "gpu_temp_after": stats_after.get("gpu_temp_c"),
        "ram_used_before": stats_before.get("ram_used_mb"),
        "ram_used_after": stats_after.get("ram_used_mb"),
    }

def benchmark_config(filename, ctx_size, n_gpu_l, threads, batch_size, cache_k, cache_v, flash_attn):
    """Benchmark a specific configuration."""
    print(f"    Config: ctx={ctx_size}, gpu={n_gpu_l}, threads={threads}, batch={batch_size}, cache={cache_k}/{cache_v}")
    
    success, launch_cmd, err = start_model(filename, ctx_size, n_gpu_l, threads, batch_size, cache_k, cache_v, flash_attn)
    if not success:
        print(f"      Failed to start: {err[:100]}")
        return None
    
    if not wait_for_ready(timeout=90):
        print(f"      Timeout waiting for model")
        stop_container()
        return None
    
    # Run test
    result = run_speed_test(max_tokens=512)
    if "error" in result:
        print(f"      Test error: {result['error'][:100]}")
        stop_container()
        return None
    
    print(f"      Result: {result['gen_tok_s']} tok/s, GPU: {result['gpu_util_pct']}%, Temp: {result.get('gpu_temp_after', '?')}°C")
    
    result["config"] = {
        "ctx_size": str(ctx_size),
        "n_gpu_layers": str(n_gpu_l),
        "threads": str(threads),
        "batch_size": str(batch_size),
        "cache_type_k": str(cache_k),
        "cache_type_v": str(cache_v),
        "flash_attn": str(flash_attn),
        "launch_cmd": str(launch_cmd),
    }
    
    stop_container()
    return result

def benchmark_model(name, repo, filename, quant, expected_size, tier):
    """Benchmark a model with multiple configurations."""
    print(f"\n{'='*60}")
    print(f"BENCHMARKING: {name} ({quant})")
    print(f"  Expected size: {expected_size} GB")
    print(f"{'='*60}")
    
    result = {
        "model": name,
        "quant": quant,
        "repo": repo,
        "filename": filename,
        "tier": tier,
        "expected_size_gb": expected_size,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": "unknown",
        "best_config": None,
        "all_configs": [],
    }
    
    # Download model
    if not download_model(repo, filename):
        result["status"] = "download_failed"
        return result
    
    # Determine which configs to try based on model size
    if expected_size <= 4.5:
        configs_to_try = CONFIGS[:6]  # Smaller models: try more configs
    elif expected_size <= 6.0:
        configs_to_try = CONFIGS[:4]  # Medium models: fewer configs
    else:
        configs_to_try = CONFIGS[:3]  # Large models: minimal configs
    
    best_tps = 0.0
    best_config = None
    
    for i, (ctx, n_gpu, threads, batch, ck, cv, fa) in enumerate(configs_to_try):
        print(f"\n  Config {i+1}/{len(configs_to_try)}")
        result_config = benchmark_config(filename, ctx, n_gpu, threads, batch, ck, cv, fa)
        
        if result_config:
            result["all_configs"].append(result_config)
            current_tps = float(result_config.get("gen_tok_s", 0))
            if current_tps > best_tps:
                best_tps = current_tps
                best_config = result_config
    
    if best_config:
        result["status"] = "success"
        result["best_config"] = best_config
        result["gen_tps"] = best_tps
        result["gpu_util_best"] = best_config.get("gpu_util_pct", 0)
    else:
        result["status"] = "all_configs_failed"
    
    return result

def main():
    print("=" * 60)
    print("MAXIMUM UTILIZATION JETSON LLM BENCHMARK")
    print(f"Started: {time.strftime('%Y-%m-%dT%H:%M:%SZ')}")
    print(f"Target: ~95-100% GPU utilization")
    print(f"Models to test: {len(MODELS)}")
    print("=" * 60)
    
    # Stop production service
    print("\nStopping production service...")
    run_cmd("sudo systemctl stop qwen35-llm.service", timeout=30)
    stop_container()
    
    results = []
    for i, (name, repo, filename, quant, size, tier) in enumerate(MODELS):
        print(f"\n[{i+1}/{len(MODELS)}] {name}")
        result = benchmark_model(name, repo, filename, quant, size, tier)
        results.append(result)
        
        # Save incrementally
        with open(RESULTS_FILE, "a") as f:
            f.write(json.dumps(result) + "\n")
    
    # Restore production service
    print("\nRestoring production service...")
    run_cmd("sudo systemctl start qwen35-llm.service", timeout=30)
    
    # Summary
    print("\n" + "=" * 60)
    print("BENCHMARK SUMMARY")
    print("=" * 60)
    
    successful = [r for r in results if r["status"] == "success"]
    failed = [r for r in results if r["status"] != "success"]
    
    print(f"\nSuccessful: {len(successful)}/{len(results)}")
    print(f"Failed: {len(failed)}/{len(results)}")
    
    if successful:
        print("\nTop performers by GPU utilization:")
        sorted_by_gpu = sorted(successful, key=lambda x: x.get("gpu_util_best", 0), reverse=True)
        for r in sorted_by_gpu[:5]:
            cfg = r["best_config"]["config"]
            print(f"  {r['model']:30s} {r['gen_tps']:>8.2f} tok/s  GPU: {r.get('gpu_util_best', 0):>5.1f}%  ctx={cfg['ctx_size']} threads={cfg['threads']} batch={cfg['batch_size']}")
        
        print("\nTop performers by speed:")
        sorted_by_speed = sorted(successful, key=lambda x: x["gen_tps"], reverse=True)
        for r in sorted_by_speed[:5]:
            cfg = r["best_config"]["config"]
            print(f"  {r['model']:30s} {r['gen_tps']:>8.2f} tok/s  GPU: {r.get('gpu_util_best', 0):>5.1f}%  ctx={cfg['ctx_size']} threads={cfg['threads']} batch={cfg['batch_size']}")
    
    if failed:
        print("\nFailed models:")
        for r in failed:
            print(f"  {r['model']:30s} [{r['status']}]")
    
    print(f"\nResults saved to {RESULTS_FILE}")
    print(f"Finished: {time.strftime('%Y-%m-%dT%H:%M:%SZ')}")

if __name__ == "__main__":
    main()
