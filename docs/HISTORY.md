# Project History

A chronological log of what was actually done on this project, in the order it happened.
This is the "what happened and when" record — for *why* the current hyperparameters/settings
are what they are, see `../CLAUDE.md`; for the detailed design/results of each experiment, see
`METHODOLOGY.md` and `EXPERIMENTS.md`; for the paper's own review/fix history, see
`../paper/AISSH_Springer/REVIEW_TODO.md`. Dates are drawn from git history and the dated notes
inside those files.

---

## 2026-03 — Project start, first adapters

- **2026-03-12.** Project created from a proof-of-concept repository. Source train/validation
  JSONL data added under `data/source/`.
- **2026-03-20.** Hyperparameter choices documented and justified (the basis of CLAUDE.md's
  "Hyperparameters & Inference Settings" section).
- **2026-03-25.** First adapters trained: the **Standard** configuration (rank 8, 16 layers)
  and, on the `fast-bear` branch, a **Fast** configuration (rank 4, 8 layers) — the two-way
  ablation that the whole project is built around. Merged 2026-04-16 (PR #1, "Fast bear").

## 2026-04 — Evaluation pipeline, dataset provenance, paper skeleton

- **2026-04-16.** Evaluation code (`src/evaluate.py`) updated; readability/latency/classifier
  metrics established. `docs/dataset_creation_prompts.md` added, documenting the exact prompts
  used to synthetically generate the training data from the *Children's Hospital Patient and
  Family Guide* (`childrens_hospital_patient_and_family_guide_-_printable_pdf.pdf`).
- **2026-04-18.** Documentation and roadmap updated for next steps; `paper/Paper.tex` added as
  the project's running numbers/write-up source of truth.

## 2026-05 — Cross-architecture sweep, dataset quality pass, mechanism identified

- **2026-05-04.** Began testing Qwen2-0.5B-Instruct as an alternative base model; `mlx`/`mlx-lm`
  updated.
- **2026-05-06.** Rank ablation and Standard-adapter perplexity tests run. SmolLM2 360M
  cross-architecture evaluation and the first rank sweep (fixed `num_layers=8`, ranks
  {2,4,8,16}, 4 architectures, 2 seeds) completed and merged (PR #2, "qwen" branch). **Finding:**
  rank — not layer depth — is the dominant variable behind the Standard/Fast crossover, via
  capacity regularization (see `METHODOLOGY.md` Phase 3).
- **2026-05-07.** **Dataset quality pass**: independent validation set (100 new examples
  replacing the circular original set), 73 new non-interrogative/atypical training examples,
  and a new `edge_cases` category (50 examples) added — training data grew from 1,000 to 1,123
  examples across six categories. Same day: Qwen 2.5 family sweep (0.5B/1.5B/3B, Standard +
  Fast) and the layer sweep (fixed rank=4, `num_layers` ∈ {4,8,16}) both completed, confirming
  depth as a secondary independent contributor. Paper updated with all of the above.
- **2026-05-08.** `METHODOLOGY.md` (phase-by-phase experiment log) and
  `small-bear-for-dummies.md` (plain-language walkthrough) written.
- **2026-05-18.** AISSH-26 workshop abstract submitted (`paper/AISSH_Springer/abstract_AISSH.tex`)
  and accepted — this later becomes the seed for the full Springer Nature manuscript expansion.
- **2026-05-27 → 2026-06-29.** A colleague (Kelsey) conducted a manual, critical pass over the
  post-quality-pass training data (`data/source/train/*.jsonl`), flagging tone and factual
  issues — including that "Dr. Beary Good" should read "Dr. Beary Goode." Not all findings were
  acted on in the dataset itself (retraining wasn't repeated for a naming fix); the "Goode"
  correction was instead made only in the paper text. The raw review notes and the resulting
  improvement plan were removed from `docs/` on 2026-08-04 as superseded process artifacts (see
  the Repo Cleanup entry below).
- **2026-05-29.** Poster/presentation example outputs written up (`docs/POSTER_EXAMPLES.md`).

## 2026-06 — Wiley/AECAI-PRiSM manuscript begins

- **2026-06-29.** Wiley Optimal Design LaTeX template dropped into
  `paper/WileyDesign/Optimal-Design-layout/` for the AECAI-PRiSM 2026 submission (deadline
  2026-07-16).

## 2026-07 (first half) — AECAI-PRiSM submission completed

- **2026-07-03 → 2026-07-16.** The Wiley manuscript was built out: paper content ported in,
  bibliography filled out, an alternate AECAI template evaluated then dropped, appendix
  (architecture figure + sample outputs) added, several formatting/proofreading passes, and the
  abstract edited. Unused template files deleted along the way. **Submitted to AECAI-PRiSM 2026
  on the 2026-07-16 deadline** as `Optimal-Design-layout.tex` — LoRA-crossover work only, no
  guard-bear.

## 2026-07 (second half) — AISSH/Springer expansion, the reproducibility crisis, guard-bear

- **2026-07-21.** AISSH-26 invited an expansion of the accepted workshop abstract into a full
  Springer Nature manuscript (`sn-jnl` class), deadline 2026-07-30 (`SPRINGER_PLAN.md`). Unlike
  the Wiley paper, this version was planned from the start to include **guard-bear** — a
  sibling-repo (`../guard-bear/`) input-safety classifier — as a full second contribution
  alongside the LoRA crossover.
- **2026-07-21 → 2026-07-22.** `springer-nature.tex` template dropped in; first full draft
  (`aissh_springer_manuscript.tex`, ~20pp) written, merging the Wiley prose with a new
  guard-bear System Architecture/Results section. **Pessimistic-review Round 1** (score 4/10):
  added a Related Work section (with a real literature search), disclosed the single-seed
  framing of the crossover claims, added proxy-metric and weak-baseline caveats.
- **2026-07-22 (later same day).** **Round 2 review — the FATAL discovery.** A routine
  rank-sweep rerun of the nominally-identical Fast-1B configuration produced 65% FK≤7.0 instead
  of the original 82% — a 17-point swing with nothing changed. This single finding triggered
  the entire investigation below. Also fixed this round: a latency-claim contradiction, a
  classifier-accuracy overlap caveat, and a sharper circularity disclosure.
- **2026-07-27.** **Round 3 — version-confound test.** Ruled out an `mlx`/`mlx-lm` version bump
  as the cause (old-version reruns swung even further). Root cause: GPU/Metal floating-point
  non-determinism, present in both training and inference. Given noise larger than the claimed
  effect, ran a **110-run multi-seed campaign** (Standard/Fast × 1B/3B, up to 30 seeds each).
  **Result: the crossover is real** — 1B: t=6.40, p=6.0×10⁻⁸; 3B: t=3.42, p=0.0011 (naive).
- **2026-07-27 (continued).** **Round 4** — a sharper reviewer question ("why do all four
  original numbers sit 3+ SD above the campaign's own means?") led to the real explanation:
  the original ablation and the rank sweep used an *older dataset vintage* than the seed
  campaign (pre- vs. post- the 2026-05-07 quality pass), not primarily training instability.
- **2026-07-28.** **Round 5 — full vintage audit.** Found the vintage-mixing was broader than
  Round 4 disclosed: the rank sweep (32 runs), the full layer sweep (12 runs), and the initial
  cross-architecture results (16 runs) all predated the quality pass. Resolved by retraining 40
  additional runs across five batches on a consistent current vintage: `sweeps_v2`,
  `crossarch_v2`, `layer_sweep_v2`, `qwen25_v2`, and new `role_parity_v2` runs for `age_12_18`.
  On retraining, the crossover itself replicated, perplexity was found *not* to track the FK
  crossover, and the rank sweep's clean "small-model regime" story for Llama 1B/Qwen 0.5B
  specifically did not replicate (walked back from confirmed to suggestive). Also this day:
  James' earlier simplified AISSH template moved into `paper/Archive/`, a narrative-restructured
  manuscript draft written (reframing guard-bear's safety-transfer finding — the off-the-shelf
  Prompt-Guard-86M baseline scored a below-chance 0.466 ROC-AUC on this pediatric-specific task —
  as the lead finding, ahead of the LoRA crossover), and `.gitignore` cleaned up to exclude
  `.venv*` variants and reproducible analysis outputs.
- **2026-07-28 (continued).** **Round 6 — page-budget fix.** Manuscript had grown to 15 pages;
  cut back to 12 pages of body content (removed a placeholder architecture figure, condensed
  prose throughout). **Round 6b** — a fact-check of two new statistical fixes: (1) a
  **peeking correction**, since the 3B seed-campaign batch was extended from n=15 to n=30 after
  an interim look (p=0.0011 naive → **p=0.0015** via a pre-specified combination test, reported
  as the new headline number); (2) a **length-confound check** across all 5,500 seed-campaign
  responses, finding the 1B-side crossover is a genuine length-independent register effect
  (p=3×10⁻⁹) while the 3B-side is substantially a response-length effect (p=0.055, marginal
  once length is controlled for).
- **2026-07-29.** `aissh_final.tex` finalized — official `sn-jnl-official.cls` (replacing the
  earlier GitHub-mirror `sn-jnl.cls`), BibTeX bibliography (`aissh_final.bib`), real author
  names/emails filled in (de-anonymized, no longer double-blind). This became, and remains, the
  actively maintained AISSH-26 manuscript.
- **2026-07-31.** Further paper updates on `aissh_final.tex`.

## 2026-08 — Repo cleanup and documentation reconciliation

- **2026-08-04.** Housekeeping pass across the whole repo:
  - Removed the superseded AISSH draft chain (`aissh_springer_manuscript.tex/pdf`,
    `aissh_springer_manuscript_12pg.tex/pdf`, the unused `springer-nature.tex` template
    scaffold, and the old mirrored `sn-jnl.cls`/`sn-mathphys.bst` only those drafts needed) —
    `aissh_final.tex` was confirmed self-contained and unaffected.
  - Removed superseded dataset-review docs (`KelseyDatasetReview.md`, `dataset_improvement_plan.md`
    — both fully executed/subsumed by the 2026-05-07 quality pass and later paper text fixes),
    an empty `docs/notes.md`, and assorted orphaned build artifacts / OS junk / `__pycache__`.
  - Updated `CLAUDE.md`, `README.md`, `EXPERIMENTS.md`, `METHODOLOGY.md`, and
    `small-bear-for-dummies.md` to fix documentation that had gone stale relative to the actual
    project state: none of the first three previously mentioned guard-bear at all; `EXPERIMENTS.md`
    contradicted itself (§1 called the rank sweep's small-model-regime finding fully resolved,
    §6.4 later walked part of it back); and the forward-roadmap items still listed "safety
    eval" and a "dataset quality pass" as outstanding work when guard-bear was already built and
    the pass was already done.
  - This file created to consolidate the log above.
