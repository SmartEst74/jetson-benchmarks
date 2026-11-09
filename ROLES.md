# Role benchmarks

The project adapted eight roles from agency-agents for local LLM testing. The archived dataset defines three candidate tasks per role with weighted grading rubrics. Individual historical runs used one task per role. [Agency-agents role collection](https://github.com/msitarzewski/agency-agents)

| Role | Task families |
| --- | --- |
| Frontend Developer | React data tables, CSS animation, performance audits |
| Backend Architect | Multi-tenant schemas, rate limiting, event-driven design |
| Code Reviewer | Security review, performance review, shell safety |
| Security Engineer | STRIDE, endpoint hardening, security headers |
| Technical Writer | Project READMEs, OpenAPI references, tutorials |
| AI Engineer | Edge inference, RAG, evaluation design |
| Performance Benchmarker | Inference analysis, load testing, reporting |
| API Tester | Pytest suites, contract tests, failure matrices |

## Prompts and results

- **Task dataset and rubrics.** Use the run's actual runner to identify the prompt used. The dataset and standalone prompt files also contain tasks that were planned for broader coverage. [Archived task dataset][dataset] · [Prompt files][prompts] · [Role definitions][roles]
- **Qwen3.5-4B Q8_0, March 23.** The eight-role thinking run recorded six empty visible answers at a 1,024-token cap. The later 2,048-token run was interrupted by a server crash and some roles were rerun after restart. Treat response length and finish reason as completion evidence. [Qwen results][qwen-results] · [First runner][qwen-runner] · [Dual-mode runner][qwen-runner-v2]
- **Ternary-Bonsai-8B Q2_0, May 5.** The 4,096-output-cap run tabulated eight roles with and without a thinking prefix. The recorded build returned no separate reasoning field. Two roles hit the length cap, and the record flags one run with a different context setting. [Bonsai results][bonsai-results] · [Original runner][bonsai-runner]

Use the archived runners to inspect prompts and request settings. Use the [current methodology](docs/methodology.md) for a fresh run and record scored correctness separately from response length.

[dataset]: https://github.com/SmartEst74/jetson-benchmarks/blob/1c4196c794a39dc206453428593fffdf164e68bb/data/agent-roles.json
[prompts]: https://github.com/SmartEst74/jetson-benchmarks/tree/1c4196c794a39dc206453428593fffdf164e68bb/prompts
[roles]: https://github.com/SmartEst74/jetson-benchmarks/tree/1c4196c794a39dc206453428593fffdf164e68bb/roles
[qwen-results]: https://github.com/SmartEst74/jetson-benchmarks/blob/1c4196c794a39dc206453428593fffdf164e68bb/BENCHMARKS.md#qwen35-4b-q8_0--role-benchmark-results
[qwen-runner]: https://github.com/SmartEst74/jetson-benchmarks/blob/1c4196c794a39dc206453428593fffdf164e68bb/scripts/bench-roles-live.py
[qwen-runner-v2]: https://github.com/SmartEst74/jetson-benchmarks/blob/1c4196c794a39dc206453428593fffdf164e68bb/scripts/bench-roles-v2.py
[bonsai-results]: https://github.com/SmartEst74/jetson-benchmarks/blob/1c4196c794a39dc206453428593fffdf164e68bb/benchmarks/current-performance.md#role-benchmark-results-8-roles--think--no_think-max_tokens4096
[bonsai-runner]: https://github.com/SmartEst74/jetson-benchmarks/blob/1c4196c794a39dc206453428593fffdf164e68bb/scripts/bench-ternary-bonsai.py
