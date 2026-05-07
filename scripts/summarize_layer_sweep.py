#!/usr/bin/env python3
"""
Summarize layer sweep results (Experiment §1 optional depth).

Reads outputs/layer_sweep_rank4_layers*_age_5_11_outputs.jsonl,
computes FK pass rate and latency per run, then prints per-seed and
aggregated (mean ± std across seeds) tables showing the effect of
num_layers at fixed rank=4 on Llama 1B and 3B.

Usage:
    python scripts/summarize_layer_sweep.py
    python scripts/summarize_layer_sweep.py --output results/layer_sweep/summary.md
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

# Matches: layer_sweep_rank4_layers8_seed42_1b_age_5_11_outputs.jsonl
_NAME_RE = re.compile(
    r"layer_sweep_rank4_layers(\d+)_seed(\d+)_(.+?)_age_5_11_outputs\.jsonl"
)

MODEL_ORDER  = ["1b", "3b"]
LAYERS_ORDER = [4, 8, 16]


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

    files = sorted(OUTPUTS_DIR.glob(f"layer_sweep_rank4_layers*_{ROLE}_outputs.jsonl"))
    if not files:
        print(f"No layer sweep outputs found in {OUTPUTS_DIR}/. "
              "Run scripts/run_layer_sweep.sh first.")
        return

    rows = []
    for f in files:
        m = _NAME_RE.match(f.name)
        if not m:
            continue
        num_layers, seed, model = int(m.group(1)), int(m.group(2)), m.group(3)
        metrics = compute_metrics(f)
        rows.append({"num_layers": num_layers, "seed": seed, "model": model, **metrics})

    if not rows:
        print("No matching layer sweep output files found.")
        return

    # Group by (num_layers, model) for aggregation
    groups: dict = defaultdict(list)
    for row in rows:
        groups[(row["num_layers"], row["model"])].append(row)

    lines = []
    lines.append("# Layer Sweep Results — rank=4 fixed, num_layers ∈ {4, 8, 16}")
    lines.append(f"\nModels: Llama 1B, Llama 3B | Role: `{ROLE}` | "
                 f"FK target: ≤ {FK_TARGET} | rank=4 (fixed)")
    lines.append("\nnum_layers=8 reuses rank sweep adapters (no additional training).")

    # ── Per-seed table ────────────────────────────────────────────────────────
    lines.append("\n## Per-Run Results\n")
    hdr = (f"{'Model':<6} {'Layers':>6} {'Seed':>6}  "
           f"{'FK avg':>6}  {'FK ≤ 7.0':>10}  {'Avg lat':>8}  {'TPS':>7}")
    sep = "-" * len(hdr)
    lines.append(hdr)
    lines.append(sep)

    for model in MODEL_ORDER:
        for num_layers in LAYERS_ORDER:
            for row in sorted(groups.get((num_layers, model), []), key=lambda r: r["seed"]):
                lines.append(
                    f"{row['model']:<6} {row['num_layers']:>6} {row['seed']:>6}"
                    f"  {row['fk_avg']:>6.2f}"
                    f"  {row['fk_pass']:>3}/{row['n']:<3} {row['fk_pct']:>5.1f}%"
                    f"  {_fmt_lat(row['lat_avg']):>8}"
                    f"  {_fmt_tps(row['tps_avg']):>7}"
                )
        lines.append("")

    # ── Aggregated table ──────────────────────────────────────────────────────
    lines.append("\n## Aggregated (mean ± std across seeds)\n")
    hdr2 = (f"{'Model':<6} {'Layers':>6}  "
            f"{'FK avg':>12}  {'FK ≤ 7.0 %':>12}  {'Avg lat':>12}  {'TPS':>10}")
    lines.append(hdr2)
    lines.append("-" * len(hdr2))

    for model in MODEL_ORDER:
        for num_layers in LAYERS_ORDER:
            group = groups.get((num_layers, model), [])
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
                f"{model:<6} {num_layers:>6}"
                f"  {fk_str:>12}"
                f"  {pct_str:>12}"
                f"  {lat_str:>12}"
                f"  {tps_str:>10}"
            )
        lines.append("")

    # ── Layer effect: layers=8 vs layers=16 at rank=4 ────────────────────────
    lines.append("\n## Effect of num_layers at rank=4\n")
    lines.append("Comparison of interest: layers=8 (Fast original) vs layers=16 (Standard "
                 "original) at fixed rank=4.")
    lines.append("Also includes layers=4 to show the lower end of the range.\n")
    lines.append(f"{'Model':<6}  {'L=4 FK%':>9}  {'L=8 FK%':>9}  {'L=16 FK%':>10}  "
                 f"{'L=8→16 Δ':>10}  {'Winner (8 vs 16)':>18}")
    lines.append("-" * 70)

    for model in MODEL_ORDER:
        pcts = {}
        for num_layers in LAYERS_ORDER:
            group = groups.get((num_layers, model), [])
            if group:
                pcts[num_layers] = _mean([r["fk_pct"] for r in group])

        l4  = f"{pcts[4]:.1f}%"  if 4  in pcts else "—"
        l8  = f"{pcts[8]:.1f}%"  if 8  in pcts else "—"
        l16 = f"{pcts[16]:.1f}%" if 16 in pcts else "—"

        if 8 in pcts and 16 in pcts:
            delta  = pcts[16] - pcts[8]
            delta_str = f"{delta:+.1f}%"
            winner = "layers=16" if delta > 0 else ("layers=8" if delta < 0 else "Tie")
        else:
            delta_str = "—"
            winner    = "—"

        lines.append(f"{model:<6}  {l4:>9}  {l8:>9}  {l16:>10}  {delta_str:>10}  {winner:>18}")

    lines.append("")
    lines.append("Interpretation: if layers=16 >> layers=8 at fixed rank=4, num_layers")
    lines.append("is an independent contributor to the crossover beyond rank alone.")

    output = "\n".join(lines)
    print(output)

    completed = len(rows)
    expected  = len(MODEL_ORDER) * len(LAYERS_ORDER) * 2  # 2 seeds
    print(f"\n{completed}/{expected} runs present in summary.")

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(output)
        print(f"Summary saved to {args.output}")


if __name__ == "__main__":
    main()
