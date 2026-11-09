# Freeing memory before loading a model

The Jetson Orin Nano Super 8 GB shares physical RAM between the CPU and integrated GPU. Model weights, the KV cache (attention state for the active context), CUDA work buffers, and the OS all compete for that memory. A GGUF's on-disk size is only one part of the budget. [NVIDIA CUDA for Tegra](https://docs.nvidia.com/cuda/cuda-for-tegra-appnote/index.html#memory-management)

## Before loading a model

1. **Identify the running workload.** Save any work and let active requests finish. On the Jetson, inspect running containers if you use Docker, and check the process list for inference servers and other large workloads.

   ```bash
   docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}'
   ps -eo pid,rss,comm,args --sort=-rss | head -n 15
   ```

2. **Stop the old model through its owner.** Use the command that matches your setup, replacing the example service or container name with the one you identified. If systemd manages a container, stop the unit. For a server running in your foreground terminal, press Ctrl+C there. Wait for the workload to exit and repeat the inspection in step 1 to catch any automatic restart. [Docker stop](https://docs.docker.com/reference/cli/docker/container/stop/)

   ```bash
   # systemd-managed workload
   sudo systemctl stop your-llm.service

   # Standalone Docker container
   docker stop your-llm-container
   ```

   If a port is still occupied, identify its owner with `sudo ss -ltnp` before stopping anything else. Close unused desktop applications and other inference workloads you control, such as embedding or vision servers.

3. **Check the recovered headroom.** Run these on the Jetson host, outside any container.

   ```bash
   free -h
   swapon --show
   vmstat 1 6
   tegrastats --interval 1000
   ```

   - Read `available` in `free -h`. Linux estimates how much memory new applications can use without swapping, including memory it expects to reclaim from caches. This is a system-wide estimate. CUDA allocations and container limits can still fail earlier. [Linux /proc documentation](https://docs.kernel.org/filesystems/proc.html#meminfo)
   - In `vmstat`, skip the first row when judging current swap activity. Sustained nonzero `si` or `so` in the following samples means active paging. Used swap by itself can persist when the system is idle.
   - Watch `RAM`, `SWAP`, and `lfb` in `tegrastats`. The largest free block is a clue about physical memory fragmentation. Total usable headroom comes from the other readings. Leave `tegrastats` running in a second terminal during load and the first request, then press Ctrl+C to stop it. [NVIDIA tegrastats reference](https://docs.nvidia.com/jetson/archives/r36.5/DeveloperGuide/AT/JetsonLinuxDevelopmentTools/TegrastatsUtility.html)

   In the Bonsai 2 27B test, available RAM returned to its 6.7 GiB baseline after the process exited. The decode run had reached 6,749 MB sampled RAM use. Use a before-and-after reading like this to check that the model's memory has been released. [On-device memory observations](results/2026-11-09-bonsai2-27b.md#memory-observations)

4. **Load one model with a small context.** Start at 2,048 or 4,096 tokens with one slot, if the model and workload allow it. Leave space for the system prompt, input, and generated answer, including reasoning tokens. Check that startup completes and that a representative request fits before raising context or enabling concurrency. [Launch example](methodology.md#launch-a-local-test-server)

## If the model still fails to load

| Symptom | Next check or adjustment |
| --- | --- |
| Low available RAM before launch | Recheck which service or container owns the previous model and whether it restarted. Compare against a known idle baseline. Inspect large background processes and close only those you own and can safely stop. |
| Allocation failure at launch | Use a smaller GGUF or reduce context. Check the runtime's model, KV, and compute buffer allocations in the startup log. Check any Docker or systemd memory limit as well as host RAM. |
| Launch works but a long prompt fails | Try a smaller prompt or smaller prefill batch or microbatch. Use a quantized KV cache only if the pinned build and model support it, and retest answer quality and stability. KV cache format and size depend on the model and runtime. [llama.cpp server flags](https://github.com/ggml-org/llama.cpp/tree/master/tools/server) |
| Generation slows sharply under load | Correlate throughput with `vmstat` swap activity, `tegrastats` clocks and temperatures, and the runtime's offload logs. Try a smaller model or context before increasing swap. |
| Server exits unexpectedly | Check the runtime logs and `sudo journalctl -k -b --no-pager \| grep -Ei 'out of memory\|oom-kill\|killed process'`. For Docker, check `docker inspect --format '{{.State.OOMKilled}}' your-llm-container` if the container still exists. Exit status 137 by itself only shows SIGKILL. |

Keep swap configured as intended for the host. Zram compresses pages in RAM, and disk-backed swap can slow inference when actively paging. Cycling swap can pull swapped pages back into scarce RAM and fail under pressure. [Linux zram documentation](https://docs.kernel.org/admin-guide/blockdev/zram.html) · [util-linux swapoff manual](https://man7.org/linux/man-pages/man8/swapoff.8.html)

Leave Linux page cache reclamation to the kernel during normal model swaps. Writing to `drop_caches` evicts reclaimable filesystem caches and can make subsequent loads slower. Stop the model to release its live allocations. If a controlled cold-load experiment requires cache eviction, document the cache policy and use the same policy across compared runs. [Linux VM sysctl documentation](https://docs.kernel.org/admin-guide/sysctl/vm.html#drop-caches)
