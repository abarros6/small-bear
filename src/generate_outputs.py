#!/usr/bin/env python3
"""
Generate model outputs from the validation set for evaluation.

Loads each adapter, runs inference on data/{role}/valid.jsonl (no system prompt,
matching training conditions), and writes results to outputs/.

Output format per example:
    {"instruction": "...", "response": "...", "role": "...", "model_size": "...", "latency": 0.0}

Usage:
    python src/generate_outputs.py                    # 3B, both roles
    python src/generate_outputs.py --model-size 1b   # 1B ablation
    python src/generate_outputs.py --role age_5_11   # single role
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from constants import ROLES
from inference import load_model, generate_response

DATA_DIR = Path("data")
OUTPUT_DIR = Path("outputs")


def generate_for_role(role: str, model_size: str, max_tokens: int) -> list:
    valid_path = DATA_DIR / role / "valid.jsonl"
    if not valid_path.exists():
        print(f"  Error: {valid_path} not found. Run prepare_data.py first.")
        return []

    # valid.jsonl is in messages format — extract user content
    instructions = []
    with open(valid_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            ex = json.loads(line)
            user_msg = next(m for m in ex["messages"] if m["role"] == "user")
            instructions.append(user_msg["content"])

    if not instructions:
        print(f"  Warning: {valid_path} is empty.")
        return []

    print(f"\n  Loading {role} ({model_size})...")
    model, tokenizer = load_model(role, model_size=model_size)

    results = []
    for i, instruction in enumerate(instructions):
        # No system prompt — matches training conditions
        response, latency = generate_response(
            model, tokenizer, instruction,
            system_prompt=None,
            max_tokens=max_tokens,
        )
        results.append({
            "instruction": instruction,
            "response": response,
            "role": role,
            "model_size": model_size,
            "latency": round(latency, 3),
        })
        print(f"  [{i+1:3d}/{len(instructions)}] {latency:.2f}s  {instruction[:55]}")

    return results


def main():
    parser = argparse.ArgumentParser(description="Generate model outputs for evaluation")
    parser.add_argument("--role", choices=ROLES, help="Single role (default: all roles)")
    parser.add_argument("--model-size", choices=["3b", "1b"], default="3b",
                        help="Base model size (default: 3b)")
    parser.add_argument("--max-tokens", type=int, default=300)
    args = parser.parse_args()

    roles = [args.role] if args.role else ROLES
    OUTPUT_DIR.mkdir(exist_ok=True)

    all_results = []
    for role in roles:
        results = generate_for_role(role, args.model_size, args.max_tokens)
        if not results:
            continue

        role_path = OUTPUT_DIR / f"{role}_{args.model_size}_outputs.jsonl"
        with open(role_path, "w") as f:
            for r in results:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"  → {role_path} ({len(results)} examples)")
        all_results.extend(results)

    if all_results:
        combined_path = OUTPUT_DIR / f"all_{args.model_size}_outputs.jsonl"
        with open(combined_path, "w") as f:
            for r in all_results:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"\n  → {combined_path} ({len(all_results)} total)")


if __name__ == "__main__":
    main()
