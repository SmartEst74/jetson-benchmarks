# Jetson LLM Hot-Swap API

Lightweight HTTP API that switches the active LLM model on the Jetson based on the requested agent role.

## Quick Start

```bash
# On the Jetson (requires llm-switch.sh)
python3 api/hot-swap.py --port 8001
```

## Endpoints

### `POST /api/switch`

Switch to the optimal model for an agent role.

```bash
curl -X POST http://127.0.0.1:8001/api/switch \
  -H 'Content-Type: application/json' \
  -d '{"role": "tool_caller"}'
```

Response:
```json
{
  "switched": true,
  "model": "Nanbeige4-3B-Thinking",
  "previous_model": "Qwen3.5-4B",
  "role": "tool_caller",
  "api": "http://127.0.0.1:8000/v1",
  "ready": true,
  "message": "Model switched successfully"
}
```

### `GET /api/status`

Check the currently loaded model.

```bash
curl http://127.0.0.1:8001/api/status
```

### `GET /api/roles`

List available roles and their recommended models.

```bash
curl http://127.0.0.1:8001/api/roles
```

## Architecture

```
Agent Framework
    │
    ▼
Hot-Swap API (:8001)    ──→  llm-switch.sh  ──→  llama.cpp container
    │                                                    │
    └── Returns API endpoint (:8000/v1) ◄────────────────┘
```

The API reads role→model mappings from `data/agent-roles.json` and uses `llm-switch.sh` to swap models on the Jetson. It resolves the switch script path using `LLM_SWITCH_PATH`, then common paths (`~/llm-switch.sh`, `~/scripts/llm-switch.sh`, repo `scripts/llm-switch.sh`). Only one model runs at a time (8GB constraint).

## Requirements

- Python 3.8+ (stdlib only)
- `llm-switch.sh` available via one of the supported paths (or set `LLM_SWITCH_PATH`)
- `data/agent-roles.json` with role definitions

## Adding New Models

1. Test the model on Jetson and add results to `data/jetson-models.json`
2. Add a switch mapping in `MODEL_SWITCH_MAP` in `hot-swap.py`
3. Add model entry to `scripts/llm-switch.sh` on the Jetson (or your configured `LLM_SWITCH_PATH` script)
4. Update role recommendations in `data/agent-roles.json` if the new model is better
