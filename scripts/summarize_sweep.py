#!/usr/bin/env python3
"""
Summarize Experiment §1 rank sweep results.

Reads outputs/rank*_{role}_outputs.jsonl, computes FK pass rate and latency
per run, then prints per-seed and aggregated (mean across seeds) tables.

Usage:
    python scripts/summarize_sweep.py
    python scripts/summarize_sweep.py --output results/sweeps/summary.md
"""

import argparse
import json
import math
import re
from collections import defaultdict
from pathlib import Path

import textstat

OUTPUTS_DIR = Path("outputs")
FK_TARGET   = 7.0
ROLE        = "age_5_11"

# Matches: rank4_layers8_seed42_qwen4bit_age_5_11_outputs.jsonl
_NAME_RE = re.compile(
    r"rank(\d+)_layers(\d+)_seed(\d+)_(.+?)_age_5_11_outputs\.jsonl"
)

MODEL_ORDER = ["1b", "3b", "qwen4bit"]
RANK_ORDER  = [2, 4, 8, 16]


def _mean(xs):
    return sum(xs) / len(xs) if xs else float("nan")


def _std(xs):
    if len(xs) < 2:
        return float("nan")
    m = _mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / len(xs))


def compute_metrics(path: Path) -> dict:
    fk_grades, latencies, tps_vals = [], [], []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            ex = json.loads(line)
            fk_grades.append(textstat.flesch_kincaid_grade(ex["response"]))
            if "latency" in ex:
                latencies.append(ex["latency"])
            if "tokens_per_second" in ex:
                tps_vals.append(ex["tokens_per_second"])

    n = len(fk_grades)
    fk_pass = sum(1 for g in fk_grades if g <= FK_TARGET)
    return {
        "n":       n,
        "fk_avg":  _mean(fk_grades),
        "fk_pass": fk_pass,
        "fk_pct":  100 * fk_pass / n if n else 0,
        "lat_avg": _mean(latencies) if latencies else None,
        "tps_avg": _mean(tps_vals)  if tps_vals  else None,
    }


def _fmt_lat(v):
    return f"{v:.2f}s" if v is not None and not math.isnan(v) else "—"


def _fmt_tps(v):
    return f"{v:.1f}" if v is not None and not math.isnan(v) else "—"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", help="Write summary Markdown to this path")
    args = parser.parse_args()

    files = sorted(OUTPUTS_DIR.glob(f"rank*_{ROLE}_outputs.jsonl"))
    if not files:
        print(f"No sweep outputs found in {OUTPUTS_DIR}/. Run scripts/run_exp1.sh first.")
        return

    rows = []
    for f in files:
        m = _NAME_RE.match(f.name)
        if not m:
            continue
        rank, layers, seed, model = int(m.group(1)), int(m.group(2)), int(m.group(3)), m.group(4)
        metrics = compute_metrics(f)
        rows.append({"rank": rank, "layers": layers, "seed": seed, "model": model, **metrics})

    if not rows:
        print("No matching sweep output files found.")
        return

    # Group by (rank, model) for aggregation
    groups: dict = defaultdict(list)
    for row in rows:
        groups[(row["rank"], row["model"])].append(row)

    lines = []
    lines.append("# Experiment §1 — Rank Sweep Results")
    lines.append(f"\nRole: `{ROLE}` | FK target: ≤ {FK_TARGET} | `num_layers=8` (fixed)")

    # ── Per-seed table ────────────────────────────────────────────────────────
    lines.append("\n## Per-Run Results\n")
    hdr = f"{'Model':<10} {'Rank':>4} {'Seed':>6}  {'FK avg':>6}  {'FK ≤ 7.0':>10}  {'Avg lat':>8}  {'TPS':>7}"
    sep = "-" * len(hdr)
    lines.append(hdr)
    lines.append(sep)

    for model in MODEL_ORDER:
        for rank in RANK_ORDER:
            for row in sorted(groups.get((rank, model), []), key=lambda r: r["seed"]):
                lines.append(
                    f"{row['model']:<10} {row['rank']:>4} {row['seed']:>6}"
                    f"  {row['fk_avg']:>6.2f}"
                    f"  {row['fk_pass']:>3}/{row['n']:<3} {row['fk_pct']:>5.1f}%"
                    f"  {_fmt_lat(row['lat_avg']):>8}"
                    f"  {_fmt_tps(row['tps_avg']):>7}"
                )
        lines.append("")

    # ── Aggregated table (mean ± std across seeds) ────────────────────────────
    lines.append("\n## Aggregated (mean ± std across seeds)\n")
    hdr2 = f"{'Model':<10} {'Rank':>4}  {'FK avg':>12}  {'FK ≤ 7.0 %':>12}  {'Avg lat':>12}  {'TPS':>10}"
    lines.append(hdr2)
    lines.append("-" * len(hdr2))

    for model in MODEL_ORDER:
        for rank in RANK_ORDER:
            group = groups.get((rank, model), [])
            if not group:
                continue
            fk_avgs = [r["fk_avg"] for r in group]
            fk_pcts = [r["fk_pct"] for r in group]
            lats    = [r["lat_avg"] for r in group if r["lat_avg"] is not None]
            tps_    = [r["tps_avg"] for r in group if r["tps_avg"] is not None]

            fk_str  = f"{_mean(fk_avgs):.2f} ± {_std(fk_avgs):.2f}"
            pct_str = f"{_mean(fk_pcts):.1f} ± {_std(fk_pcts):.1f}"
            lat_str = f"{_mean(lats):.2f}s ± {_std(lats):.2f}" if lats else "—"
            tps_str = f"{_mean(tps_):.1f} ± {_std(tps_):.1f}" if tps_ else "—"

            lines.append(
                f"{model:<10} {rank:>4}"
                f"  {fk_str:>12}"
                f"  {pct_str:>12}"
                f"  {lat_str:>12}"
                f"  {tps_str:>10}"
            )
        lines.append("")

    # ── Crossover summary ─────────────────────────────────────────────────────
    lines.append("\n## Crossover: Standard (rank=8) vs Fast (rank=4) per model\n")
    lines.append(f"{'Model':<10} {'Std (r=8) FK%':>14} {'Fast (r=4) FK%':>15} {'Winner':>8}")
    lines.append("-" * 52)
    for model in MODEL_ORDER:
        r8 = groups.get((8, model), [])
        r4 = groups.get((4, model), [])
        if not r8 or not r4:
            continue
        pct8 = _mean([r["fk_pct"] for r in r8])
        pct4 = _mean([r["fk_pct"] for r in r4])
        winner = "Standard" if pct8 > pct4 else ("Fast" if pct4 > pct8 else "Tie")
        lines.append(f"{model:<10} {pct8:>14.1f}% {pct4:>14.1f}%  {winner:>8}")
    lines.append("")

    output = "\n".join(lines)
    print(output)

    completed = len(rows)
    expected  = len(MODEL_ORDER) * len(RANK_ORDER) * 2  # 2 seeds
    print(f"\n{completed}/{expected} runs present in summary.")

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(output)
        print(f"Summary saved to {args.output}")


if __name__ == "__main__":
    main()
