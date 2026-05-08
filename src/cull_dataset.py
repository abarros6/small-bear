#!/usr/bin/env python3
"""
Dataset quality cull for Dr. Beary Good training data.

Flags weak training examples based on three criteria:
  1. FK grade > 9.0  for age_5_11 role  (too hard for target age group)
  2. Response word count < 30            (too terse to carry style signal)
  3. Formulaic opener                    (rote affirmations dilute register)

Usage:
    # Dry run — report only, no files changed
    python src/cull_dataset.py

    # Apply — rewrite source files with flagged examples removed
    python src/cull_dataset.py --apply

    # Adjust thresholds
    python src/cull_dataset.py --fk-threshold 8.0 --min-words 40
"""

import argparse
import json
import re
import sys
from pathlib import Path

import textstat

SOURCE_DIR = Path("data/source/train")

# FK grade ceiling for age_5_11 responses in *training* data.
# The model target is ≤7.0 at inference; we flag training examples above 9.0
# (not 7.0) because some legitimate examples use medical vocabulary that
# drives FK up despite otherwise appropriate language.
DEFAULT_FK_THRESHOLD = 9.0

# Minimum response length — below this the example carries too little style signal.
DEFAULT_MIN_WORDS = 30

# Responses that start with these patterns are formulaic.
# All matching is case-insensitive; strings are matched at the start of the response
# (after stripping leading whitespace).
FORMULAIC_PATTERNS = [
    r"great question",
    r"that'?s? a great",
    r"that'?s? a wonderful",
    r"that'?s? a fantastic",
    r"what a great",
    r"wonderful question",
    r"excellent question",
    r"of course[!,]",
    r"absolutely[!,]",
    r"certainly[!,]",
    r"sure thing",
    r"i'?m (so )?happy to help",
    r"i'?d be happy to",
    r"i'?d love to help",
    r"great[!,] ",
    r"wonderful[!,] ",
    r"excellent[!,] ",
    r"fantastic[!,] ",
]

_FORMULAIC_RE = re.compile(
    r"^(" + "|".join(FORMULAIC_PATTERNS) + r")",
    re.IGNORECASE,
)


def word_count(text: str) -> int:
    return textstat.lexicon_count(text, removepunct=True)


def fk_grade(text: str) -> float:
    return round(textstat.flesch_kincaid_grade(text), 1)


def is_formulaic(response: str) -> bool:
    return bool(_FORMULAIC_RE.match(response.strip()))


def flag_reasons(example: dict, fk_threshold: float, min_words: int) -> list[str]:
    reasons = []
    role = example.get("role", "")
    resp = example.get("response", "")

    wc = word_count(resp)
    if wc < min_words:
        reasons.append(f"short ({wc} words < {min_words})")

    if role in ("5-11", "age_5_11"):
        fk = fk_grade(resp)
        if fk > fk_threshold:
            reasons.append(f"FK {fk} > {fk_threshold}")

    if is_formulaic(resp):
        opener = resp.strip()[:50].replace("\n", " ")
        reasons.append(f'formulaic opener: "{opener}..."')

    return reasons


def load_source_files() -> dict[Path, list[dict]]:
    files = {}
    for path in sorted(SOURCE_DIR.glob("*.jsonl")):
        examples = []
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line:
                    examples.append(json.loads(line))
        files[path] = examples
    return files


def run(fk_threshold: float, min_words: int, apply: bool):
    files = load_source_files()

    total_in = 0
    total_flagged = 0
    all_flagged = []

    for path, examples in files.items():
        flagged = []
        for i, ex in enumerate(examples):
            reasons = flag_reasons(ex, fk_threshold, min_words)
            if reasons:
                flagged.append((i, ex, reasons))

        total_in += len(examples)
        total_flagged += len(flagged)
        all_flagged.extend(flagged)

        if flagged:
            print(f"\n{'─'*60}")
            print(f"{path.name}  ({len(flagged)} flagged / {len(examples)} total)")
            print(f"{'─'*60}")
            for _, ex, reasons in flagged:
                instr = ex.get("instruction", "")[:70].replace("\n", " ")
                role = ex.get("role", "?")
                print(f"  [{role}] {instr}")
                for r in reasons:
                    print(f"    • {r}")

    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"  Source examples:  {total_in}")
    print(f"  Flagged:          {total_flagged}  ({100*total_flagged/total_in:.1f}%)")
    print(f"  Would keep:       {total_in - total_flagged}")

    if not apply:
        print(f"\n  Dry run — no files changed. Re-run with --apply to remove flagged examples.")
        return

    # Rewrite source files
    removed = 0
    for path, examples in files.items():
        kept = []
        for i, ex in enumerate(examples):
            reasons = flag_reasons(ex, fk_threshold, min_words)
            if reasons:
                removed += 1
            else:
                kept.append(ex)

        with open(path, "w") as f:
            for ex in kept:
                f.write(json.dumps(ex, ensure_ascii=False) + "\n")

    print(f"\n  Removed {removed} examples. Source files rewritten.")
    print(f"  Run: python src/prepare_data.py   to rebuild train/valid splits.")


def main():
    parser = argparse.ArgumentParser(description="Cull weak training examples")
    parser.add_argument(
        "--fk-threshold", type=float, default=DEFAULT_FK_THRESHOLD,
        metavar="N",
        help=f"FK grade ceiling for age_5_11 responses (default: {DEFAULT_FK_THRESHOLD})",
    )
    parser.add_argument(
        "--min-words", type=int, default=DEFAULT_MIN_WORDS,
        metavar="N",
        help=f"Minimum response word count (default: {DEFAULT_MIN_WORDS})",
    )
    parser.add_argument(
        "--apply", action="store_true",
        help="Rewrite source files with flagged examples removed (default: dry run)",
    )
    args = parser.parse_args()
    run(args.fk_threshold, args.min_words, args.apply)


if __name__ == "__main__":
    main()
