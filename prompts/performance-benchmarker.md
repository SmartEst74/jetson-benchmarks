# Performance Benchmarker — Benchmark Prompts

**Purpose**: Test a model's ability to analyze performance data, identify bottlenecks, and recommend optimizations.

**Scoring**: Each prompt is graded on correctness (30%), completeness (25%), code quality (20%), robustness (15%), documentation (10%).

---

## Prompt PB-1: LLM Inference Analysis (Complexity: ★★★★☆)

**Tests**: Performance analysis, bottleneck identification

```
Analyze LLM inference data from a Jetson Orin Nano:

Hardware:
- Jetson Orin Nano 8GB
- Qwen3.5-4B Q8_0 (4.48GB)
- llama.cpp b8095

5 runs:
- Gen: 10.2, 10.4, 10.5, 10.3, 10.6 tok/s
- Prompt: 245, 258, 261, 252, 256 tok/s
- RAM: 6.1, 6.2, 6.1, 6.1, 6.2 GiB
- Temp: 58, 61, 63, 65, 62°C

Theoretical limit: 15.2 tok/s (68 GB/s ÷ 4.48 GB)
Actual efficiency: 68.4%

Explain the efficiency gap, identify the bottleneck, analyze thermal trend, provide optimization recommendations.
```

**Expected**: Memory bandwidth analysis, thermal throttling explanation, KV cache overhead, optimization suggestions.

---

## Prompt PB-2: Web Server Benchmark (Complexity: ★★★☆☆)

**Tests**: Load testing methodology, metrics interpretation

```
Analyze these load test results for a Python FastAPI server:

Configuration:
- 4 uvicorn workers
- 8GB RAM, 4 vCPUs
- Endpoint: POST /api/chat (LLM proxy)

Results at 100 concurrent users:
- p50 latency: 250ms
- p95 latency: 1200ms
- p99 latency: 3500ms
- Throughput: 45 req/s
- Error rate: 2.3% (mostly 503s)
- CPU: 95%
- RAM: 7.2GB

Identify the bottleneck and recommend 3 specific optimizations.
```

**Expected**: Worker exhaustion, queue buildup, connection pooling, caching, horizontal scaling.

---

## Prompt PB-3: Database Query Optimization (Complexity: ★★★★★)

**Tests**: SQL optimization, indexing, query plans

```
Optimize this slow PostgreSQL query:

```sql
SELECT 
    u.name,
    COUNT(DISTINCT o.id) as order_count,
    SUM(o.total) as total_spent,
    MAX(o.created_at) as last_order
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
LEFT JOIN order_items oi ON o.id = oi.order_id
LEFT JOIN products p ON oi.product_id = p.id
WHERE p.category = 'electronics'
    AND o.created_at >= '2025-01-01'
    AND u.status = 'active'
GROUP BY u.id, u.name
HAVING COUNT(DISTINCT o.id) > 5
ORDER BY total_spent DESC
LIMIT 100;

EXPLAIN ANALYZE shows:
- Seq Scan on users (cost=0.00..45231.00 rows=500000)
- Hash Join (cost=12345.00..98765.00 rows=1000)
- Sort (cost=5000.00..5001.00 rows=100)
- Planning Time: 15ms
- Execution Time: 4500ms
```

Provide: index recommendations, rewritten query, expected improvement.
```

**Expected**: Composite indexes, query restructuring, subquery pre-filtering, covering indexes.
