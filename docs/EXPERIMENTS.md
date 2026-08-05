# Forward Experiments Roadmap

This file is the source of truth for follow-up work after the paper (`../paper/Paper.tex`).
Sections are ordered by priority. Each entry includes a run count and a rough wall-clock
estimate so compute cost is visible at a glance.

For project context, hardware constraints, and the Critical Lessons that constrain training
choices, see `../CLAUDE.md`. For full results, methodology, and the limitations that motivate
this roadmap, see `../paper/Paper.tex` §§5–6.

---

## §1 — **COMPLETE** — Rank Sweep: Crossover Mechanism Identification

> **Later caveat (see §6.4).** This sweep's *own* vintage was later found to predate the
> May-7 dataset quality pass. On vintage-corrected retraining (`sweeps_v2`), the "rank is
> dominant" conclusion below still holds for the crossover overall, but the clean small-model
> regime story for Llama 1B and Qwen 0.5B specifically did **not** replicate — it came back
> flat within noise. Read the rank values below as the original (superseded) single/two-seed
> read; §6.4 has the current-vintage numbers and the walked-back interpretation.

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

## §6 — **COMPLETE** — Crossover Reproducibility Crisis and Resolution (Seed Campaign)

**Context.** During Springer/AISSH-26 manuscript review (three rounds of adversarial
self-review, see `paper/AISSH_Springer/REVIEW_TODO.md`), a routine check re-ran the nominal
Fast-1B configuration (`r=4`, `num_layers=8`, seed=42, identical data) as part of the §1 rank
sweep. It produced FK≤7.0 = 65% instead of the original single run's 82% — a 17-point swing
on a configuration that was supposed to be identical in every controlled variable. This called
the entire Standard-vs-Fast crossover (the paper's central empirical claim) into question: the
original 8-run ablation was single-seed, and if identical reruns swing by double digits, the
6–12 point crossover gaps originally reported could plausibly be noise, not signal.

### §6.1 — Version-confound test — COMPLETE (confound ruled out)

**Question.** Is the swing explained by an undisclosed `mlx`/`mlx-lm` version change between
the original training (2026-03-25, `mlx==0.30.6`/`mlx-lm==0.30.7`) and the rank-sweep rerun
(2026-05-06, `mlx==0.31.2`/`mlx-lm==0.31.3`, bumped 2026-05-04 in commit `729d0de`)?

**Design.** Created an isolated venv (`.venv-mlx030`) pinned to the original `mlx==0.30.6`/
`mlx-lm==0.30.7`. Retrained Fast-1B and Fast-3B (`r=4`, `num_layers=8`, seed=42, identical data
— verified via `diff` against the sweep configs and via git history that `data/age_5_11/` was
untouched between the two dates) under the old versions.

**Result.** Old-version reruns landed at 58% (1B) and 62% (3B) — *further* from the original
(82%/76%) than even the new-version sweep rerun (64%/64%), not closer to it. **The version
bump is not the (sole) explanation.** Three independent attempts at one nominal configuration
now span 58–82% (1B) and 62–76% (3B) — noise larger than the effect being tested.

A quick code audit (`mlx_lm/tuner/trainer.py`, `mlx_lm/lora.py`) confirmed the seeding logic
itself is correct (`np.random.seed(seed)` before batch-order permutation, `mx.random.seed`
before training). The remaining source is very likely GPU/Metal kernel-level floating-point
non-determinism (non-associative parallel reduction order), a known category of issue for
GPU-accelerated training in general, not a coding bug in this project. A follow-up check found
this extends to *inference* too: re-generating from an unmodified, already-trained adapter
(no retraining at all) produced a different FK pass rate on a second invocation.

**Infrastructure:** `.venv-mlx030` (temporary, pinned old versions), `configs/version_check_{1b,3b}.yaml`

### §6.2 — Seed campaign — COMPLETE (crossover confirmed with real statistical power)

**Question.** Given demonstrated run-to-run variance larger than the claimed effect, is the
Standard-vs-Fast crossover (Standard wins on 3B, Fast wins on 1B) real, or noise?

**Design.** Retrained Standard and Fast at their *actual* defined configurations (Standard:
`r=8`, `num_layers=16`; Fast: `r=4`, `num_layers=8` — not the rank-sweep's one-factor-at-a-time
variants) across many seeds, role `age_5_11`, measuring FK≤7.0 pass rate per run (the paper's
primary crossover metric). Two batches to reach adequate power without stopping-early bias:
batch 1 (n=25 for 1B configs, n=15 for 3B configs, chosen from an a priori power estimate off
the version-confound test's noise), then — after batch 1 left the 3B comparison marginal
(p=0.054) — a pre-committed batch 2 doubling 3B to n=30/config, analyzed only after the full
batch completed. 110 total training runs; 4 adapters reused from the existing rank-sweep
(seed 42/1337, already trained under the current `mlx` version).

**Result:**

| Config | n | FK≤7.0 mean | SD | min–max |
|--------|---|-------------|-----|---------|
| Fast-1B | 25 | 63.4% | 6.3 | 52–78% |
| Standard-1B | 25 | 52.1% | 6.3 | 40–62% |
| Fast-3B | 30 | 52.2% | 7.0 | 42–66% |
| Standard-3B | 30 | 58.3% | 6.9 | 46–80% |

Two-sample t-tests:
- **1B: Fast > Standard, t=6.40, p=6.04×10⁻⁸.**
- **3B: Standard > Fast, t=3.42, p=0.0011.**

**Key finding: the crossover is real and reproducible on both sides**, confirmed with proper
statistical power — not an artifact of two lucky single-seed draws. The original single-run
point estimates (82%/72% for 1B; 84%/76% for 3B) were themselves toward the high end of a wide
per-config distribution (SD ≈ 6–7 points) rather than representative means; the *direction and
approximate magnitude* of the gap (11.3 points on 1B here vs. 10 originally; 6.1 points on 3B
here vs. 8 originally) held up under proper multi-seed testing even though the absolute levels
did not.

**Scope caveat.** The campaign measured FK≤7.0 pass rate only, on `age_5_11` only. It does not
re-verify the other four readability metrics, the `age_12_18` role, latency, or the inter-role
classifier at this sample size — those remain single-seed (or, for the classifier, single
5-fold-CV run) as in the original ablation. The rank/layer sweeps (§1) remain their own
2-seed experiments and are not superseded by this campaign; they answer a different question
(what does varying rank/depth in isolation do) from this campaign (is the specific
Standard-vs-Fast comparison, at their actual defined configs, statistically real).

**Infrastructure:** `scripts/gen_seed_campaign_configs.py`, `scripts/gen_seed_campaign_batch2_3b.py`,
`scripts/run_seed_campaign.sh` (resumable: skips training/generation/evaluation steps whose
outputs already exist) | **Results:** `results/seed_campaign/summary.csv`

### §6.3 — Follow-up — COMPLETE — Why the campaign's absolute numbers are lower: a dataset-vintage confound, not (mainly) non-determinism

A pessimistic-review pass on the resulting manuscript (4th round) caught something the §6.2
writeup got wrong: all four original single-seed numbers sit 3+ SD above their own
campaign-measured means *simultaneously* (Standard-3B z≈3.72, Fast-3B z≈3.40, Standard-1B
z≈3.16, Fast-1B z≈2.95) — a joint event with probability ≈4×10⁻¹⁴ if these were really just
noisy draws from the same distribution. That ruled out "high end of a wide distribution" as
the explanation and demanded a real cause.

**Checkpoint-selection hypothesis — ruled out.** Verified `adapters.safetensors` (what
`generate_outputs.py` loads) is byte-identical to the step-600 checkpoint for all four
original adapters — no post-hoc best-of-6-checkpoint cherry-picking occurred.

**The real cause: the training and validation data are not the same vintage.** The May 7
dataset quality pass (§5) did two things simultaneously that the original manuscript text
didn't flag: (1) added `edge_cases` (50 examples) and 73 diversified examples to
**training** data (1000 → 1123 examples), and (2) replaced the **validation** set with 100
new, independently-written examples. The original 8-run ablation and the §1 rank sweep
(2026-03-25 and 2026-05-06, both before 2026-05-07) used the *old* 1000-example training set
and the *old*, circular validation set. The seed campaign (2026-07-25/27) used whatever was
on disk — the *current*, expanded training set and the *current*, independently-written
validation set — without this being a deliberate choice or a disclosed one.

**Decisive test:** re-evaluated the original, unmodified Fast-1B and Standard-1B adapters
(zero retraining) on the *current* validation set:
- Fast-1B: 82% (old validation set) → **66%** (current validation set) — campaign mean 63.4%±6.3
- Standard-1B: 72% (old validation set) → **60%** (current validation set) — campaign mean 52.1%±6.3

Both land much closer to the campaign's own distribution than the original numbers did —
most of the original-vs-campaign gap is the dataset-vintage change, not training instability.

**Caveat — it's not simply "the new set is harder."** Re-evaluating the May-6 rank-sweep
adapter (new mlx version, *old* training data, never retrained) on the *current* validation
set gave 72% — *higher* than its own old-validation-set score of 64%. Validation-set choice
moves scores in both directions depending on the specific adapter, consistent with ordinary
50-example sampling variance in *which* items landed in each hand-curated set, not a uniform
difficulty gradient.

**Net effect on the §6.1/§6.2 conclusions:**
- The §6.2 crossover confirmation (t=6.40 / t=3.42) is unaffected — all 110 campaign runs
  share one consistent (current) dataset vintage, so that internal comparison was never
  confounded by this.
- The §6.1 finding that a library-version bump doesn't explain the original single-run swing
  is *weaker* than stated: that test (re-training under the old mlx version) was itself run in
  July, so it also used the current (not period-matched) validation set — an additional,
  unaccounted-for confound layered on top of the library-version test. It was never cleanly
  re-tested holding the validation set at its original vintage.
- The original §1 rank-sweep finding (82% → 64%/66%, same seed, same *old*-vintage data and
  validation set both times, differing only in mlx version and training invocation) remains a
  clean, unconfounded result and still shows genuine ~16-18pt run-to-run non-determinism
  independent of any dataset-vintage effect — smaller in magnitude than initially emphasized,
  but real.
- We did not attempt to fully decompose the relative contributions of training
  non-determinism, evaluation-set sampling variance, and the dataset revision — that would
  need a proper factorial design (old/new training data × old/new validation set × old/new
  mlx version) not run here.

**Paper fix:** manuscript's Datasets (§4.2), Results (§3.2/seed campaign), and Limitations
sections rewritten to disclose the two dataset vintages and attribute the gap correctly.

### §6.4 — Follow-up — COMPLETE — Full vintage audit: the mixing was broader than §6.3 found, now resolved

A direct question ("shouldn't all experiments use the same dataset?") prompted a full audit
of every experiment's adapter-training timestamp against the dataset files' final
modification time (2026-05-07 15:06), rather than trusting commit-bundling as a proxy for
vintage (§6.3's approach). Result: **the rank sweep (32 runs), the full layer sweep (12 runs),
and the initial Qwen 2/SmolLM2/Qwen 2.5 cross-architecture results (16 runs total) all
predated the final data update**, contradicting the manuscript text written after §6.3, which
had incorrectly asserted that only the original 8-run ablation was old-vintage.

**Retrained everything to close the gap** (40 additional training runs, ~3 batches):
- Rank sweep v2 (32 runs, `configs/sweeps_v2`, `adapters/sweeps_v2`) — current vintage
- Qwen 2 / SmolLM2 cross-arch v2 (4 runs, `configs/crossarch_v2`) — current vintage
- age_12_18 role-parity (4 runs, `configs/role_parity_v2`) — new, current vintage (the
  original ablation's age_12_18 outputs had no current-vintage equivalent at all)
- Layer sweep v2 (8 new runs + 4 reused from sweeps_v2, `configs/layer_sweep_v2`) — current
  vintage; confirmed via timestamp that ALL layer-sweep configs (including layers=16, not
  just the layers=8 reused ones) predated the data update
- Qwen 2.5 family sweep v2 (6 runs, `configs/qwen25_v2`) — current vintage; also confirmed
  to have predated the update by a full day, despite being commit-bundled with the quality
  pass in a way that initially looked like it postdated it

Base models (1B, 3B) were also re-evaluated on the current validation set (zero-shot, no
training needed) since base-model scores depend on which 50 validation prompts are asked,
not on training-data vintage.

**Key findings after full revalidation, current vintage throughout:**
- Perplexity (seed 42, current vintage): Fast-1B 30.18, Standard-1B 30.46, Fast-3B 22.91,
  Standard-3B 24.88 — perplexity does NOT track the FK-based crossover (Fast has lower PPL
  than Standard at both sizes), a genuine construct-validity finding worth flagging rather
  than smoothing over.
- Rank sweep v2: SmolLM2's depth-driven "large-model regime" (48→63% from r=2 to r=16)
  **replicates cleanly**. Llama 1B and Qwen 0.5B's original clean "small-model regime, peaks
  at r=2" story **does not replicate** — both are now flat within noise (Llama 1B: 63/59/64/62;
  Qwen 0.5B: 70/71/71/60). Llama 3B shows only a weak, noisy increase (54→62%). The paper's
  "rank is the operative variable, transformer depth determines the regime" claim is now
  presented as suggestive (SmolLM2-supported) rather than resolved across all four
  architectures, as the original single-seed sweep implied.
- Layer sweep v2: replicates well — 3B improves with depth (57→63%, +6pt, vs original +7pt);
  1B still peaks at fewest layers (69% at layers=4) though the exact shape differs from the
  original (monotonic decline vs. dip-then-recovery).
- Cross-arch v2 (Qwen2/SmolLM2 FK+latency): directions replicate (Standard beats Fast for
  both; SmolLM2 dominates). Qwen 2.5 v2: "Fast at or above Standard at every size" replicates
  (tied rather than a clear Fast win at 0.5B, clear wins at 1.5B/3B).
- **One remaining, explicitly disclosed gap:** the cross-architecture table's Classifier
  column (Qwen2/SmolLM2/Qwen2.5, all sizes) still reflects the original pre-revision vintage —
  computing it on the current vintage would require training age_12_18 counterparts for all
  10 configs, not done here. Flagged as provisional in the paper (Table~tab:crossarch caption
  and footnote) rather than silently left inconsistent.

**Paper fix:** Abstract, Introduction, Contributions, Results §3.1 (new single-seed table,
now fully current-vintage, plus new perplexity discussion), §3.2 (seed campaign, streamlined),
§3.4 (rank/layer sweep tables and prose, substantially rewritten to reflect partial
replication), §3.5 (cross-arch table and prose, with the classifier caveat), Methods §4.2
(corrected the false "only the ablation is old-vintage" claim), Discussion, Conclusion, and
Limitations (added the mechanism-claim walk-back, the perplexity finding, and a guard-bear
leakage-check caveat raised in the same review round) all rewritten. Also added a training/
eval-only leakage caveat for guard-bear's near-ceiling ROC-AUC, flagged by the same review
round but not yet independently investigated.

**Infrastructure:** `scripts/run_generic_batch.sh` (parameterized train→generate→evaluate
runner, reused across all four new v2 batches with a per-directory model-size map file) |
**Results:** `logs/sweeps_v2/`, `logs/crossarch_v2/`, `logs/role_parity_v2/`,
`logs/layer_sweep_v2/`, `logs/qwen25_v2/` (per-run eval text files; no single aggregated CSV
was built for these batches — aggregation was done ad hoc via Python one-liners during the
paper rewrite).

---

### §6.5 — Follow-up — COMPLETE — Sample-size peeking correction and length-confound check on the seed campaign

A 6th pessimistic review (after the page-budget trim, `paper/AISSH_Springer/REVIEW_TODO.md`
Round 6) flagged two further substantive issues in the seed campaign (Section 3.2 of the
paper), both fixed with real analysis rather than caveats:

**Sample-size peeking (3B side).** The 3B campaign's $n$ was raised from 15 to 30/config
after a preliminary batch left the comparison marginal ($t=2.01$, $p=0.054$); analyzing the
resulting pooled $n=30$ naively is anti-conservative because the decision to extend was
itself informed by this unblinded interim look. Fix: identified the exact seed split between
the interim batch (`scripts/gen_seed_campaign_configs.py`, `SEEDS_3B` first 15) and the
top-up batch (`scripts/gen_seed_campaign_batch2_3b.py`, 15 new seeds), then computed a
pre-specified equal-weight inverse-normal combination test (Bauer–Köhne/Lehmacher–Wassmer
style) combining the interim-stage one-sided $p$ with the fresh, independent 15-seed
replication's result ($t=2.75$, $p=0.010$, never used in the extension decision). Combined
result: one-sided $p=0.00075$ (two-sided-equivalent $p=0.0015$) — still significant, so the
3B-side crossover survives the statistically correct test, just less dramatically than the
naive pooled $p=0.0011$ the paper previously reported as its sole number. The paper now
reports the corrected $p=0.0015$ as the headline 3B figure throughout (Abstract, Contributions,
Discussion, Conclusion), with the naive number kept only in Section 3.2 for methodological
transparency. Script: `scripts/peeking_correction_analysis.py`; raw numbers in
`results/seed_campaign/peeking_correction.txt`.

**Response-length confound.** Standard and Fast differ systematically in output length
(Table 1), raising the question of whether the crossover is really a readability/register
effect or just a length effect. Fix: recomputed per-example FK grade and word count (via
`textstat`, same method as `src/evaluate.py`) for all 5,500 individual seed-campaign
responses (`scripts/length_confound_analysis.py`, output saved to
`results/seed_campaign/length_confound.txt`), then residualized FK grade on word count and
compared residuals by config. Findings: **the 1B-side crossover survives length-adjustment**
($t=-5.95$, $p=3\times10^{-9}$) — Fast's advantage is a genuine length-independent register
effect, not just being shorter (72 vs. 78 words). **The 3B-side crossover is substantially a
length effect** — the length-adjusted difference is only marginal ($t=-1.92$, $p=0.055$), and
a logistic regression of pass/fail on config + word count gives a near-zero config
coefficient once length is controlled; Standard's 3B advantage is better described as
"produces shorter responses" than "produces more simply-worded responses at a given length."
This was not tested for the rank/layer sweeps' architectures (flagged as a residual gap in
Limitations).

**Net effect:** the crossover's statistical existence is now confirmed under the
methodologically correct test (not just the anti-conservative one) on both sides, but the two
sides are understood to differ in kind — 1B is a real register effect, 3B is mostly a length
effect. This is a genuine tightening of the paper's causal story, in the same spirit as the
rank-sweep mechanism walk-back in §6.4: report what survives scrutiny, not what was originally
hoped for.

**Paper fix:** Abstract, Contributions, Results §3.2 (two new paragraphs plus corrected
p-value), Discussion, Conclusion, and Limitations all updated. Page budget was re-exceeded by
this addition (12→13 pages) and re-trimmed back to exactly 12 pages of body content via
further prose condensing (Related Work, Evaluation Framework, Discussion) — no numeric content
was cut to make room, only redundant phrasing.

## §7 — TODO (future, not scheduled)

- **Dataset quality cull (Area 4).** Score all training examples on FK grade and response
  length, flag weak candidates for removal before next retraining run. See §5 above.
- **Human evaluation.** Peer raters score outputs on age-appropriateness (~30 outputs per
  adapter, inter-rater agreement check). Addresses the "learned stylistic imitation vs.
  genuinely age-appropriate" limitation.
- ~~Safety evaluation / guard model.~~ **DONE, in a sibling repo.** This item used to describe
  a not-yet-built classifier; it now exists as **guard-bear** (`../guard-bear/`), a full
  fine-tune of `meta-llama/Prompt-Guard-86M` (DeBERTa-v2), gating access to the response model.
  It's built, trained, and evaluated (near-ceiling 0.9998 ROC-AUC post-retrain, see next
  bullet), and is presented as this project's second contribution in the submitted AISSH-26
  manuscript (`paper/AISSH_Springer/aissh_final.tex`).
- **guard-bear leakage/shortcut check — PARTIALLY RESOLVED (2026-08-04).** Exact-text
  train/val/test overlap check: an initial pass found what looked like near-total validation
  leakage (612/614), but that compared validation against the full train+val pool it was
  carved from, not the actual disjoint training set — an artifact of file organization, not
  real contamination. Reproducing the true split showed the real duplicate-text overlap was
  minor (10/614 val, 3/613 test, from ~36 exact-duplicate rows among 4,089 raw examples).
  Fixed at the root: `assemble_dataset.py` now deduplicates the full pool by exact text
  before any splitting; `guard-bear` was retrained from scratch on the corrected split
  (verified zero overlap across all three splits) and the deployment threshold re-tuned
  (0.08 → 0.94). The finding replicates, slightly more cleanly (ROC-AUC 0.9993 → 0.9998).
  A separate pre-existing bug was caught in the same pass: `pandas.read_csv`'s default NA
  parsing silently corrupted literal "null"/"NaN" gibberish-test-case text to missing values;
  fixed via `keep_default_na=False` throughout. **Still outstanding:** template-level
  paraphrase leakage (as opposed to exact-string) and lexical-shortcut checks (e.g. the
  classifier keying on a small vocabulary marker rather than genuine semantic understanding)
  remain unchecked and are flagged as such in the paper's Limitations. Details:
  `../guard-bear/results/BASELINE_COMPARISON.md`, `../guard-bear/gen-docs/EVAL.md`.
- **Cross-architecture classifier revalidation.** Table~tab:crossarch's Classifier column
  (Qwen2, SmolLM2, Qwen2.5 — 10 configs) still reflects the pre-quality-pass dataset vintage;
  revalidating requires training age_12_18 counterparts for all 10 configs (not yet done —
  see §6.4).
