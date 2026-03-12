#!/usr/bin/env python3
"""
Prepare per-role train/valid splits from source JSONL files.

Expects source directory to have two subdirectories:
    data/source/train/     — training examples (one JSONL per category)
    data/source/validate/  — hand-curated validation examples (one JSONL per category)

Reads:
    Format: {"instruction": "...", "response": "...", "role": "...", "category": "..."}

Writes:
    data/{role}/train.jsonl
    data/{role}/valid.jsonl
    Format: {"messages": [{"role": "user", ...}, {"role": "assistant", ...}]}

No system prompt is included in the training data. The adapter weights must encode
the age-appropriate communication register directly. The VR application can inject
its own system prompt at inference time without conflicting with trained behaviour.

The messages format is required by mlx_lm.lora CLI (ChatDataset + apply_chat_template).
Pre-formatting chat strings causes double-BOS tokens and NaN gradients — do not do that.

Usage:
    python src/prepare_data.py
    python src/prepare_data.py --source-dir data/source --seed 42
"""

import argparse
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from constants import ROLES

# Map source data role strings → canonical role names used throughout the pipeline.
# Source data was generated with "5-11" / "12-18"; pipeline uses "age_5_11" / "age_12_18".
ROLE_MAP = {
    "5-11":      "age_5_11",
    "12-18":     "age_12_18",
    "age_5_11":  "age_5_11",   # already canonical — pass through
    "age_12_18": "age_12_18",
}


def load_examples(source_dir: Path) -> dict:
    """Load examples from all JSONL files in source_dir, grouped by role."""
    by_role = {role: [] for role in ROLES}
    source_files = sorted(source_dir.glob("*.jsonl"))
    if not source_files:
        print(f"  Warning: no .jsonl files found in {source_dir}")
        return by_role

    total = 0
    for source_path in source_files:
        file_count = 0
        with open(source_path) as f:
            for lineno, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    ex = json.loads(line)
                except json.JSONDecodeError as e:
                    print(f"  Warning: {source_path.name} line {lineno}: {e}")
                    continue

                role = ROLE_MAP.get(ex.get("role"))
                if role is None:
                    print(f"  Warning: unknown role '{ex.get('role')}' in {source_path.name} line {lineno}, skipping")
                    continue
                ex["role"] = role  # normalise in-place before storing

                instruction = ex.get("instruction", "").strip()
                response = ex.get("response", "").strip()
                if not instruction or not response:
                    print(f"  Warning: empty instruction/response in {source_path.name} line {lineno}, skipping")
                    continue

                by_role[role].append(ex)
                file_count += 1
        total += file_count
        print(f"    Loaded {file_count:4d} examples from {source_path.name}")

    print(f"    Total: {total}")
    return by_role


def to_messages(ex: dict) -> dict:
    """Convert a source example to the messages format expected by mlx_lm CLI.

    No system prompt — style is encoded entirely in the adapter weights.
    The VR application injects its own system prompt at inference time.
    """
    return {
        "messages": [
            {"role": "user",      "content": ex["instruction"].strip()},
            {"role": "assistant", "content": ex["response"].strip()},
        ]
    }


def write_jsonl(path: Path, examples: list):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        for ex in examples:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")


def prepare(source_dir: Path, data_dir: Path, seed: int):
    train_dir = source_dir / "train"
    validate_dir = source_dir / "validate"

    for d in (train_dir, validate_dir):
        if not d.is_dir():
            print(f"Error: expected subdirectory not found: {d}")
            print(f"  Source directory must contain train/ and validate/ subdirectories.")
            raise SystemExit(1)

    print(f"\nSource: {source_dir}")
    print(f"  train/    → {train_dir}")
    print(f"  validate/ → {validate_dir}")
    print(f"  Seed: {seed}\n")

    print("Loading train/")
    by_role_train = load_examples(train_dir)
    print("\nLoading validate/")
    by_role_valid = load_examples(validate_dir)

    print()
    for role in ROLES:
        train_examples = by_role_train[role]
        valid_examples = by_role_valid[role]

        if not train_examples:
            print(f"  {role}: 0 train examples — skipping")
            continue

        # Shuffle training set for training stability
        rng = random.Random(seed)
        rng.shuffle(train_examples)

        train_out = [to_messages(ex) for ex in train_examples]
        valid_out = [to_messages(ex) for ex in valid_examples]

        train_path = data_dir / role / "train.jsonl"
        valid_path = data_dir / role / "valid.jsonl"

        write_jsonl(train_path, train_out)
        write_jsonl(valid_path, valid_out)

        cats = {}
        for ex in train_examples:
            c = ex.get("category", "unknown")
            cats[c] = cats.get(c, 0) + 1

        print(f"  {role}: {len(train_examples)} train / {len(valid_examples)} valid")
        for cat, count in sorted(cats.items()):
            print(f"    {cat}: {count}")
        print(f"    → {train_path}")
        print(f"    → {valid_path}")

    print()


def main():
    parser = argparse.ArgumentParser(description="Prepare per-role train/valid splits")
    parser.add_argument(
        "--source-dir",
        default="data/source",
        help="Directory containing train/ and validate/ subdirectories (default: data/source)",
    )
    parser.add_argument(
        "--data-dir",
        default="data",
        help="Output data directory (default: data)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for training shuffle (default: 42)",
    )
    args = parser.parse_args()

    source_dir = Path(args.source_dir)
    if not source_dir.is_dir():
        print(f"Error: source directory not found: {source_dir}")
        raise SystemExit(1)

    prepare(source_dir, Path(args.data_dir), args.seed)


if __name__ == "__main__":
    main()
