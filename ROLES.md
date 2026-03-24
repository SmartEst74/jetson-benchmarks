# Agency-Agents Roles for Jetson LLM Benchmarking

> Testing LLMs against real agent role definitions from [agency-agents](https://github.com/msitarzewski/agency-agents)

## Why Real Roles Matter

Generic benchmarks (MMLU, HumanEval) tell you how smart a model is. **Role benchmarks tell you how useful it is.** We test each model against the actual role definitions used in production agent systems.

The [agency-agents](https://github.com/msitarzewski/agency-agents) project by [@msitarzewski](https://github.com/msitarzewski) defines 144+ specialized AI agent roles across 12 divisions. We selected 8 roles that best represent the diversity of tasks an edge-deployed LLM must handle:

## Selected Roles

### 🖥️ Frontend Developer
**Division**: Engineering | **Source**: [`engineering/engineering-frontend-developer.md`](https://github.com/msitarzewski/agency-agents/blob/main/engineering/engineering-frontend-developer.md)

Builds responsive, accessible, performant web applications. Tests code generation for React/Vue/Angular components, CSS systems, and performance optimization.

**Benchmark tasks**:
| # | Task | Difficulty | What It Tests |
|---|------|-----------|---------------|
| 1 | React Data Table Component | ⭐⭐⭐⭐ | TypeScript, virtualization, a11y, responsive design |
| 2 | CSS Animation System | ⭐⭐⭐ | CSS custom properties, prefers-reduced-motion |
| 3 | Performance Audit Fix | ⭐⭐⭐⭐⭐ | Bundle analysis, React optimization, Lighthouse |

---

### 🏗️ Backend Architect
**Division**: Engineering | **Source**: [`engineering/engineering-backend-architect.md`](https://github.com/msitarzewski/agency-agents/blob/main/engineering/engineering-backend-architect.md)

Designs scalable system architecture, database schemas, APIs. Tests system design thinking, SQL knowledge, distributed systems understanding.

**Benchmark tasks**:
| # | Task | Difficulty | What It Tests |
|---|------|-----------|---------------|
| 1 | Database Schema Design | ⭐⭐⭐⭐ | PostgreSQL, RLS, multi-tenancy, indexing |
| 2 | API Rate Limiter | ⭐⭐⭐⭐⭐ | Redis, sliding window, FastAPI middleware |
| 3 | Event-Driven Architecture | ⭐⭐⭐⭐ | Saga pattern, idempotency, DLQ, schema versioning |

---

### 👁️ Code Reviewer
**Division**: Engineering | **Source**: [`engineering/engineering-code-reviewer.md`](https://github.com/msitarzewski/agency-agents/blob/main/engineering/engineering-code-reviewer.md)

Provides constructive, actionable code reviews focused on correctness, security, maintainability, and performance.

**Benchmark tasks**:
| # | Task | Difficulty | What It Tests |
|---|------|-----------|---------------|
| 1 | Security-focused Review | ⭐⭐⭐⭐⭐ | SQL injection, JWT, CORS, OWASP mapping |
| 2 | Performance Code Review | ⭐⭐⭐⭐ | O(n²) detection, memory, date parsing |
| 3 | Shell Script Safety | ⭐⭐⭐ | Quoting, blast radius, error handling |

---

### 🔒 Security Engineer
**Division**: Engineering | **Source**: [`engineering/engineering-security-engineer.md`](https://github.com/msitarzewski/agency-agents/blob/main/engineering/engineering-security-engineer.md)

Threat modeling, vulnerability assessment, secure code review, security architecture. Tests adversarial thinking and OWASP knowledge.

**Benchmark tasks**:
| # | Task | Difficulty | What It Tests |
|---|------|-----------|---------------|
| 1 | STRIDE Threat Model | ⭐⭐⭐⭐⭐ | 6 STRIDE categories, Jetson-specific threats |
| 2 | Secure API Endpoint | ⭐⭐⭐⭐ | Path traversal, OOM, permissions, auth |
| 3 | Security Headers Audit | ⭐⭐⭐ | HSTS, CSP, X-Frame-Options, nginx config |

---

### 📚 Technical Writer
**Division**: Engineering | **Source**: [`engineering/engineering-technical-writer.md`](https://github.com/msitarzewski/agency-agents/blob/main/engineering/engineering-technical-writer.md)

Developer documentation architect. README files, API references, tutorials. Tests structured output, instruction following, and formatting.

**Benchmark tasks**:
| # | Task | Difficulty | What It Tests |
|---|------|-----------|---------------|
| 1 | Project README | ⭐⭐⭐ | Markdown structure, badges, config tables |
| 2 | API Reference (OpenAPI) | ⭐⭐⭐⭐ | Schema typing, curl examples, error codes |
| 3 | Step-by-Step Tutorial | ⭐⭐⭐ | Beginner-friendly, expected output, troubleshooting |

---

### 🤖 AI Engineer
**Division**: Engineering | **Source**: [`engineering/engineering-ai-engineer.md`](https://github.com/msitarzewski/agency-agents/blob/main/engineering/engineering-ai-engineer.md)

AI/ML engineer specializing in model deployment, optimization, and production integration. Tests domain expertise in inference, RAG, and MLOps.

**Benchmark tasks**:
| # | Task | Difficulty | What It Tests |
|---|------|-----------|---------------|
| 1 | Edge Inference Optimization | ⭐⭐⭐⭐⭐ | Quantization, KV cache, memory math, thermal |
| 2 | RAG Pipeline on 8GB | ⭐⭐⭐⭐ | Embedding + vector store + LLM in 8GB RAM |
| 3 | Model Evaluation Framework | ⭐⭐⭐⭐ | Benchmark design, auto-scoring, statistics |

---

### ⏱️ Performance Benchmarker
**Division**: Testing | **Source**: [`testing/testing-performance-benchmarker.md`](https://github.com/msitarzewski/agency-agents/blob/main/testing/testing-performance-benchmarker.md)

Performance testing and optimization specialist. Tests analytical reasoning, data interpretation, and metrics-driven recommendations.

**Benchmark tasks**:
| # | Task | Difficulty | What It Tests |
|---|------|-----------|---------------|
| 1 | Inference Performance Analysis | ⭐⭐⭐⭐ | Bandwidth math, thermal analysis, optimization |
| 2 | Load Test Design | ⭐⭐⭐ | Single-GPU constraints, k6/curl scripts |
| 3 | Comparative Benchmark Report | ⭐⭐⭐⭐ | Multi-model comparison, efficiency analysis |

---

### 🔌 API Tester
**Division**: Testing | **Source**: [`testing/testing-api-tester.md`](https://github.com/msitarzewski/agency-agents/blob/main/testing/testing-api-tester.md)

API testing and validation specialist. Tests ability to generate comprehensive test suites, contract tests, and failure scenarios.

**Benchmark tasks**:
| # | Task | Difficulty | What It Tests |
|---|------|-----------|---------------|
| 1 | API Test Suite (pytest) | ⭐⭐⭐⭐ | Happy path, validation, error handling, security |
| 2 | Contract Testing Design | ⭐⭐⭐ | Schema validation, CI pipeline, compatibility |
| 3 | Failure Scenario Matrix | ⭐⭐⭐⭐ | Network, resource, application, concurrency failures |

---

## How We Use These Roles

1. **System prompt**: Each model receives the role's identity and mission as system context
2. **Task prompt**: Domain-specific prompt from the task list above
3. **Measurement**: Generation speed, token count, thinking engagement, response quality
4. **Grading**: Each task has a 5-dimension rubric (correctness, completeness, code quality, robustness, documentation) with weighted scores

## Full Role Definitions

Complete role definitions are stored in the [roles/](roles/) directory, copied from the [agency-agents](https://github.com/msitarzewski/agency-agents) repository under MIT license.

## Adding New Roles

To add a new role from agency-agents:

1. Copy the role definition to `roles/<division>-<role-name>.md`
2. Add the role to `data/agent-roles.json` with benchmark tasks
3. Design 3 tasks that test the role's core capabilities
4. Create grading rubrics with 5 weighted dimensions
5. Run `python3 scripts/bench-roles-live.py` to benchmark

---

*Roles sourced from [agency-agents](https://github.com/msitarzewski/agency-agents) by [@msitarzewski](https://github.com/msitarzewski) — MIT License*
