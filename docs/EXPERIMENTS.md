# Forward Experiments Roadmap

This file is the source of truth for follow-up work after the paper (`../paper/Paper.tex`).
Sections are ordered by priority. Each entry includes a run count and a rough wall-clock
estimate so compute cost is visible at a glance.

For project context, hardware constraints, and the Critical Lessons that constrain training
choices, see `../CLAUDE.md`. For full results, methodology, and the limitations that motivate
this roadmap, see `../paper/Paper.tex` §§5–6.

---

## §1 — **COMPLETE** — Rank Sweep: Crossover Mechanism Identification

**Question.** Standard and Fast differ in both `rank` (8 vs. 4) and `num_layers` (16 vs. 8).
Which factor drives the crossover?

**Design:** Fixed `num_layers=8`, rank ∈ {2, 4, 8, 16}, 4 models (Llama 1B, 3B, Qwen 0.5B,
SmolLM2 360M), seeds 42 and 1337, role `age_5_11`. 32 runs total.

**Result:** Crossover persists at fixed `num_layers` → **rank is the operative variable**
(capacity regularization). Two regimes identified:
- Small-model (lower rank better): Llama 1B (peak r=2, 81%), Qwen 0.5B (peak r=2, 78%)
- Large-model (higher rank better): Llama 3B (peak r=8, 69%), SmolLM2 360M (peak r=16, 76%)

**Key finding:** Transformer depth, not total parameter count, predicts rank regime.
SmolLM2 360M (32 layers, hidden 960) behaves like a large model despite 360M parameters.

**Results:** `results/sweeps/summary.md` | Paper §6.1

**Infrastructure:** `scripts/gen_sweep_configs.py`, `scripts/run_exp1.sh`

**Optional depth (not yet done):**
- Layer sweep at fixed rank: `rank=4`, `num_layers ∈ {4, 8, 16}`, Llama 1B/3B, 2 seeds
  = 12 runs (~6 h). Quantifies the independent contribution of `num_layers` to the
  original Standard-vs-Fast comparison on Llama. Lower priority now that rank is confirmed
  as the primary driver.

---

## §2 — **PARTIALLY COMPLETE** — Alternative Model Family + Smaller Scales

**Question.** Is the crossover Llama-specific or architecture-general? Does it persist
at even smaller scales?

### SmolLM2 360M — COMPLETE

Standard/Fast adapters trained and evaluated (both age groups, seed 42). Rank sweep also
completed as part of §1 extension.

**Result:** Standard dominates on all metrics (84% FK, 0.950 classifier, 0.81s avg).
Fast is severely under-parameterized (64% FK, runaway response lengths). Standard follows
the large-model rank regime — confirmed by rank sweep.

**Results:** `results/smollm2_standard_eval.txt`, `results/smollm2_fast_eval.txt` | Paper §6.2

### Qwen 2 0.5B — COMPLETE (BF16 + 4-bit, Standard + Fast)

Both quantization variants produce identical outputs (< 5% TPS difference). Qwen Fast has
the lowest latency of any trained adapter (0.46s avg, 98% under 1s for age_5_11), and the
highest classifier accuracy (0.960). Rank sweep confirms Qwen is in the small-model regime
(peak at r=2).

**Results:** `results/qwen_eval.txt`, `results/qwen4bit_eval.txt` | Paper §6.2

### Qwen 2.5 family sweep — NOT STARTED

| Axis | Values |
|------|--------|
| Model | Qwen 2.5 0.5B-Instruct-4bit, Qwen 2.5 1.5B-Instruct-4bit, Qwen 2.5 3B-Instruct-4bit |
| Adapter config | Standard (r=8, 16 layers), Fast (r=4, 8 layers) |
| Role | both age groups |
| Seed | 42 |

Total: 2 configs × 3 models × 2 roles = **12 runs**. Wall-clock ~5–6 h.

Lower priority than it was — the Qwen 2 0.5B and SmolLM2 results already provide
cross-architecture evidence. This sweep would add a capacity ladder within the Qwen 2.5
family.

---

## §3 — Quick Wins — **COMPLETE**

### Standard adapter perplexity — DONE

Table 1 in the paper now reports validation perplexity for all 8 Llama adapter configurations.
Values were obtained via a post-hoc `--test` pass (full-sequence cross-entropy, not masked) on
`data/{role}/valid.jsonl` using the step-600 checkpoint for each adapter.

Command used:
```
mlx_lm.lora --model <base> --adapter-path adapters/{size}/{role} --data data/{role} --test --val-batches -1
```

Results (val loss / PPL):
| Config | age_5_11 | age_12_18 |
|--------|----------|-----------|
| Standard-3B | 2.900 / 18.17 | 2.830 / 16.95 |
| Standard-1B | 3.185 / 24.17 | 3.105 / 22.31 |
| Fast-3B     | 3.034 / 20.77 | 3.073 / 21.61 |
| Fast-1B     | 3.106 / 22.32 | 2.985 / 19.79 |

**Key finding:** Perplexity crossover corroborates FK crossover — Standard-3B < Fast-3B;
Fast-1B < Standard-1B. Supports the capacity-regularization interpretation.

Note: these values are higher than the training-time masked val loss (1.7–1.9 for Fast runs)
because the `--test` pass includes prompt tokens in the loss.

---

## §4 — Infrastructure — COMPLETE

All infrastructure items from the original roadmap are implemented:

1. ✅ Parameterized training scripts (`train_sweep.sh` accepts config path)
2. ✅ Sweep config generator (`scripts/gen_sweep_configs.py`) — now supports 4 models
   including SmolLM2 (with `data/smollm` path override)
3. ✅ Multi-seed aggregation in `scripts/summarize_sweep.py`
4. ✅ Full pipeline script `scripts/run_exp1.sh` (train → generate → evaluate → summarize,
   skips existing runs)
5. ✅ SmolLM2 chat template handling (`--add-empty-system` in `prepare_data.py`;
   `system_prompt=""` in `generate_outputs.py` for smollm2)

---

## §5 — TODO (future, not scheduled)

- **Dataset quality pass.** User-owned. Should precede any further training that depends
  on the dataset. Current results are a lower bound on achievable quality.
- **Human evaluation.** Peer raters score outputs on age-appropriateness (~30 outputs per
  adapter, inter-rater agreement check). Addresses the "learned stylistic imitation vs.
  genuinely age-appropriate" limitation.
- **Safety evaluation.** Guard model (e.g. Llama Guard) or trained classifier. Most useful
  once deployment configuration is locked in.
- **Layer sweep at fixed rank.** `rank=4`, `num_layers ∈ {4, 8, 16}`, Llama 1B/3B, 2 seeds.
  Quantifies the independent `num_layers` contribution (see §1 optional depth above).
