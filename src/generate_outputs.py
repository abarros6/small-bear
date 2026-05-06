#!/usr/bin/env python3
"""
Generate model outputs from the validation set for evaluation.

Loads each adapter, runs inference on data/{role}/valid.jsonl (no system prompt,
matching training conditions), and writes results to outputs/.

Output format per example:
    {
        "instruction": "...",
        "response":    "...",
        "role":        "age_5_11" | "age_12_18",
        "model_size":  "3b" | "1b",
        "latency":     0.0,          # total generation time in seconds
        "token_count": 0,            # tokens in the response
        "tokens_per_second": 0.0     # throughput
    }

Usage:
    python src/generate_outputs.py                              # standard 3B, both roles
    python src/generate_outputs.py --model-size 1b             # standard 1B ablation
    python src/generate_outputs.py --variant fast              # fast 3B adapters
    python src/generate_outputs.py --variant fast --model-size 1b  # fast 1B
    python src/generate_outputs.py --base                      # base model, no adapter
    python src/generate_outputs.py --role age_5_11             # single role
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


def generate_for_role(role: str, model_size: str, max_tokens: int, variant: str = "",
                      use_base: bool = False, adapter_path_override: str = "") -> list:
    """Run inference on the validation set for one role and return results.

    Args:
        role:                  Role to evaluate — one of ROLES (e.g. 'age_5_11').
        model_size:            Base model size — '3b', '1b', 'qwen4bit', etc.
        max_tokens:            Hard token ceiling passed to generate_response.
        variant:               Adapter subdirectory prefix, e.g. 'fast'.
        use_base:              If True, load base model with no adapter.
        adapter_path_override: Explicit adapter directory path — used for sweep runs.

    Returns:
        List of result dicts, one per validation example.
    """
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

    desc = adapter_path_override or (f"{model_size}/{variant}" if variant else model_size)
    print(f"\n  Loading {role} ({desc}{' base' if use_base else ''})...")
    model, tokenizer = load_model(role, model_size=model_size, variant=variant, use_base=use_base,
                                  adapter_path_override=adapter_path_override)

    results = []
    for i, instruction in enumerate(instructions):
        # No system prompt — matches training conditions
        response, latency = generate_response(
            model, tokenizer, instruction,
            system_prompt=None,
            max_tokens=max_tokens,
        )
        token_count = len(tokenizer.encode(response))
        results.append({
            "instruction": instruction,
            "response": response,
            "role": role,
            "model_size": model_size,
            "latency": round(latency, 3),
            "token_count": token_count,
            "tokens_per_second": round(token_count / latency, 1) if latency > 0 else 0.0,
        })
        print(f"  [{i+1:3d}/{len(instructions)}] {latency:.2f}s  {instruction[:55]}")

    return results


def main():
    parser = argparse.ArgumentParser(description="Generate model outputs for evaluation")
    parser.add_argument("--role", choices=ROLES, help="Single role (default: all roles)")
    parser.add_argument("--model-size", choices=["3b", "1b", "qwen", "qwen4bit", "qwen_standard", "qwen4bit_standard"], default="3b",
                        help="Base model size (default: 3b)")
    parser.add_argument("--max-tokens", type=int, default=300)
    parser.add_argument("--variant", default="",
                        help="Adapter variant subdirectory, e.g. 'fast' → adapters/fast/{size}/{role}. "
                             "Output files will be prefixed with the variant name.")
    parser.add_argument("--base", action="store_true",
                        help="Run on the base model with no adapter (for baseline comparison).")
    parser.add_argument("--adapter-path", default="",
                        help="Explicit adapter directory path, overrides default path construction. "
                             "Use with --output-tag for sweep runs.")
    parser.add_argument("--output-tag", default="",
                        help="Override the output filename prefix (default: derived from --variant / --model-size). "
                             "E.g. --output-tag rank4_layers8_seed42_1b → "
                             "outputs/rank4_layers8_seed42_1b_age_5_11_outputs.jsonl")
    args = parser.parse_args()

    roles = [args.role] if args.role else ROLES
    OUTPUT_DIR.mkdir(exist_ok=True)

    if args.output_tag:
        tag = f"{args.output_tag}_"
    elif args.base:
        tag = "base_"
    elif args.variant:
        tag = f"{args.variant}_"
    else:
        tag = ""
    all_results = []
    for role in roles:
        results = generate_for_role(role, args.model_size, args.max_tokens, args.variant, args.base,
                                    adapter_path_override=args.adapter_path)
        if not results:
            continue

        # When --output-tag is given it already encodes model_size; don't double-append it.
        if args.output_tag:
            role_path = OUTPUT_DIR / f"{tag}{role}_outputs.jsonl"
        else:
            role_path = OUTPUT_DIR / f"{tag}{role}_{args.model_size}_outputs.jsonl"
        with open(role_path, "w") as f:
            for r in results:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"  → {role_path} ({len(results)} examples)")
        all_results.extend(results)

    if all_results:
        if args.output_tag:
            combined_path = OUTPUT_DIR / f"all_{args.output_tag}_outputs.jsonl"
        else:
            combined_path = OUTPUT_DIR / f"all_{tag}{args.model_size}_outputs.jsonl"
        with open(combined_path, "w") as f:
            for r in all_results:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"\n  → {combined_path} ({len(all_results)} total)")


if __name__ == "__main__":
    main()
