# API Tester — Benchmark Prompts

**Purpose**: Test a model's ability to create comprehensive test suites for APIs.

**Scoring**: Each prompt is graded on correctness (30%), completeness (25%), code quality (20%), robustness (15%), documentation (10%).

---

## Prompt AT-1: Pytest Suite (Complexity: ★★★★☆)

**Tests**: Test methodology, edge cases, assertions

```
Generate a pytest test suite for an OpenAI-compatible LLM API at localhost:8000/v1.

Endpoints:
- POST /v1/chat/completions
- GET /v1/models

Cover:
- Happy path for each endpoint
- Input validation (missing messages, invalid model, empty array)
- Error handling (500 responses, timeouts)
- Performance (response under 30s)
- Security (proper headers, no sensitive data leaks)

Use pytest fixtures and clear test names.
```

**Expected**: Complete test file with fixtures, parametrized tests, proper assertions.

---

## Prompt AT-2: Contract Testing (Complexity: ★★★☆☆)

**Tests**: API contracts, schema validation

```
Create contract tests for this API response schema:

```json
{
  "type": "object",
  "required": ["id", "status", "created_at"],
  "properties": {
    "id": {"type": "string", "format": "uuid"},
    "status": {"enum": ["pending", "processing", "completed", "failed"]},
    "created_at": {"type": "string", "format": "date-time"},
    "result": {"type": "object", "nullable": true},
    "error": {"type": "string", "nullable": true}
  }
}
```

Write tests using jsonschema and pytest that validate:
- Valid responses pass
- Missing required fields fail
- Invalid enum values fail
- Null handling is correct
```

**Expected**: Schema validation tests with parametrized cases.

---

## Prompt AT-3: Chaos Testing (Complexity: ★★★★★)

**Tests**: Resilience testing, failure modes, recovery

```
Design a chaos testing suite for a microservices architecture:

Services:
- API Gateway (port 8000)
- Auth Service (port 8001)
- User Service (port 8002)
- Database (PostgreSQL)

Failure scenarios to test:
- Auth service timeout
- Database connection exhaustion
- Network partition between services
- Memory leak simulation
- Disk full condition

Write the test framework using Python and provide the first 2 chaos tests.
```

**Expected**: Chaos framework design, timeout tests, circuit breaker validation, recovery verification.
