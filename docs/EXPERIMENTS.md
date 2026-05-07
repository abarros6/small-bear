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

### Layer sweep (num_layers at fixed rank=4) — COMPLETE

**Design:** Fixed `rank=4`, `num_layers ∈ {4, 8, 16}`, Llama 1B and 3B, seeds 42 and 1337,
role `age_5_11`. 12 runs total (4 reusing rank sweep adapters at `num_layers=8`, no extra training).

**Infrastructure:** `scripts/gen_layer_sweep_configs.py`, `scripts/run_layer_sweep.sh`,
`scripts/summarize_layer_sweep.py`

**Results:** `results/layer_sweep/summary.md`

| Model | L=4 FK% | L=8 FK% | L=16 FK% | L=8→16 Δ |
|-------|---------|---------|----------|----------|
| Llama 1B | 75.0 ± 5.0% | 67.0 ± 1.0% | 71.0 ± 3.0% | +4.0% |
| Llama 3B | 58.0 ± 6.0% | 58.0 ± 2.0% | 65.0 ± 1.0% | +7.0% |

**Key findings:**
- `num_layers` is an independent contributor to the crossover: at fixed rank=4, layers=16
  beats layers=8 by +4% (1B) and +7% (3B). The Standard configuration's depth advantage
  (16 vs. 8 layers) contributes to its superiority on 3B beyond rank alone.
- Small models prefer fewer layers: on 1B, peak FK is at `num_layers=4` (75%), declining
  at layers=8 (67%) and recovering partially at layers=16 (71%). Adapting fewer layers with
  lower rank reduces over-parameterization for capacity-constrained models.
- Latency constraint: 1B layers=16 averages 1.07s, exceeding the 1.0s real-time target.
  Layers=4 (0.92s) and layers=8 (0.93s) remain within target.
- Combined interpretation: the original crossover reflects the joint effect of rank and depth.
  Rank is the dominant factor (confirmed by rank sweep); depth is a secondary independent
  contributor in the same direction.

---

## §2 — **COMPLETE** — Alternative Model Family + Smaller Scales

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

### Qwen 2.5 family sweep — COMPLETE

2 configs × 3 models × 2 roles = 12 runs. `scripts/run_qwen25.sh`.

**Results:** `results/qwen25_*_eval.txt`

| Variant | FK ≤ 7.0 | Avg latency | Classifier acc. |
|---------|----------|-------------|-----------------|
| Qwen2.5-0.5B Fast | 76% | **0.46s** | 0.950 |
| Qwen2.5-0.5B Standard | 72% | 0.57s | 0.940 |
| Qwen2.5-1.5B Fast | 70% | 0.98s | **0.980** |
| Qwen2.5-1.5B Standard | 48% | 1.31s | 0.890 |
| Qwen2.5-3B Fast | 76% | 1.89s | 0.970 |
| Qwen2.5-3B Standard | 58% | 2.23s | 0.930 |

**Key finding:** Fast dominates Standard on **all three Qwen 2.5 sizes** (no crossover). This
contrasts with the original Llama results where Standard won on 3B and Fast won on 1B. The
Fast-wins-uniformly pattern on Qwen 2.5 suggests the crossover may be family-specific, not a
universal size effect. Consistent with the rank-sweep finding that Qwen is in the small-model
regime (peak at r=2) — Standard (r=8) is over-parameterized across the full Qwen 2.5 capacity
ladder.

**Latency:** Qwen 2.5 tokens/sec degrades steeply with model size (177 → 75 → 44 tok/s).
The 1.5B and 3B variants miss the 1.0s real-time target on most samples despite fewer LoRA
layers under Fast config. Only 0.5B Fast reliably meets the latency target (50/50 under 1.0s).

**Deployment recommendation within Qwen 2.5:** 0.5B Fast — tied for best FK pass (76%),
fastest latency (0.46s), strong classifier (0.950). The 1.5B Fast achieves the best classifier
of any trained adapter (0.980) but is borderline on latency (26/50 under 1.0s).

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

## §5 — Dataset Quality Pass — **COMPLETE**

Four improvement areas addressed. Dataset rebuilt and `prepare_data.py` re-run.

### Area 1 — Independent validation set — DONE

All 100 original validation examples (generated in the same Claude sessions as training data,
creating circular validation) replaced with 100 new independent examples written with different
prompting: atypical phrasings, edge-of-category scenarios, emotionally genuine situations.
10 per category × role bucket. Files: `data/source/validate/`.

### Area 2 — Question style diversification — DONE

73 new training examples added across all five categories using non-interrogative and atypical
question forms: emotional statements (`"I don't want to be here"`), incomplete thoughts
(`"What if the nurse... I don't know, what if she hurts me?"`), resistance, overheard fears,
post-surgery confusion. Distributed to existing category files in `data/source/train/`.

### Area 3 — Adversarial / edge-case examples — DONE

50 new training examples (`data/source/train/edge_cases.jsonl`, 25 per role) covering six
out-of-distribution types:
- **Out-of-scope requests** — "Can you call my mom?", "Can you contact my school?"
- **Safety-boundary probes** — "Do I have cancer?", "Can I increase my own pain medication dose?"
- **Distress escalation** — "I can't breathe properly", "My chest feels tight"
- **Self-harm disclosure** — "I had thoughts of hurting myself last night"
- **Meta/identity questions** — "Are you a real person?", "Who made you?"
- **Boredom/disengagement** — "I'm bored", "Can you play a game with me?"

Responses redirect appropriately, never diagnose, never pretend to be human. Category field
is `"edge_cases"` — these do not pollute the five named categories.

### Area 4 — Quality cull — TODO

Programmatic scoring of all training examples on FK grade and response length to identify
and remove weakest examples (targets: FK > 9.0 for 5-11 role, response < 30 words, formulaic
openers). Not yet run — should precede next retraining run.

### Updated dataset totals

| File | Examples |
|------|----------|
| `train/edge_cases.jsonl` | 50 |
| `train/emotional_reassurance.jsonl` | 225 |
| `train/faqs_general_curiosity.jsonl` | 213 |
| `train/hospital_rules_and_routines.jsonl` | 212 |
| `train/what_to_expect.jsonl` | 218 |
| `train/who_are_these_people.jsonl` | 205 |
| **Total train** | **1123** |
| `validate/` (5 files) | 100 (20 each) |

After `prepare_data.py`: age_5_11 → 562 train / 50 valid; age_12_18 → 561 train / 50 valid.

---

## §6 — TODO (future, not scheduled)

- **Dataset quality cull (Area 4).** Score all training examples on FK grade and response
  length, flag weak candidates for removal before next retraining run. See §5 above.
- **Human evaluation.** Peer raters score outputs on age-appropriateness (~30 outputs per
  adapter, inter-rater agreement check). Addresses the "learned stylistic imitation vs.
  genuinely age-appropriate" limitation.
- **Safety evaluation / guard model.** Blocking inline classifier (DistilBERT distilled from
  Llama Guard 3 1B labels) placed before adapter response is shown. Planned architecture
  confirmed: Option A (tiny fine-tuned classifier), ~66M params, ~30ms inference.
