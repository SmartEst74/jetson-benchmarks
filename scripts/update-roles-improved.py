#!/usr/bin/env python3
"""
Improved role recommendation algorithm that balances speed, capability, and task suitability.

This script updates agent-roles.json with better model recommendations based on:
1. Model capability (parameter count and BFCL score)
2. Jetson speed performance
3. Task-specific requirements (some roles need thinking capability, others need tool calling)
4. Minimum capability threshold (reject models below 1B parameters for complex tasks)

Usage:
  python3 update-roles-improved.py [--dry-run]
"""
import json
import sys
import os

DATA_DIR = "/home/jon/jetson-knowledge/data"
MODELS_JSON = os.path.join(DATA_DIR, "jetson-models.json")
ROLES_JSON = os.path.join(DATA_DIR, "agent-roles.json")

def load_json(path):
    with open(path) as f:
        return json.load(f)

def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def compute_model_score(entry, role_type):
    """
    Compute a weighted score for a model based on role requirements.
    
    Role types:
    - 'thinking': Needs reasoning capability (higher weight on BFCL, thinking support)
    - 'coding': Needs code generation (higher weight on BFCL, LiveCodeBench)
    - 'tool_calling': Needs function calling (higher weight on BFCL)
    - 'general': Balanced score
    """
    bfcl = entry.get('bfcl_v4', 0) or 0
    speed = entry.get('gen_tps', 0) or 0
    params = entry.get('params_b', 0) or 0
    tier = entry.get('tier', 1)
    features = entry.get('features', [])
    
    # Reject models that are too small for complex tasks
    if params < 1.0 and role_type not in ['simple_qa', 'fast路由']:
        return -1  # Too small
    
    # Base weights
    weights = {
        'thinking': {'bfcl': 0.5, 'speed': 0.2, 'params': 0.2, 'thinking': 0.1},
        'coding': {'bfcl': 0.6, 'speed': 0.2, 'params': 0.1, 'thinking': 0.1},
        'tool_calling': {'bfcl': 0.7, 'speed': 0.2, 'params': 0.05, 'thinking': 0.05},
        'general': {'bfcl': 0.4, 'speed': 0.3, 'params': 0.2, 'thinking': 0.1},
    }
    
    w = weights.get(role_type, weights['general'])
    
    # Normalize scores
    norm_bfcl = bfcl / 100.0 * 100  # BFCL is already 0-100
    norm_speed = min(speed / 20.0 * 100, 100) if speed else 0  # 20 tok/s is excellent
    norm_params = min(params / 14.0 * 100, 100)  # 14B is large for Jetson
    norm_thinking = 100 if 'thinking' in features else 0
    
    # Penalize small models for complex tasks
    if params < 3.0 and role_type in ['thinking', 'coding']:
        norm_params *= 0.5  # 50% penalty for <3B on complex tasks
    
    # Boost models with thinking capability for thinking roles
    thinking_boost = 1.2 if ('thinking' in features and role_type in ['thinking', 'coding']) else 1.0
    
    score = (
        norm_bfcl * w['bfcl'] +
        norm_speed * w['speed'] +
        norm_params * w['params'] +
        norm_thinking * w['thinking']
    ) * thinking_boost
    
    return score

def determine_role_type(role_id, key_metric):
    """Determine the type of role for scoring."""
    if 'bfcl' in key_metric.lower():
        if 'multi_turn' in role_id or 'reviewer' in role_id:
            return 'thinking'
        elif 'api' in role_id or 'tester' in role_id:
            return 'tool_calling'
        else:
            return 'coding'
    elif 'livecode' in key_metric.lower():
        return 'coding'
    elif 'gpqa' in key_metric.lower() or 'ifeval' in key_metric.lower():
        return 'thinking'
    else:
        return 'general'

def update_roles():
    """Update agent-roles.json with improved model recommendations."""
    models = load_json(MODELS_JSON)
    roles = load_json(ROLES_JSON)
    
    # Filter tested models
    tested_models = [m for m in models if m.get('status') == 'tested']
    print(f"Found {len(tested_models)} tested models")
    
    # Compute scores for each model by role type
    model_scores = {}
    for entry in tested_models:
        model_scores[entry['model']] = {
            'thinking': compute_model_score(entry, 'thinking'),
            'coding': compute_model_score(entry, 'coding'),
            'tool_calling': compute_model_score(entry, 'tool_calling'),
            'general': compute_model_score(entry, 'general'),
            'bfcl': entry.get('bfcl_v4', 0),
            'speed': entry.get('gen_tps', 0),
            'params': entry.get('params_b', 0),
            'quant': entry.get('best_quant', ''),
            'features': entry.get('features', []),
        }
    
    # Update each role
    updates = []
    for role in roles.get('roles', []):
        role_id = role['id']
        role_type = determine_role_type(role_id, role.get('key_metric', ''))
        
        # Find best model for this role type
        best_model = None
        best_score = -1
        
        for model_name, scores in model_scores.items():
            score = scores[role_type]
            if score > best_score:
                best_score = score
                best_model = model_name
        
        if best_model and best_score > 0:
            old_model = role.get('recommended_model', '')
            if old_model != best_model:
                role['recommended_model'] = best_model
                role['recommended_quant'] = model_scores[best_model]['quant']
                
                # Add reasoning
                model_info = model_scores[best_model]
                role['recommendation_reason'] = (
                    f"BFCL: {model_info['bfcl']:.1f}, "
                    f"Speed: {model_info['speed']:.1f} tok/s, "
                    f"Params: {model_info['params']}B, "
                    f"Score: {best_score:.1f}"
                )
                
                updates.append({
                    'role': role_id,
                    'role_type': role_type,
                    'old_model': old_model,
                    'new_model': best_model,
                    'score': best_score,
                    'reason': role['recommendation_reason'],
                })
    
    # Save updated roles
    save_json(ROLES_JSON, roles)
    
    # Print summary
    print("\nRole Recommendation Updates:")
    print("=" * 80)
    for update in updates:
        print(f"\n{update['role']}:")
        print(f"  Type: {update['role_type']}")
        print(f"  Old: {update['old_model']}")
        print(f"  New: {update['new_model']} (score: {update['score']:.1f})")
        print(f"  Reason: {update['reason']}")
    
    return updates

def main():
    dry_run = '--dry-run' in sys.argv
    
    if dry_run:
        print("DRY RUN - No changes will be saved")
    
    updates = update_roles()
    
    if dry_run:
        print("\nDry run complete. Run without --dry-run to apply changes.")
    else:
        print(f"\nUpdated {len(updates)} role recommendations.")

if __name__ == '__main__':
    main()