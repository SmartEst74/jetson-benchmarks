# Security Engineer — Benchmark Prompts

**Purpose**: Test a model's ability to perform threat modeling, identify vulnerabilities, and design security controls.

**Scoring**: Each prompt is graded on correctness (30%), completeness (25%), code quality (20%), robustness (15%), documentation (10%).

---

## Prompt SE-1: STRIDE Threat Model (Complexity: ★★★★☆)

**Tests**: Threat modeling methodology, OWASP knowledge

```
Perform a STRIDE threat model for this architecture:

A Jetson edge device runs an LLM inference API (HTTP, port 8000) on a local network.
Users SSH in to manage models. A hot-swap API (port 8001) switches models.
Models stored on NVMe. No firewall configured. IoT devices on same subnet.

For each STRIDE category, identify at least 2 threats with severity and mitigations.
```

**Expected**: Cover all 6 STRIDE categories (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege).

---

## Prompt SE-2: API Security Review (Complexity: ★★★☆☆)

**Tests**: API security, authentication, authorization

```
Review this API design for security issues:

```
POST /api/users/{id}/data
Headers: X-API-Key: abc123
Body: {"name": "John", "email": "john@example.com", "role": "admin"}

Response: 200 OK
{
  "user": {"id": 1, "name": "John", "email": "john@example.com", "role": "admin"},
  "token": "eyJhbGciOiJIUzI1NiJ9..."
}
```

Identify all security issues and recommend fixes.
```

**Expected**: API key in URL, no auth check, privilege escalation (setting role), returning sensitive data, token in response.

---

## Prompt SE-3: Container Escape Scenario (Complexity: ★★★★★)

**Tests**: Container security, Linux security, defense in depth

```
Analyze this Docker setup for container escape risks:

```dockerfile
FROM nvidia/cuda:12.2.0-runtime-ubuntu22.04
RUN apt-get update && apt-get install -y curl python3
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
EXPOSE 8000
CMD ["python3", "server.py"]
```

Run command: `docker run --privileged -v /:/host -p 8000:8000 myimage`

Identify all security issues and provide a hardened version.
```

**Expected**: --privileged flag, volume mount to root, no user isolation, no security options, suggest alternatives.
