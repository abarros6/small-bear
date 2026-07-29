# Springer Nature Manuscript Plan — AISSH-26 Workshop Expansion

## Context

- Invited expansion of the accepted AISSH-26 workshop abstract into a full manuscript for a
  Springer Nature book series.
- **Deadline: July 30, 2026, 11:59 PM EST** (9 days out as of 2026-07-21).
- **Submit via EasyChair**: https://easychair.org/cfp/aissh-26
- **Format**: Springer Nature `sn-jnl` LaTeX class, already dropped in as `paper/springer-nature.tex`
  (currently set to `sn-mathphys-num` — numbered reference style, single column).
- **Page budget: 6–12 pages excluding references.**

## Source material and how each feeds in

| Source | Role |
|---|---|
| `paper/abstract_AISSH.tex` | Original accepted abstract — real author block, opening framing, headline numbers to carry forward |
| `paper/WileyDesign/Optimal-Design-layout/Optimal-Design-layout.tex` | Primary prose donor — a fuller (9pp, two-column) draft written for a different, already-lapsed venue (AECAI-PRiSM). De-anonymize and reflow into `sn-jnl` |
| `paper/Paper.tex` | Source of truth for all numbers — rank sweep, layer sweep, cross-architecture (Qwen2, Qwen2.5 family, SmolLM2), perplexity crossover |
| `../guard-bear/` (README, `results/BASELINE_COMPARISON.md`, `guard_model_final/`) | New material — a second research contribution not in any existing draft |

## Decisions locked in (from our chat)

1. **Real authorship.** Restore the AISSH abstract's actual author block — Sandrine de
   Ribaupierre, Roy Eagleson, Anthony Barros, Kelsey Kloosterman, with affiliations — replacing
   the Wiley draft's double-blind "Anonymous Author 1/2" placeholders. Restore the repo link
   in the appendix (no longer a blind-review concern).
2. **Guard-bear gets a full new section**, not a passing mention — its own System Architecture
   subsection and its own Results subsection with the recall/precision/F1/ROC-AUC table and
   subcategory breakdown.
3. **Full experimental scope**, matching the Wiley draft's breadth: rank sweep, layer sweep,
   and cross-architecture validation (Qwen 2, Qwen 2.5 family, SmolLM2) all included, not
   trimmed back to the original abstract's narrower Llama-only scope.
4. **Guard-bear authorship**: solely your individual contribution. Credit all four authors on
   the manuscript as a whole, but the Author Contributions statement should attribute the
   guard-bear model specifically to you.

## Page-budget risk (flagging now, not a surprise later)

- The Wiley draft is 9 pages **two-column**. `sn-jnl` is **single-column** — the same word
  count reflows to noticeably more pages in single-column layout (fewer words fit per physical
  page despite the wider line length).
- Adding a full guard-bear section is genuinely new content, not a repackaging — expect
  +1.5–2 pages for it (architecture, dataset, results table, subcategory table, discussion).
- Naive port + addition risks landing past 12 pages before we even open the extended
  experiments section.
- **Mitigation**: keep every table and number, but condense narrative prose aggressively in
  Related Work, Methodology, and Limitations (same approach already used once when the Wiley
  draft was trimmed from `Paper.tex`). Target landing at ~11–12 pages before references, and
  treat cuts to prose (not tables/results) as the release valve if we run over.

## Proposed section outline (`sn-jnl`)

1. **Title / Author block** — real names + affiliations, corresponding author designated
2. **Abstract** — updated to introduce guard-bear as the paper's second contribution alongside
   the LoRA ablation
3. **Introduction** — merges the AISSH abstract's framing with the Wiley draft's fuller intro;
   adds a paragraph motivating input-safety gating for a pediatric-facing system
4. **Related Work** — condensed: PEFT, LLMs in clinical/health communication, VR in pediatric
   care (as before) + **new subsection**: prompt injection / input-safety classifiers for
   deployed LLM systems
5. **System Architecture** — two components: (a) dual-LoRA adapter response model, (b) **new**:
   guard-bear as an upstream input classifier gating access to the response model
6. **Dataset** — response-model dataset (6 categories, 1,123 examples) + guard-bear dataset
   (4,414 examples across 13 subcategories)
7. **Methodology** — LoRA training protocol (existing) + guard-bear fine-tuning protocol
   (Prompt-Guard-86M base, threshold tuning methodology)
8. **Results**
   - 8.1 Response model — readability, latency, inter-role separation, the crossover finding
   - 8.2 Guard-bear — recall/precision/F1/ROC-AUC vs. base Prompt-Guard-86M, confusion matrix,
     subcategory breakdown, error analysis (4 FN / 3 FP)
9. **Extended Experiments** — rank sweep, layer sweep, cross-architecture validation
   (Qwen 2, Qwen 2.5 family, SmolLM2)
10. **Discussion** — unify both contributions: config-transfer story for the response model +
    the safety-gated deployment story for guard-bear
11. **Limitations**
12. **Conclusion**
13. **Declarations** (funding, conflicts, data availability — per `sn-jnl` backmatter conventions)
14. **Appendix** — repo link(s), author contributions, dataset generation provenance

## Mechanical conversion notes (not open decisions, just things to do)

- `sn-jnl` expects BibTeX (`\bibliography{sn-bibliography}`), not the manual `thebibliography`
  used in both existing drafts — need to convert the ~11 references into a `.bib` file.
- Need a repo link decision for the appendix — restoring it means picking what's actually
  public (GitHub URL) vs. still-private; confirm before the final pass.
- Check whether `Paper.tex`'s existing figures (architecture diagram, sample outputs) need a
  new panel/diagram added for guard-bear's position in the pipeline.

## Open items to resolve while writing (flag if any need your input)

- Exact abstract wording once guard-bear numbers are folded in
- Whether the architecture diagram gets redrawn to show guard-bear's gating position, or a
  new supplementary figure is added instead
- Final reference-style check: `sn-mathphys-num` vs. `sn-mathphys-ay` — currently set to
  numbered, matching the Wiley/Paper.tex citation style already in use, so no change planned
  unless you want author-year
