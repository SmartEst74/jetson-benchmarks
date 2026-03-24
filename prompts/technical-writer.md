# Technical Writer — Benchmark Prompts

**Purpose**: Test a model's ability to create clear, structured documentation for developers.

**Scoring**: Each prompt is graded on correctness (30%), completeness (25%), code quality (20%), robustness (15%), documentation (10%).

---

## Prompt TW-1: API Documentation (Complexity: ★★★★☆)

**Tests**: API documentation, examples, error handling

```
Write complete API documentation for a WebSocket chat service:

Endpoints:
- ws://localhost:8000/ws/{room_id}?token={jwt}
- POST /api/rooms (create room)
- GET /api/rooms/{id}/history?limit=50

Messages (client→server):
- {"type": "message", "content": "text"}
- {"type": "typing", "active": true}
- {"type": "ping"}

Messages (server→client):
- {"type": "message", "user": "name", "content": "text", "timestamp": "ISO8601"}
- {"type": "user_joined", "user": "name"}
- {"type": "user_left", "user": "name"}
- {"type": "error", "code": 400, "message": "reason"}

Include: connection flow, message examples, error codes, reconnection logic.
```

**Expected**: Complete docs with connection sequence, message schemas, error table, code examples.

---

## Prompt TW-2: README.md (Complexity: ★★★☆☆)

**Tests**: Project documentation, structure, clarity

```
Write a README.md for a tool called jetson-bench.

Include:
- Project title and one-line description
- Badge placeholders (build, version, license)
- Prerequisites (JetPack 6.2+, Docker, 8GB+ RAM)
- Install section
- Usage with 3 example commands and output
- Configuration table (6+ options)
- Troubleshooting with 3 common issues
- Contributing link
- MIT license

Under 180 lines. Use proper markdown formatting.
```

**Expected**: Well-structured README with all sections, proper code blocks, clear instructions.

---

## Prompt TW-3: Changelog and Migration Guide (Complexity: ★★★★★)

**Tests**: Version documentation, breaking changes, migration paths

```
Write a changelog and migration guide for upgrading from v2 to v3:

v2 API:
- POST /v1/complete (text completion)
- GET /v1/models (list models)

v3 API:
- POST /v1/chat/completions (chat format)
- POST /v1/embeddings (new)
- GET /v1/models (unchanged)

Breaking changes:
- /v1/complete removed, use /v1/chat/completions
- prompt field replaced with messages array
- max_tokens renamed to max_completion_tokens
- stop renamed to stop_sequences

Include: what changed, why, code examples (before/after), deprecation timeline.
```

**Expected**: Changelog format, clear before/after examples, migration steps, timeline.
