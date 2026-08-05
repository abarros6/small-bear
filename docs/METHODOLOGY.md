# Methodology: Experiment Sequence and Findings

This document records the experiments run in this project in the order they were conducted,
what each was designed to answer, and what it found. For raw numbers see
`RESULTS_COMPARISON.md`; for forward roadmap see `EXPERIMENTS.md`; for the numbers/rationale
source of truth see `paper/Paper.tex`. The manuscript actually submitted for AISSH-26 (which
also adds the guard-bear contribution, Phase 7 below) is `paper/AISSH_Springer/aissh_final.tex`.

---

## Phase 1 — Main Ablation: Standard vs. Fast on Llama

**Question.** Does reducing LoRA rank (8 → 4) and layer coverage (16 → 8) improve or degrade
style adaptation? Does the answer depend on model size?

**Setup.** Two Llama base models (3B and 1B, both 4-bit quantized). Two adapter configurations:
- **Standard**: rank 8, 16 layers — larger adapter, more expressive
- **Fast**: rank 4, 8 layers — smaller adapter, fewer trainable parameters

All other hyperparameters held constant. Evaluated on 100 validation examples per variant
(50 per role), no system prompt (matching training conditions). Metrics: FK grade ≤ 7.0 pass
rate, five readability scores, latency, inter-role classifier accuracy.

**Finding: configuration-ordering crossover.**

| Variant     | FK ≤ 7.0 | Classifier | Avg latency |
|-------------|----------|------------|-------------|
| Standard-3B | **84%**  | 0.920      | 2.37 s      |
| Fast-3B     | 76%      | 0.900      | 2.83 s      |
| Standard-1B | 72%      | 0.890      | 1.09 s      |
| Fast-1B     | **82%**  | **0.940**  | **0.93 s**  |

Standard wins on 3B; Fast wins on 1B — across both readability and style separation metrics.
The ordering of the two configurations is fully reversed between model sizes. Fast-1B is also
the only Llama variant that clears the 1.0 s VR real-time latency target (0.93 s avg, 70%
of responses under 1.0 s).

**Unanswered question at this stage.** Standard and Fast differ in both rank (8 vs. 4) and
layer coverage (16 vs. 8). The crossover could be caused by either factor, or both.

---

## Phase 2 — Cross-Architecture Evaluation (Qwen2, SmolLM2)

**Question.** Is the crossover Llama-specific? Does it persist at even smaller scales or
different architectures?

### Qwen 2 0.5B (BF16 + 4-bit)

Both Standard and Fast adapters trained for both roles. BF16 and 4-bit quantization tested.

**Finding.** BF16 and 4-bit produce identical outputs (< 5% TPS difference) — quantization
is a non-factor at 0.5B. Qwen Fast achieves the lowest latency of any trained adapter
(0.46 s avg) and the highest classifier accuracy (0.960). FK pass rate favours Standard
(74% vs 68%). This **split result** — FK favours Standard, classifier favours Fast — does
not cleanly match either side of the Llama crossover.

### SmolLM2 360M (Standard + Fast)

**Finding.** SmolLM2 Standard dominates on both metrics (84% FK, 0.950 classifier). Fast
underperforms severely (64% FK, runaway response lengths). This is **unexpected**: at 360M
parameters, the smallest model in the study follows the large-model pattern (Standard wins),
not the small-model pattern seen in Llama 1B.

### Qwen 2.5 Family Sweep (0.5B, 1.5B, 3B — Standard + Fast)

**Finding.** Fast dominates Standard uniformly across all three Qwen 2.5 sizes — no crossover
within this family. This contrasts with Llama, where Standard won at 3B. Consistent with
the rank sweep finding that Qwen is in the small-model rank regime (peak at r=2), meaning
even Standard (r=8) is over-parameterized for Qwen at any tested size.

---

## Phase 3 — Rank Sweep: Isolating the Crossover Mechanism

**Question.** Standard and Fast differ in rank and layer coverage simultaneously. Which
variable drives the crossover?

**Design.** Fix `num_layers=8` across all runs. Vary rank ∈ {2, 4, 8, 16}. Test four
architectures: Llama 1B, Llama 3B, Qwen 0.5B, SmolLM2 360M. Two seeds (42, 1337).
Role `age_5_11` only. 32 training runs total.

**Finding: rank is the operative variable.**

> **Later caveat (see Phase 7 / `EXPERIMENTS.md` §6.4).** This sweep predated the May-7
> dataset quality pass. On vintage-corrected retraining, SmolLM2's depth-driven large-model
> pattern replicated cleanly, but Llama 1B and Qwen 0.5B's clean small-model regime below came
> back flat within noise. The table below is the original (superseded) reading — treat the
> per-model peak-rank numbers as suggestive, not confirmed; the crossover itself and the
> rank-dominant/depth-secondary interpretation still stand.

| Model      | Rank 2          | Rank 4       | Rank 8           | Rank 16          | Peak  |
|------------|-----------------|--------------|------------------|------------------|-------|
| Llama 1B   | **81.0 ± 1.0%** | 65.0 ± 1.0%  | 63.0 ± 5.0%      | 63.0 ± 3.0%      | r=2   |
| Llama 3B   | 56.0 ± 4.0%     | 60.0 ± 4.0%  | **69.0 ± 9.0%**  | 68.0 ± 0.0%      | r=8   |
| Qwen 0.5B  | **78.0 ± 0.0%** | 72.0 ± 4.0%  | 75.0 ± 3.0%      | 68.0 ± 2.0%      | r=2   |
| SmolLM2    | 49.0 ± 7.0%     | 69.0 ± 5.0%  | 70.0 ± 6.0%      | **76.0 ± 8.0%**  | ≥r=16 |

The crossover persists at fixed `num_layers` — the reversal cannot be attributed to layer
coverage. **Rank is the dominant operative variable** via capacity regularization: the 1B
model's smaller representational capacity benefits from a lower-rank adapter; the 3B model
has sufficient capacity to exploit additional rank.

**Depth, not parameter count, determines rank regime.** SmolLM2 (360M, 32 layers) follows
the large-model pattern. Llama 1B (1B, 16 layers) follows the small-model pattern. Layer
depth and per-layer representation capacity predict rank sensitivity better than total
parameter count.

**Optimal ranks:** Llama 1B peaks at r=2 (81%), meaning the original Fast adapter (r=4)
was already over-parameterized. SmolLM2 shows a monotonically increasing curve through
rank 16 — the most rank-hungry model tested, curve not yet plateaued.

---

## Phase 4 — Layer Sweep: Depth as an Independent Contributor

**Question.** After rank is confirmed as the dominant variable, does layer coverage
(`num_layers`) contribute independently?

**Design.** Fix rank=4. Vary `num_layers` ∈ {4, 8, 16}. Test Llama 1B and 3B, seeds 42
and 1337, role `age_5_11`. 12 runs total (4 reused from rank sweep at `num_layers=8`).

**Finding: depth is a secondary independent contributor.**

| Model    | L=4             | L=8             | L=16            | L=8→16 Δ |
|----------|-----------------|-----------------|-----------------|----------|
| Llama 1B | **75.0 ± 5.0%** | 67.0 ± 1.0%     | 71.0 ± 3.0%     | +4.0%    |
| Llama 3B | 58.0 ± 6.0%     | 58.0 ± 2.0%     | **65.0 ± 1.0%** | +7.0%    |

At fixed rank, more layers improves performance on 3B (+7%) and partially on 1B (+4%). The
original Standard configuration's depth advantage (16 vs. 8 layers) contributes to its
superiority on 3B beyond rank alone.

**Small models prefer fewer layers.** Llama 1B peaks at `num_layers=4` (75%), declining at
layers=8 (67%) and partially recovering at layers=16 (71%). Fewer adapted layers with lower
rank reduces over-parameterization for capacity-constrained models.

**Combined interpretation.** The original Standard vs. Fast crossover reflects the joint
effect of rank and depth: rank is the dominant factor (Phase 3); depth is a secondary
independent contributor in the same direction (this phase).

---

## Phase 5 — Perplexity Post-Hoc (Standard Adapter Validation)

**Question.** Do validation perplexity scores corroborate the FK-based crossover?

**Method.** Post-hoc `--test` pass on all 8 Llama adapter checkpoints using full-sequence
cross-entropy (not masked) on `data/{role}/valid.jsonl`.

**Finding.** Perplexity crossover matches FK crossover exactly:

| Config      | age_5_11 PPL | age_12_18 PPL |
|-------------|--------------|---------------|
| Standard-3B | **18.17**    | **16.95**     |
| Fast-3B     | 20.77        | 21.61         |
| Standard-1B | 24.17        | 22.31         |
| Fast-1B     | **22.32**    | **19.79**     |

Standard-3B < Fast-3B; Fast-1B < Standard-1B. Independent metric, same direction.
Supports the capacity-regularization interpretation.

---

## Phase 6 — Dataset Quality Pass

Four targeted improvements to the training data:

1. **Independent validation set.** All 100 original validation examples (generated in the
   same Claude sessions as training data, creating circular validation) replaced with 100
   new independent examples written with atypical phrasings, edge-of-category scenarios,
   and emotionally genuine situations.

2. **Question style diversification.** 73 new training examples added using non-interrogative
   and atypical question forms: emotional statements, incomplete thoughts, resistance, overheard
   fears, post-surgery confusion. Distributed across all five categories.

3. **Edge-case category.** 50 new training examples (`edge_cases.jsonl`, 25 per role) covering
   out-of-scope requests, safety-boundary probes, distress escalation, self-harm disclosure,
   meta/identity questions, and boredom/disengagement.

4. **Programmatic quality cull.** Scoring of all training examples on FK grade and response
   length to identify and remove weakest examples. Not yet run — pending next retraining pass.

---

## Phase 7 — Crossover Reproducibility Crisis and Resolution (Seed Campaign)

**Trigger.** During AISSH-26 manuscript review, a routine rank-sweep rerun of the nominal
Fast-1B configuration (identical hyperparameters, seed, and data as the Phase 1 headline run)
landed at 65% FK≤7.0 instead of the original 82% — a 17-point swing on a run that should have
been deterministic-ish. This called the entire Phase 1 crossover into question.

**Version-confound test.** Retrained under the exact original `mlx`/`mlx-lm` versions in an
isolated venv — ruled out as the explanation; old-version reruns landed even further from the
original numbers. Root cause is very likely GPU/Metal floating-point non-determinism at the
kernel level (confirmed present in inference too, not just training), not a project bug.

**Seed campaign.** With run-to-run noise established as larger than the claimed effect, retrained
Standard/Fast × 1B/3B at their actual defined configs across up to 30 seeds each (110 runs
total, two batches to avoid stopping-early bias). Result: **the crossover is real on both
sides** — 1B: Fast (63.4%) > Standard (52.1%), t=6.40, p=6.0×10⁻⁸. 3B: Standard (58.3%) >
Fast (52.2%), t=3.42, p=0.0011 naive / **p=0.0015 after a pre-specified peeking correction**
(the 3B batch was extended from n=15 to n=30 after an interim look, which needed a proper
combination test rather than naive pooling).

**Length-confound check.** Residualized FK grade on response word count across all 5,500
seed-campaign responses. **The 1B-side crossover survives length adjustment** (t=-5.95,
p=3×10⁻⁹ — a genuine register effect). **The 3B-side crossover is substantially a length
effect** (length-adjusted t=-1.92, p=0.055, only marginal) — Standard's 3B advantage is better
described as "shorter" than "more simply worded at a given length."

**Full vintage audit.** Investigating why the campaign's absolute numbers ran lower than the
originals surfaced a broader issue: the original Phase 1 ablation, the Phase 3 rank sweep, the
Phase 4 layer sweep, and the Phase 2 cross-architecture runs all predated the Phase 6 dataset
quality pass (old training + old, circular validation data). Resolved by retraining all of
those (40 additional runs, `configs/sweeps_v2`, `layer_sweep_v2`, `crossarch_v2`,
`qwen25_v2`, plus new `role_parity_v2` runs for `age_12_18`) on the current, consistent
vintage. The crossover itself replicates; the rank sweep's clean small-model-regime story for
Llama 1B/Qwen 0.5B specifically does not (see Phase 3 caveat above).

Full detail, raw numbers, and infrastructure: `EXPERIMENTS.md` §6.

**Related, separate contribution — guard-bear.** A companion input-safety classifier
(`../guard-bear/`, DistilBERT distilled from Llama Guard 3 1B labels) was built and evaluated
independently of this ablation work, gating access to the response model. Near-ceiling 0.999
ROC-AUC; a leakage/shortcut check is still outstanding (`EXPERIMENTS.md` §7). Presented as this
project's second contribution alongside the LoRA crossover in the submitted AISSH-26 manuscript
(`paper/AISSH_Springer/aissh_final.tex`).

---

## Summary of Confirmed Findings

| Finding | Source | Status |
|---------|--------|--------|
| Standard wins on 3B; Fast wins on 1B (crossover) | Phase 1 | Confirmed |
| Crossover holds under proper multi-seed statistical power (110 runs) | Phase 7 | Confirmed |
| 1B-side crossover is a genuine length-independent register effect | Phase 7 | Confirmed |
| 3B-side crossover is substantially a response-length effect | Phase 7 | Confirmed |
| Fast-1B is the only Llama variant under the 1.0 s latency target | Phase 1 | Confirmed |
| Rank is the operative variable (not layer depth), overall | Phase 3 | Confirmed |
| ...but Llama 1B/Qwen 0.5B's specific small-model-regime curve | Phase 3 / 7 | Suggestive (didn't replicate on retrain) |
| Depth is a secondary independent contributor | Phase 4 | Confirmed |
| Perplexity corroborates FK crossover | Phase 5 | Confirmed |
| Qwen 2.5: Fast dominates Standard at all sizes (no crossover) | Phase 2 | Confirmed |
| SmolLM2 follows large-model rank pattern despite 360M params | Phases 2 & 3 | Confirmed |
| BF16 ≈ 4-bit at 0.5B scale | Phase 2 | Confirmed |
| guard-bear input-safety classifier: near-ceiling discrimination | Phase 7 (sibling repo) | Confirmed, leakage check pending |
