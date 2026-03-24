#!/usr/bin/env python3
"""
collect-results.py — Parse benchmark results and generate summary tables.

Usage:
    python3 scripts/collect-results.py results/2026-03-24
    python3 scripts/collect-results.py results/2026-03-24 --format markdown
    python3 scripts/collect-results.py results/2026-03-24 --format json --output summary.json
"""

import argparse
import json
import os
import sys
from pathlib import Path


def load_results(results_dir):
    """Load all JSON result files from a directory."""
    results = []
    p = Path(results_dir)
    if not p.is_dir():
        print(f"Error: {results_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    for f in sorted(p.glob('*.json')):
        try:
            with open(f) as fh:
                data = json.load(fh)
                if 'error' not in data:
                    results.append(data)
        except (json.JSONDecodeError, OSError) as e:
            print(f"Warning: skipping {f}: {e}", file=sys.stderr)

    return results


def summarize(results):
    """Group results by role and compute summaries."""
    roles = {}
    for r in results:
        role = r.get('role', 'unknown')
        if role not in roles:
            roles[role] = {
                'tasks': [],
                'total_tokens': 0,
                'total_ms': 0,
                'model': r.get('model', 'unknown'),
            }
        roles[role]['tasks'].append({
            'task_id': r['task_id'],
            'task_name': r['task_name'],
            'tokens': r['tokens'],
            'elapsed_ms': r['elapsed_ms'],
            'tok_per_sec': r.get('tok_per_sec', '0'),
        })
        roles[role]['total_tokens'] += r['tokens']
        roles[role]['total_ms'] += r['elapsed_ms']

    for role, data in roles.items():
        if data['total_ms'] > 0:
            data['avg_tok_per_sec'] = round(
                data['total_tokens'] * 1000 / data['total_ms'], 1
            )
        else:
            data['avg_tok_per_sec'] = 0

    return roles


def format_markdown(roles):
    """Generate a Markdown summary table."""
    lines = ['# Benchmark Results\n']

    for role, data in sorted(roles.items()):
        lines.append(f'## {role} (model: {data["model"]})')
        lines.append('')
        lines.append(f'| Task | Tokens | Time (ms) | tok/s |')
        lines.append(f'|------|--------|-----------|-------|')
        for t in data['tasks']:
            lines.append(
                f'| {t["task_name"]} | {t["tokens"]} | {t["elapsed_ms"]} | {t["tok_per_sec"]} |'
            )
        lines.append('')
        lines.append(
            f'**Total:** {data["total_tokens"]} tokens, '
            f'{data["total_ms"]}ms, '
            f'{data["avg_tok_per_sec"]} avg tok/s'
        )
        lines.append('')

    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='Collect benchmark results')
    parser.add_argument('results_dir', help='Directory containing result JSON files')
    parser.add_argument('--format', choices=['markdown', 'json'], default='markdown')
    parser.add_argument('--output', help='Output file (default: stdout)')
    args = parser.parse_args()

    results = load_results(args.results_dir)
    if not results:
        print('No valid results found.', file=sys.stderr)
        sys.exit(1)

    print(f'Loaded {len(results)} results from {args.results_dir}', file=sys.stderr)

    roles = summarize(results)

    if args.format == 'json':
        output = json.dumps(roles, indent=2)
    else:
        output = format_markdown(roles)

    if args.output:
        with open(args.output, 'w') as f:
            f.write(output)
        print(f'Written to {args.output}', file=sys.stderr)
    else:
        print(output)


if __name__ == '__main__':
    main()
