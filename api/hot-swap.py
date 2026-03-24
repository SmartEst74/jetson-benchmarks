#!/usr/bin/env python3
"""
Jetson LLM Hot-Swap API

Lightweight HTTP API that switches the active LLM model on the Jetson
based on the requested agent role. Uses llm-switch.sh under the hood.

Endpoints:
  POST /api/switch    — Switch to optimal model for a role
  GET  /api/status    — Current model and API info
  GET  /api/roles     — List available roles and model mappings

Usage:
  python3 hot-swap.py                        # default port 8001
  python3 hot-swap.py --port 8001 --host 0.0.0.0

Requirements: Python 3.8+ (stdlib only, no pip dependencies)
"""

import json
import subprocess
import sys
import os
import argparse
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

ROLES_JSON = os.path.join(os.path.dirname(__file__), '..', 'data', 'agent-roles.json')
LLM_SWITCH = os.path.expanduser('~/llm-switch.sh')
LLM_API = 'http://192.168.1.23:8000/v1'

# Model name → llm-switch.sh argument
# Maps model names to their llm-switch.sh aliases
# Updated based on comprehensive benchmark results (2026-03-24)
MODEL_SWITCH_MAP = {
    'Qwen3.5-4B': 'qwen35-4b',
    'Qwen3.5-9B': 'qwen35-9b',
    'Nanbeige4-3B-Thinking': 'nanbeige4-3b',
    'Qwen3-8B': 'qwen3-8b',
    'xLAM-2-1b-fc-r': 'xlam-2-1b',
    'Qwen3-1.7B': 'qwen3-1.7b',
    'Arch-Agent-1.5B': 'arch-agent-1.5b',
    'Granite-4.0-350m': 'granite-4.0-350m',
    'Hammer2.1-3b': 'hammer2.1-3b',
    'xLAM-2-3b-fc-r': 'xlam-2-3b',
    'Llama-3.2-3B-Instruct': 'llama-3.2-3b',
    'Arch-Agent-3B': 'arch-agent-3b',
    'Gemma-3-4b-it': 'gemma-3-4b',
    'MiniCPM3-4B': 'minicpm3-4b',
    'Qwen3-4B-Instruct-2507': 'qwen3-4b-2507',
    # Tier 2 models (larger, may need smaller context)
    'xLAM-2-8b-fc-r': 'xlam-2-8b',
    'Hammer2.1-7b': 'hammer2.1-7b',
    'BitAgent-Bounty-8B': 'bitagent-8b',
    'ToolACE-2-8B': 'toolace-2-8b',
    'Llama-3.1-8B-Instruct': 'llama-3.1-8b',
    'Granite-3.2-8B-Instruct': 'granite-3.2-8b',
    'Command-R7B': 'command-r7b',
    'CoALM-8B': 'coalm-8b',
    'Falcon3-7B-Instruct': 'falcon3-7b',
    'Qwen3-14B': 'qwen3-14b',
    'Phi-4': 'phi-4',
    'Gemma-3-12b-it': 'gemma-3-12b',
}


def load_roles():
    with open(ROLES_JSON, 'r') as f:
        return json.load(f)


def get_current_model():
    """Get currently running model by checking llm-switch.sh status or Docker container."""
    try:
        # Try llm-switch.sh status first
        result = subprocess.run(
            [LLM_SWITCH, 'status'],
            capture_output=True, text=True, timeout=10
        )
        output = result.stdout.strip().lower()
        
        # Map status output to model name
        for model_name, alias in MODEL_SWITCH_MAP.items():
            if alias in output or model_name.lower().replace('-', '').replace('.', '') in output.replace('-', '').replace('.', ''):
                return model_name
        
        # Fallback: check Docker container logs for model name
        docker_result = subprocess.run(
            ['docker', 'logs', 'llm-server', '2>&1'],
            capture_output=True, text=True, timeout=10
        )
        docker_output = docker_result.stdout.lower()
        for model_name, alias in MODEL_SWITCH_MAP.items():
            if model_name.lower().replace('-', '').replace('.', '') in docker_output.replace('-', '').replace('.', ''):
                return model_name
        
        return output or 'unknown'
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return 'unknown'


def switch_model(model_name):
    """Switch to the specified model using llm-switch.sh or Docker commands."""
    switch_arg = MODEL_SWITCH_MAP.get(model_name)
    if not switch_arg:
        return False, f'No switch mapping for {model_name}. Available models: {list(MODEL_SWITCH_MAP.keys())}'
    
    try:
        # First try llm-switch.sh
        if os.path.exists(LLM_SWITCH):
            result = subprocess.run(
                [LLM_SWITCH, switch_arg],
                capture_output=True, text=True, timeout=120
            )
            if result.returncode == 0:
                return True, f'Switched to {model_name} via llm-switch.sh'
            else:
                # llm-switch.sh failed, try Docker approach
                print(f'llm-switch.sh failed: {result.stderr[:200]}')
        
        # Fallback: Docker-based model switching
        # Stop current container
        subprocess.run(['docker', 'stop', 'llm-server'], capture_output=True, timeout=30)
        time.sleep(2)
        
        # Start new model container
        # This is a simplified version - in production, you'd need proper model paths
        model_path = f'/home/jetson/models/{model_name}.gguf'
        
        # Check if model exists
        if not os.path.exists(model_path):
            # Try to find model in cache
            cache_dir = '/home/jetson/models/llama-cache'
            possible_files = [
                f'{model_name}-Q8_0.gguf',
                f'{model_name}-Q4_K_M.gguf',
                f'{model_name}.gguf',
            ]
            for fname in possible_files:
                full_path = os.path.join(cache_dir, fname)
                if os.path.exists(full_path):
                    model_path = full_path
                    break
        
        if not os.path.exists(model_path):
            return False, f'Model file not found for {model_name}. Download first.'
        
        # Determine appropriate context size based on model size
        model_size_gb = os.path.getsize(model_path) / (1024**3)
        if model_size_gb > 6:
            ctx_size = 2048
        elif model_size_gb > 4:
            ctx_size = 4096
        else:
            ctx_size = 8192
        
        # Start container
        docker_cmd = [
            'docker', 'run', '-d',
            '--name', 'llm-server',
            '--runtime', 'nvidia',
            '--gpus', 'all',
            '-v', '/home/jetson/models:/models',
            '-p', '8000:8000',
            'ghcr.io/nvidia-ai-iot/llama_cpp:latest-jetson-orin',
            '/usr/local/bin/llama-server',
            '--model', model_path,
            '--host', '0.0.0.0',
            '--port', '8000',
            '--ctx-size', str(ctx_size),
            '--n-gpu-layers', '99',
            '--flash-attn', 'on',
            '--threads', '4'
        ]
        
        result = subprocess.run(docker_cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            # Wait for model to be ready
            time.sleep(10)
            return True, f'Switched to {model_name} via Docker (ctx={ctx_size})'
        else:
            return False, f'Docker start failed: {result.stderr[:200]}'
            
    except subprocess.TimeoutExpired:
        return False, 'Model switch timed out (120s)'
    except Exception as e:
        return False, f'Model switch error: {str(e)}'


class HotSwapHandler(BaseHTTPRequestHandler):
    def _json(self, code, data):
        body = json.dumps(data, indent=2).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path

        if path == '/api/status':
            model = get_current_model()
            self._json(200, {
                'model': model,
                'api': LLM_API,
                'switch_script': LLM_SWITCH,
                'available_models': list(MODEL_SWITCH_MAP.keys()),
            })

        elif path == '/api/roles':
            try:
                roles_data = load_roles()
                summary = []
                for role in roles_data.get('roles', []):
                    summary.append({
                        'id': role['id'],
                        'name': role['name'],
                        'icon': role['icon'],
                        'recommended_model': role['recommended_model'],
                        'recommended_quant': role['recommended_quant'],
                        'key_metric': role['key_metric'],
                        'task_count': len(role.get('tasks', [])),
                    })
                self._json(200, {'roles': summary})
            except Exception as e:
                self._json(500, {'error': str(e)})

        elif path == '/':
            self._json(200, {
                'service': 'Jetson LLM Hot-Swap API',
                'endpoints': {
                    'POST /api/switch': 'Switch to optimal model for a role',
                    'GET /api/status': 'Current model and status',
                    'GET /api/roles': 'Available roles and mappings',
                },
            })
        else:
            self._json(404, {'error': 'Not found'})

    def do_POST(self):
        path = urlparse(self.path).path

        if path != '/api/switch':
            self._json(404, {'error': 'Not found'})
            return

        length = int(self.headers.get('Content-Length', 0))
        if length > 4096:
            self._json(413, {'error': 'Request too large'})
            return

        try:
            body = json.loads(self.rfile.read(length))
        except (json.JSONDecodeError, ValueError):
            self._json(400, {'error': 'Invalid JSON'})
            return

        role_id = body.get('role', '').strip()
        if not role_id:
            self._json(400, {'error': 'Missing "role" field'})
            return

        # Validate role_id against known roles
        try:
            roles_data = load_roles()
            role = next((r for r in roles_data.get('roles', []) if r['id'] == role_id), None)
        except Exception as e:
            self._json(500, {'error': f'Failed to load roles: {e}'})
            return

        if not role:
            valid = [r['id'] for r in roles_data.get('roles', [])]
            self._json(400, {'error': f'Unknown role "{role_id}". Valid: {valid}'})
            return

        target_model = role['recommended_model']
        current = get_current_model()

        if current == target_model:
            self._json(200, {
                'switched': False,
                'message': f'Already running {target_model}',
                'model': target_model,
                'role': role_id,
                'api': LLM_API,
                'ready': True,
            })
            return

        ok, msg = switch_model(target_model)
        self._json(200 if ok else 500, {
            'switched': ok,
            'model': target_model if ok else current,
            'previous_model': current,
            'role': role_id,
            'api': LLM_API,
            'ready': ok,
            'message': msg,
        })

    def log_message(self, format, *args):
        sys.stderr.write(f'[hot-swap] {args[0]} {args[1]} {args[2]}\n')


def main():
    parser = argparse.ArgumentParser(description='Jetson LLM Hot-Swap API')
    parser.add_argument('--host', default='0.0.0.0', help='Bind address')
    parser.add_argument('--port', type=int, default=8001, help='Port')
    args = parser.parse_args()

    server = HTTPServer((args.host, args.port), HotSwapHandler)
    print(f'Hot-Swap API listening on {args.host}:{args.port}')
    print(f'  POST /api/switch  — switch model by role')
    print(f'  GET  /api/status  — current model info')
    print(f'  GET  /api/roles   — available roles')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nShutting down.')
        server.server_close()


if __name__ == '__main__':
    main()
