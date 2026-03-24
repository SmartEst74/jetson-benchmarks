# Backend Architect — Benchmark Prompts

**Purpose**: Test a model's ability to design schemas, APIs, and distributed systems with proper security and scalability.

**Scoring**: Each prompt is graded on correctness (30%), completeness (25%), code quality (20%), robustness (15%), documentation (10%).

---

## Prompt BA-1: Multi-Tenant SaaS Schema (Complexity: ★★★★☆)

**Tests**: PostgreSQL, row-level security, indexing, schema design

```
Design a PostgreSQL schema for a multi-tenant SaaS project management tool.

Requirements:
- Tenant isolation via row-level security
- Projects with tasks (nested subtasks)
- Team members with roles (admin/manager/member)
- Activity audit log
- Include CREATE TABLE statements with proper types
- Indexes for common queries
- RLS policies
```

**Expected**: Complete schema with RLS policies, proper foreign keys, indexes on tenant_id and common query paths.

---

## Prompt BA-2: Rate Limiter (Complexity: ★★★☆☆)

**Tests**: Distributed systems, Redis patterns, API design

```
Design a distributed rate limiter for an API gateway.

Requirements:
- Per-user rate limiting (100 req/min)
- Per-endpoint rate limiting (different limits for /search vs /read)
- Sliding window algorithm
- Redis-backed for distributed deployment
- Return proper 429 responses with Retry-After header
- Include Redis commands and the Node.js/Python implementation
```

**Expected**: Redis sorted set or token bucket implementation, proper headers, edge cases handled.

---

## Prompt BA-3: Event-Driven Order System (Complexity: ★★★★★)

**Tests**: Event sourcing, saga pattern, error handling, idempotency

```
Design an event-driven order processing system for an e-commerce platform.

Flow:
1. Order placed → Reserve inventory
2. Payment processed → Confirm reservation
3. Shipping scheduled → Update order status
4. If payment fails → Release inventory

Requirements:
- Use event sourcing (no direct state mutations)
- Implement saga pattern for distributed transactions
- Handle partial failures (inventory reserved but payment fails)
- Idempotent event handlers
- Dead letter queue for failed events
- Include the event schema, handlers, and compensation logic
```

**Expected**: Event types, saga orchestrator, compensation handlers, idempotency keys.
