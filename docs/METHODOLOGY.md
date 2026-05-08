# Methodology: Experiment Sequence and Findings

This document records the experiments run in this project in the order they were conducted,
what each was designed to answer, and what it found. For raw numbers see
`RESULTS_COMPARISON.md`; for forward roadmap see `EXPERIMENTS.md`; for canonical write-up
see `paper/Paper.tex`.

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

## Summary of Confirmed Findings

| Finding | Source | Status |
|---------|--------|--------|
| Standard wins on 3B; Fast wins on 1B (crossover) | Phase 1 | Confirmed |
| Fast-1B is the only Llama variant under the 1.0 s latency target | Phase 1 | Confirmed |
| Rank is the operative variable (not layer depth) | Phase 3 | Confirmed |
| Depth is a secondary independent contributor | Phase 4 | Confirmed |
| Transformer depth (not parameter count) predicts rank regime | Phase 3 | Confirmed |
| Perplexity corroborates FK crossover | Phase 5 | Confirmed |
| Qwen 2.5: Fast dominates Standard at all sizes (no crossover) | Phase 2 | Confirmed |
| SmolLM2 follows large-model rank pattern despite 360M params | Phases 2 & 3 | Confirmed |
| BF16 ≈ 4-bit at 0.5B scale | Phase 2 | Confirmed |
| Optimal rank for Llama 1B is r=2, not r=4 | Phase 3 | Confirmed |
