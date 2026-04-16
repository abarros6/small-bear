#!/usr/bin/env python3
"""
Evaluation suite for Dr. Beary Good.

Measures:
  1. Readability — five corroborating metrics per response:
       - Flesch-Kincaid grade (target <= 7.0 for age_5_11; no ceiling for age_12_18)
       - SMOG index (designed for health text; reliable on longer responses only)
       - Gunning Fog index (penalises polysyllabic words)
       - Coleman-Liau index (character-based; independent cross-check)
       - Lexical diversity / TTR (unique words / total words)
  2. Latency and throughput (requires 'latency'/'token_count'/'tokens_per_second' fields):
       - Average latency, min/max, fraction under 1.0s VR target
       - Avg tokens/response and tokens/second
  3. Inter-role style separation (--separation flag; requires scikit-learn):
       - TF-IDF + logistic regression, 5-fold CV
       - Accuracy ~0.50 = no separation, ~0.90+ = strong register difference

Usage:
    # Evaluate training data quality
    cat data/source/train/*.jsonl > /tmp/all_train.jsonl
    python src/evaluate.py --data /tmp/all_train.jsonl

    # Evaluate model outputs with latency and style separation
    python src/evaluate.py --data outputs/all_3b_outputs.jsonl --latency --separation

    # Save results to file
    python src/evaluate.py --data outputs/all_3b_outputs.jsonl --latency --separation \\
        --output results/standard_3b_eval.txt

    # Evaluate a single role
    python src/evaluate.py --data outputs/all_3b_outputs.jsonl --role age_5_11
"""

import argparse
import io
import json
import sys
from pathlib import Path

import textstat

sys.path.insert(0, str(Path(__file__).parent))
from constants import ROLES


# ---------------------------------------------------------------------------
# Reading level evaluation
# ---------------------------------------------------------------------------


class ReadingLevelEvaluator:
    """Evaluates Flesch-Kincaid grade level of responses."""

    # age_5_11: ages 5–11 span grades K–6; target FK <= 7.0
    #   FK 5.0 was too aggressive — hospital role titles (e.g. "Spiritual Care
    #   Specialist", "interpretation services") are inherently multi-syllable and
    #   drive FK up even when surrounding sentences are simple and age-appropriate.
    #   FK 7.0 is appropriate for the top of the range (age 11, grade 6).
    # age_12_18: grades 6–12, no hard ceiling — measure and report
    FK_TARGETS = {
        "age_5_11": 7.0,
    }

    def evaluate(self, response: str) -> dict:
        fk_grade = textstat.flesch_kincaid_grade(response)
        flesch_ease = textstat.flesch_reading_ease(response)
        # SMOG requires ~30 sentences for reliability; textstat returns 0 for short texts
        smog = textstat.smog_index(response)
        fog = textstat.gunning_fog(response)
        coleman = textstat.coleman_liau_index(response)
        word_count = textstat.lexicon_count(response, removepunct=True)
        sentence_count = textstat.sentence_count(response)
        avg_sentence_length = word_count / max(sentence_count, 1)
        # Type-token ratio: unique words / total words — lower = simpler, more repetitive vocabulary
        words = [w.lower() for w in response.split() if w.isalpha()]
        lexical_diversity = round(len(set(words)) / len(words), 3) if words else 0.0

        return {
            "fk_grade": round(fk_grade, 1),
            "flesch_ease": round(flesch_ease, 1),
            "smog": round(smog, 1),
            "gunning_fog": round(fog, 1),
            "coleman_liau": round(coleman, 1),
            "word_count": word_count,
            "sentence_count": sentence_count,
            "avg_sentence_length": round(avg_sentence_length, 1),
            "lexical_diversity": lexical_diversity,
        }

    def check_target(self, response: str, role: str) -> tuple:
        """Check if a response meets the FK grade target for its role.

        Returns:
            (passes: bool, fk_grade: float, target: float | None)
            passes is True if no target defined for this role.
        """
        fk = textstat.flesch_kincaid_grade(response)
        target = self.FK_TARGETS.get(role)
        if target is None:
            return True, round(fk, 1), None
        return fk <= target, round(fk, 1), target


# ---------------------------------------------------------------------------
# Latency evaluator
# ---------------------------------------------------------------------------


class LatencyEvaluator:
    """Evaluates response latency against the 1.0s VR real-time target."""

    TARGET_SECONDS = 1.0

    def evaluate(self, latency_seconds: float) -> dict:
        return {
            "latency_ms": round(latency_seconds * 1000, 1),
            "passes_target": latency_seconds < self.TARGET_SECONDS,
            "target_ms": self.TARGET_SECONDS * 1000,
        }


# ---------------------------------------------------------------------------
# Aggregate evaluation
# ---------------------------------------------------------------------------


def evaluate_dataset(data_path: str, role_filter: str = None, check_latency: bool = False):
    """Evaluate all examples in a JSONL file."""
    reading = ReadingLevelEvaluator()

    examples = []
    with open(data_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            ex = json.loads(line)
            if role_filter and ex["role"] != role_filter:
                continue
            examples.append(ex)

    if not examples:
        print(f"No examples found" + (f" for role '{role_filter}'" if role_filter else ""))
        return

    results = {}
    for ex in examples:
        role = ex["role"]
        if role not in results:
            results[role] = {
                "count": 0,
                "fk_grades": [],
                "fk_pass": 0,
                "fk_fail": 0,
                "fk_target": reading.FK_TARGETS.get(role),
                "smog_grades": [],
                "fog_grades": [],
                "coleman_grades": [],
                "lexical_diversities": [],
                "word_counts": [],
                "latencies": [],
                "token_counts": [],
                "tokens_per_second": [],
            }

        r = results[role]
        r["count"] += 1

        rl = reading.evaluate(ex["response"])
        r["fk_grades"].append(rl["fk_grade"])
        r["smog_grades"].append(rl["smog"])
        r["fog_grades"].append(rl["gunning_fog"])
        r["coleman_grades"].append(rl["coleman_liau"])
        r["lexical_diversities"].append(rl["lexical_diversity"])
        r["word_counts"].append(rl["word_count"])

        passes, fk, target = reading.check_target(ex["response"], role)
        if target is not None:
            if passes:
                r["fk_pass"] += 1
            else:
                r["fk_fail"] += 1

        if check_latency and "latency" in ex:
            r["latencies"].append(ex["latency"])
        if "token_count" in ex:
            r["token_counts"].append(ex["token_count"])
        if "tokens_per_second" in ex:
            r["tokens_per_second"].append(ex["tokens_per_second"])

    print(f"\n{'='*60}")
    print(f"EVALUATION REPORT")
    print(f"{'='*60}")
    print(f"File: {data_path}")
    print(f"Total examples: {len(examples)}")

    for role in ROLES:
        if role not in results:
            continue
        r = results[role]
        print(f"\n{'-'*40}")
        print(f"Role: {role} ({r['count']} examples)")
        print(f"{'-'*40}")

        grades = r["fk_grades"]
        avg_fk = sum(grades) / len(grades)
        avg_smog = sum(r["smog_grades"]) / len(r["smog_grades"])
        avg_fog = sum(r["fog_grades"]) / len(r["fog_grades"])
        avg_coleman = sum(r["coleman_grades"]) / len(r["coleman_grades"])
        avg_lex = sum(r["lexical_diversities"]) / len(r["lexical_diversities"])
        print(f"\n  Reading Level:")
        print(f"    FK grade      — avg: {avg_fk:.1f}, min: {min(grades):.1f}, max: {max(grades):.1f}")
        print(f"    SMOG          — avg: {avg_smog:.1f}  (reliable only on long texts; 0 = too short)")
        print(f"    Gunning Fog   — avg: {avg_fog:.1f}")
        print(f"    Coleman-Liau  — avg: {avg_coleman:.1f}")
        print(f"    Lexical div.  — avg: {avg_lex:.3f}  (TTR: 0=repetitive, 1=all unique words)")
        print(f"    Avg word count: {sum(r['word_counts'])/len(r['word_counts']):.0f}")

        if r["fk_target"] is not None:
            total = r["fk_pass"] + r["fk_fail"]
            pct = 100 * r["fk_pass"] / total if total else 0
            print(f"    FK <= {r['fk_target']} target: {r['fk_pass']}/{total} pass ({pct:.1f}%)")
            if r["fk_fail"] > 0:
                worst = sorted(
                    zip(grades, [e["instruction"] for e in examples if e["role"] == role]),
                    reverse=True,
                )[:3]
                print(f"    Worst offenders:")
                for fk, q in worst:
                    if fk > r["fk_target"]:
                        print(f"      FK {fk:.1f}: '{q[:60]}'")

        if check_latency and r["latencies"]:
            lats = r["latencies"]
            avg_lat = sum(lats) / len(lats)
            under_target = sum(1 for l in lats if l < LatencyEvaluator.TARGET_SECONDS)
            print(f"\n  Latency ({len(lats)} samples):")
            print(f"    avg: {avg_lat:.2f}s, min: {min(lats):.2f}s, max: {max(lats):.2f}s")
            print(f"    Under {LatencyEvaluator.TARGET_SECONDS}s target: {under_target}/{len(lats)}")
            if r["token_counts"]:
                avg_tc = sum(r["token_counts"]) / len(r["token_counts"])
                avg_tps = sum(r["tokens_per_second"]) / len(r["tokens_per_second"])
                print(f"    Avg tokens/response: {avg_tc:.0f}")
                print(f"    Avg tokens/second:   {avg_tps:.1f}")

    print(f"\n{'-'*40}")
    print(f"Category Distribution")
    print(f"{'-'*40}")
    cats = {}
    for ex in examples:
        key = f"{ex['role']}/{ex.get('category', 'unknown')}"
        cats[key] = cats.get(key, 0) + 1
    for key in sorted(cats):
        print(f"  {key}: {cats[key]}")

    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"  Total examples: {len(examples)}")
    for role in ROLES:
        if role in results and results[role]["fk_target"] is not None:
            r = results[role]
            total_fk = r["fk_pass"] + r["fk_fail"]
            print(f"  {role} FK <= {r['fk_target']}: {r['fk_pass']}/{total_fk}")
    print()


def evaluate_role_separation(data_path: str):
    """Measure inter-role style separation using TF-IDF + logistic regression (5-fold CV).

    High accuracy = the two roles are stylistically distinct — strong evidence the adapter
    is encoding register in its weights, not just random noise.

    Interpretation:
        ~0.50  chance (no separation — adapter has no effect)
        ~0.70  moderate separation
        ~0.90+ strong, consistent register difference
    """
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.model_selection import cross_val_score
    except ImportError:
        print("\nInter-role separation skipped — scikit-learn not installed.")
        print("  pip install scikit-learn")
        return

    texts, labels = [], []
    with open(data_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            ex = json.loads(line)
            if ex.get("role") in ROLES:
                texts.append(ex["response"])
                labels.append(ex["role"])

    role_counts = {r: labels.count(r) for r in ROLES}
    if any(v < 10 for v in role_counts.values()):
        print("\nInter-role separation skipped — need at least 10 examples per role.")
        return

    vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
    X = vectorizer.fit_transform(texts)
    clf = LogisticRegression(max_iter=1000, random_state=42)
    scores = cross_val_score(clf, X, labels, cv=5, scoring="accuracy")

    print(f"\n{'-'*40}")
    print(f"Inter-Role Style Separation (TF-IDF + LR, 5-fold CV)")
    print(f"{'-'*40}")
    print(f"  Examples: {role_counts}")
    print(f"  Accuracy: {scores.mean():.3f} ± {scores.std():.3f}")
    print(f"  ~0.50=chance  ~0.70=moderate  ~0.90+=strong separation")


def main():
    parser = argparse.ArgumentParser(description="Evaluate Dr. Beary Good dataset/responses")
    parser.add_argument("--data", required=True, help="Path to JSONL data file")
    parser.add_argument("--role", choices=ROLES,
                        help="Evaluate only a specific role")
    parser.add_argument("--latency", action="store_true",
                        help="Include latency stats (requires 'latency' field in data)")
    parser.add_argument("--separation", action="store_true",
                        help="Run inter-role style separation analysis (requires scikit-learn)")
    parser.add_argument("--output", metavar="PATH",
                        help="Save results to this file in addition to printing to stdout "
                             "(e.g. results/3b_fast_eval.txt)")
    args = parser.parse_args()

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        buf = io.StringIO()

        class _Tee:
            def write(self, s):
                sys.__stdout__.write(s)
                buf.write(s)
            def flush(self):
                sys.__stdout__.flush()

        sys.stdout = _Tee()

    evaluate_dataset(args.data, role_filter=args.role, check_latency=args.latency)

    if args.separation:
        evaluate_role_separation(args.data)

    if args.output:
        sys.stdout = sys.__stdout__
        with open(args.output, "w") as f:
            f.write(buf.getvalue())
        print(f"\nResults saved to {args.output}")


if __name__ == "__main__":
    main()
