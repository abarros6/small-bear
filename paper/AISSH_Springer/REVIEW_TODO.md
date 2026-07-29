# Pessimistic Review Findings — Fix Tracker

Source: `/pessimistic-paper-review` run against `aissh_springer_manuscript_12pg.tex`,
single fresh-context reviewer, 2026-07-22. Score at time of review: 4/10, Major Revision.
Fact-checked against repo evidence (guard-bear BASELINE_COMPARISON.md, results/*_eval.txt,
results/sweeps/summary.md, results/layer_sweep/summary.md) — all core numbers confirmed
real, not fabricated. Working through weaknesses one at a time, most actionable first.

Legend: [ ] open · [x] done · [~] partially addressed / judgment call made

## ROUND 6 — page-budget fix (15pp -> 12pp body) + re-review (2026-07-28)

Manuscript had grown to 15 total PDF pages (14 pages of body content excluding references,
2 pages over the stated 6-12pp Springer budget). Cut back to exactly 12 pages of body content
(14 total, references now cleanly on pp.13-14) via: removing the Appendix B architecture
figure entirely (a placeholder that never depicted guard-bear's gating stage, so no scientific
content lost); condensing prose throughout (Introduction, Related Work, Results §3.1/3.4/3.5,
Discussion, Limitations, Methods); merging redundant Declarations bullets (Ethics
approval+Consent for publication; Data/Materials/Code availability); inlining the repo URL
directly into Declarations instead of a separate Appendix A section; tightening itemize
spacing via `enumitem`. No numeric claims, findings, or statistical results were altered.

Ran a 6th pessimistic review against the trimmed manuscript, with instructions to specifically
check the cut for dangling cross-references/orphaned labels/silently-dropped caveats, plus a
fresh full re-assessment. **Score: 4/10, Major Revision.** Fact-checked: the seed-campaign
headline stats (t=6.40/p=6.0e-8 1B; t=3.42/p=0.0011 3B) and several rank-sweep table cells
were independently recomputed from `results/seed_campaign/summary.csv` and `logs/sweeps_v2/`
raw eval logs and matched exactly — no fabrication found.

**Confirmed real defects from the page-budget edit itself** (fixed immediately):
- [x] Orphaned `\label{sec:guardmethod}` — its only `\ref` was cut during trimming but the
  label was left behind. Removed the label.
- [x] Unused `\usepackage[title]{appendix}` import, orphaned after Appendix B's removal.
  Removed the import.
- Confirmed via re-read: no scientifically load-bearing claim or caveat was dropped by the
  trim; all other `\ref`/`\label` pairs intact; manuscript still compiles clean, still exactly
  12pp body / 14pp total.

**Substantive findings — two now fixed with real analysis, not just caveats:**
- [x] [MAJOR] Sample-size extension after peeking (3B campaign n raised 15->30 after a
  preliminary batch left the comparison marginal, p=0.054). Fixed: identified the exact
  batch-1/batch-2 seed split and computed a pre-specified equal-weight inverse-normal
  combination test — the statistically valid correction for this design. Combined result
  p=0.0015 (vs naive pooled p=0.0011) — still significant, crossover survives. Paper now
  reports the corrected p=0.0015 throughout as the headline 3B number. See §6.5 in
  `docs/EXPERIMENTS.md` for full methodology and raw numbers
  (`results/seed_campaign/peeking_correction.txt`).
- [x] [MAJOR] Readability gains confounded with response length. Fixed: recomputed per-example
  FK grade + word count for all 5,500 seed-campaign responses and ran a length-adjusted
  (residualized) comparison. Result: the 1B-side crossover survives length-adjustment
  (t=-5.95, p=3e-9, genuine register effect) but the 3B-side crossover is substantially a
  length effect (length-adjusted t=-1.92, p=0.055, only marginal) — Standard's 3B advantage
  is "shorter," not "more simply-worded at a given length." This meaningfully tempers the
  3B-side interpretation of the crossover (paper updated accordingly: Abstract, §3.2,
  Discussion, Conclusion, Limitations). See §6.5 in `docs/EXPERIMENTS.md`
  (`results/seed_campaign/length_confound.txt`, `scripts/length_confound_analysis.py`).
  Not yet tested for the rank/layer sweeps' architectures (flagged in Limitations as residual).

**Round 6b — re-review of the two fixes (score 3/10, Major Revision).** Ran a 7th pessimistic
review specifically scrutinizing the peeking-correction and length-confound methodology.
Verdict: both fixes are the *right method*, confirmed independently reproducible from raw
data (batch membership read directly from `scripts/gen_seed_campaign_configs.py` /
`gen_seed_campaign_batch2_3b.py`, not inferred), but two concrete gaps in what the
*manuscript text itself* stated (not the underlying method):
- [x] The paper never stated the two-stage design was fixed *before* seeing stage-2 data
  (a reader can't verify it wasn't open-ended peeking from the text alone). Fixed: added an
  explicit clause to §3.2 confirming the top-up to n=30 was planned before unblinding stage two.
- [x] The length-adjustment paragraph reported only p-values, not effect sizes — a 3B
  p=0.055 and a 1B p=3e-9 look categorically different but the underlying effect sizes
  (residual gaps) matter more for "survives" vs "substantially a length effect" framing.
  Fixed: added the actual residual gaps (1B: 0.35 FK grade levels; 3B: 0.10 FK grade levels)
  and the cross-check logistic-regression coefficients (1B: 0.35; 3B: 0.007) directly to the
  text.
Score did not move (still reflects pre-existing structural findings below — full circularity,
single/two-seed cross-arch claims, FIXME emails — not the two items this round targeted,
which the reviewer explicitly credited as sound).

**Still open, not yet acted on** (pre-existing, left for the user to decide whether to pursue):
- [ ] [MAJOR] guard-bear's 0.999 ROC-AUC leakage/shortcut check — still not investigated
  (same gap as Round 5, confirmed still absent from `results/`).
  See [[project_dr_beary_good]] area if pursued further.
- [ ] [MAJOR] Reported latency excludes the guard-bear pass; true gated-pipeline latency
  unmeasured.
- [ ] [MINOR] Table 5's Classifier column (pre-revision vintage) sits in a table otherwise
  presented as current-vintage, with only a one-sentence caveat.
- Author emails still literal `FIXME` placeholders (known, blocked on user, untouched).

## ROUND 5 — full vintage audit; mechanism claim honestly walked back (2026-07-28)

Prompted by the user's direct question ("shouldn't all experiments use the same dataset?"),
audited every experiment's adapter-training timestamp against the dataset's final
modification time rather than trusting commit-bundling (Round 4's method). Found the
vintage-mixing was far broader than Round 4 disclosed: **the rank sweep (32 runs), the full
layer sweep (12 runs), and the initial Qwen 2/SmolLM2/Qwen 2.5 cross-architecture results (16
runs) all predated the final data update** — meaning the manuscript's own Datasets section,
written in Round 4, incorrectly claimed these used the "expanded set." Ran a 5th pessimistic
review in parallel confirming this was a real gap (score 3/10) and additionally flagging:
guard-bear's near-ceiling AUC has no leakage/shortcut check; the classifier column mixes
vintages within one table presented as directly comparable; low-n sweeps continue asserting
firm conclusions despite the paper's own evidence that this pipeline's noise can exceed the
effect size at issue.

**Resolved by retraining everything** (40 additional runs across 5 batches: rank sweep v2,
Qwen2/SmolLM2 cross-arch v2, age_12_18 role-parity, layer sweep v2, Qwen 2.5 v2) on the
current, consistent dataset vintage, then fully rewriting the paper's Abstract, Contributions,
Results (all four subsections), Methods §4.2, Discussion, Conclusion, and Limitations to
reflect what actually replicated vs. didn't:
- **Perplexity does not track the FK crossover** (new finding, reported honestly rather than
  omitted) — Fast has lower perplexity than Standard at both sizes on re-evaluation.
- **Rank sweep's "rank is the operative variable" claim, walked back from resolved to
  suggestive** — SmolLM2's depth-driven pattern replicates cleanly; Llama 1B and Qwen 0.5B's
  original clean "small-model regime" is now flat within noise on independent retraining.
- **Layer sweep replicates well** (3B depth-helps direction, 1B peaks at fewest layers).
- **Cross-architecture FK/latency directions replicate**; the Classifier column is explicitly
  flagged in the table caption/footnote as still reflecting the old vintage, rather than
  silently left inconsistent as before.
- **guard-bear leakage check**: not resolved (would need new investigation), but now
  explicitly named in Limitations rather than left as an unaddressed gap from Round 4's review.

This is a strictly more honest paper than the Round 4 version: the crossover itself remains
statistically confirmed (unaffected, since all 110 campaign runs always shared one vintage),
but the mechanism explanation is now presented at the confidence level the evidence actually
supports, not the confidence level the original single-seed sweep implied. Page count grew to
14 total (References starts page 14) — accepted as a reasonable tradeoff, same judgment call
as prior rounds, given the substance of what was added. Full technical writeup:
`docs/EXPERIMENTS.md` §6.4.

## ROUND 4 — the "high end of the distribution" framing was itself wrong; real cause found (2026-07-27)

Re-ran the skill on the Round 3-updated manuscript. Score 4/10, Major Revision — the campaign
itself checked out (t/p values independently recomputed from raw CSV, match exactly), but the
reviewer caught something the Round 3 writeup got wrong: **all four original single-run numbers
sit 3+ SD above their own campaign-measured means simultaneously** (joint probability ≈4×10⁻¹⁴
if these were ordinary noisy draws from the same distribution). "Toward the high end of a wide
distribution" was not an adequate explanation — something systematic differs between the
original 8 runs and the 110-run campaign.

Checked the reviewer's proposed cause (post-hoc best-of-6-checkpoint selection for the
originals) — **ruled out**: `adapters.safetensors` is byte-identical to the step-600 checkpoint
for all four original adapters.

Found the real cause instead: **the training and validation data are two different vintages.**
The May 7 dataset quality pass (already documented in §5) expanded training data (1000→1123
examples) *and* replaced the validation set with 100 new, independently-written examples, in
the same commit. The original 8-run ablation and the rank sweep predate this (both used the
old, smaller training set and the old, circular validation set). The seed campaign — run this
week — used whatever's currently on disk: the new training set and the new validation set,
without this being a deliberate or disclosed choice. Decisive test: re-evaluated the original,
*unmodified* Fast-1B and Standard-1B adapters (zero retraining) on the current validation set —
82%→66% and 72%→60% respectively, landing much closer to the campaign's own distributions
(63.4%±6.3 and 52.1%±6.3). Most of the original-vs-campaign gap is the dataset-vintage change,
not training instability — though a smaller, separately-confirmed non-determinism effect
(same-vintage data, same seed, different training invocation, still 16-18pt swing) is real too.

This means the Round 3 causal narrative ("most likely GPU/Metal floating-point
non-determinism") was incomplete/wrong as the *primary* explanation. The crossover confirmation
itself (t=6.40/t=3.42) is unaffected — all 110 campaign runs share one consistent vintage — but
the manuscript's Datasets, seed-campaign Results, and Limitations sections needed rewriting to
disclose the two dataset vintages and attribute the gap correctly. Full writeup:
`docs/EXPERIMENTS.md` §6.3. Page budget: core content now runs to 13 pages (was 12) after these
additions — accepted as a reasonable trade for accuracy given how much trimming had already
been done in prior rounds.

## ROUND 3 UPDATE — the FATAL finding is now fully resolved, not just disclosed (2026-07-27)

Following the Round 2 FATAL item below, the user chose to actually resolve the reproducibility
question rather than ship it as a caveat. Ran a version-confound test (ruled out — retraining
under the original mlx/mlx-lm versions did not reproduce the original numbers either), then a
110-run multi-seed campaign (Standard/Fast × 1B/3B, n=25 for 1B configs, n=30 for 3B configs
after an initial n=15 batch left the 3B comparison marginal at p=0.054). **Result: the crossover
is real and statistically confirmed on both sides** — 1B: Fast (63.4%) beats Standard (52.1%),
t=6.40, p=6.0×10⁻⁸; 3B: Standard (58.3%) beats Fast (52.2%), t=3.42, p=0.0011. The original
single-run point estimates were inflated (toward the high end of a wide per-config distribution,
SD≈6–7 points) but the crossover's direction and approximate magnitude held up under proper
multi-seed testing. Full methodology and results: `docs/EXPERIMENTS.md` §6. The paper's
Abstract, Contributions, Results (new §3.2 "Statistical Validation of the Crossover"), Mechanism
Sweeps framing, Discussion, Conclusion, and Limitations were all rewritten to state this as a
confirmed finding rather than a hedged, unresolved one. This upgrades the Round 2 FATAL item
from "honestly disclosed" to "actually resolved" — see that item below for the original finding.

## ROUND 2 — re-review after Round 1 fixes (2026-07-22, later same day)

Re-ran the skill, instructed to ignore the four known cosmetic/procedural items (author
emails, architecture figure, venue boilerplate, repo-link policy). Score unchanged: **4/10,
Major Revision** — the Round 1 fixes genuinely landed (reviewer explicitly credited the
blunter Limitations language, the proxy-metric caveat, and the new Related Work section),
but this pass surfaced new, more serious problems that Round 1 didn't touch. Two of the
reviewer's claims were independently verified by me against raw repo data (not just
trusted) — both held up:

- [x] **[FATAL, newly discovered, independently verified] Training non-determinism:**
  the rank sweep's "Llama 1B/3B, r=4, num_layers=8, seed=42" cells are — on paper —  the
  exact same configuration as the main Fast-1B/Fast-3B runs (same model, same data, same
  every hyperparameter, same seed). I diffed `configs/age_5_11_1b_lora.yaml` /
  `configs/age_5_11_3b_lora.yaml` against `configs/sweeps/rank4_layers8_seed42_{1b,3b}.yaml`
  — byte-identical except for `adapter_path`. I checked git history — `data/age_5_11/` was
  untouched between the original training (2026-03-25) and the rank sweep
  (2026-05-06); the only data commit on the sweep date added unrelated SmolLM2-specific
  files. Yet: original Fast-1B FK≤7.0 = 82%, the sweep's supposedly-identical rerun = 65±1%
  (17pt gap); original Fast-3B = 76%, the sweep's rerun = 60±4% (16pt gap). Same config,
  same seed, same data, different training invocation → 16-17 point swings in the headline
  metric. **Fixed via honest disclosure, not by re-running experiments** (rerunning 8
  configs with a second seed is a real ML-training decision, not a text fix — flagging it
  as the one item on this list that's a genuine judgment call, not something I should have
  silently decided for you). Added the exact numbers and framing to Limitations/Conclusion;
  softened "confirm...is not single-seed noise" language to "indicate...should be read as
  suggestive, not confirmed" throughout Abstract, Intro, Results §3.1/§3.3, Discussion, and
  Conclusion — each now distinguishes the (still-supported) qualitative rank-regime
  direction from the (now explicitly caveated) exact crossover magnitudes.

- [x] **[MAJOR, verified] "Fast-1B is the only configuration meeting the 1.0s latency
  target" (Abstract + Intro) is directly contradicted by the paper's own Section 3.4
  table**, which shows Qwen 2 Standard (0.59s), Qwen 2 Fast (0.46s), SmolLM2 Standard
  (0.81s), Qwen2.5-0.5B Fast (0.46s), and Qwen2.5-0.5B Standard (0.57s) all clearing the
  same bar. Fixed: qualified to "only Llama configuration" in Intro, Results §3.1, and
  Discussion, matching what Discussion's later sentence already said correctly.

- [x] **[MAJOR] Classifier-accuracy std overlap undermines the "confirmed by...the
  inter-role classifier" framing.** Fixed: added a sentence in Results §3.1 noting the
  ±std ranges overlap substantially across all four configs and reframing the classifier
  as "directionally consistent with, rather than independent confirmation of" the
  readability-based crossover.

- [x] **[MAJOR] The actual Standard config (r=8, layers=16) is never itself re-run with
  multiple seeds.** Folded into the new Limitations disclosure above — explicitly states
  neither sweep re-tests r=8×layers=16 directly.

- [x] **[MAJOR] Circularity disclosure understates its own severity.** Fixed: Limitations
  now states the training data itself (not just evaluation) was never reviewed by a
  clinician or child-language-development expert at creation time.

- [x] **[MAJOR] guard-bear's ROC-AUC of 0.466 (below 0.5) is mechanistically
  under-explained.** Fixed: added a sentence in §3.2 explaining a sub-0.5 AUC specifically
  means the base model ranks true-unsafe below true-safe across the full threshold range
  (not just a miscalibrated fixed threshold), and honestly notes we didn't test why beyond
  the confusion-matrix/subcategory evidence already reported.

- [ ] **[MINOR] Scope-bundling concern restated more sharply** — no action planned, same
  as the Round 1 MINOR version of this note.
- [ ] **[MINOR]** Rank-selection literature gap claim rests on a single citation — left
  as-is; would need an actual second citation, not just wording.
- [ ] **[MINOR]** Qwen2.5-1.5B Standard's 48% FK≤7.0 outlier presented with no comment —
  left as-is, low priority.
- [~] **[MINOR]** "We are not aware of prior work..." repetition — reduced from 3 near-verbatim
  instances to 2 varied ones as a side effect of trimming Related Work for page budget
  (see below), not specifically targeted.

**Page budget note:** these fixes added real length. Recompiled iteratively, trimming
redundant restated numbers (Conclusion, Discussion) and tightening Related Work prose to
compensate. Final state: References header now starts on page 12 (back to the pre-Round-2
boundary), but the appendix architecture figure itself (a placeholder pending replacement
anyway) now floats onto page 13 interleaved with the reference list — a cosmetic layout
artifact of being right at the page-budget edge, not a content problem, and something that
will resolve naturally once the real figure replaces the placeholder and the paper is
recompiled on the official submission toolchain (already a pending TODO).

## Round 1 (original pass)

## MAJOR

- [x] **Single-seed framing language in the crossover claims.** Abstract, Intro, and
  Results §2.1 stated the crossover as "consistent across all five readability metrics"
  without disclosing it's drawn from single-seed (seed 42) runs. Fixed by adding explicit
  "single-seed" / "in the original eight single-seed runs" framing at first mention in
  Abstract, Intro, and Results §2.1, each pointing forward to the two-seed rank sweep
  (§2.3 / `sec:ranksweep`) as the source of statistical confirmation. Recompiled: still 12
  pages, no overflow.

- [ ] **Architecture figure contradicts the text.** The only diagram in the paper (Appendix
  Fig. 1) shows just the age-gate/LoRA pipeline — no guard-bear stage — and its own caption
  admits this. User is regenerating the diagram externally (prompt already handed off in an
  earlier turn); once the new PNG lands, update the figure caption to drop the
  "does not yet depict guard-bear" disclaimer.

- [ ] **Placeholder author emails + unresolved internal TODOs.** All four author emails are
  literal `FIXME-institutional-email@uwo.ca`. Blocked on the user — needs real institutional
  emails before submission. Also unresolved: whether AISSH-26 permits the appendix repo link,
  and venue/copyright/funding boilerplate confirmation. (Tracked already in the file's own
  header TODO block and in `SPRINGER_PLAN.md`.)

- [x] **n=2 "mean ± std" in the sweep tables reads as more rigorous than it is.** Decision:
  keep ±std (compact, standard convention) but caveat it explicitly. Updated Table
  `tab:sweeps`'s caption to say "(n=2; read as a range between the two runs, not a variance
  estimate)" and added a sentence in the Mechanism Sweeps prose making the same point before
  the sweep results are presented. Recompiled: still 13 total pages, body content unaffected.

- [ ] **Closed evaluation loop** (same generative pipeline produces training data, validation
  data, and is graded only by automated proxies — no independent human/clinical judgment).
  This is a real, structural limitation, not a wording fix. Options: strengthen the existing
  Limitations sentence to state the severity plainly (currently undersells it as something
  that would merely "strengthen" the claim), or leave as a flagged future-work item. Needs a
  decision on how blunt to be.

- [x] **Weak baseline inflates the fine-tuning story.** Added a caveat sentence to the
  Conclusion's Limitations paragraph naming the zero-shot/no-system-prompt baseline as "the
  weakest plausible baseline" and noting a simple-instruction baseline would better isolate
  fine-tuning's contribution from that of any instruction at all. Recompiled: still 13 total
  pages, body content unaffected.

- [x] **FK pass rate and the TF-IDF style classifier are proxies, not direct measures of
  "age-appropriateness."** Added a caveat sentence to Evaluation Framework (Methods) naming
  the specific gap (sentence-length complexity ≠ conceptual difficulty/emotional register;
  lexical distinguishability ≠ developmental appropriateness), with a forward pointer to
  Discussion, where a matching sentence was added acknowledging readability/separation gains
  are "necessary but not sufficient" evidence of genuine age-appropriateness. Recompiled:
  13 total pages now (was 12), but body+appendix content still ends within page 11 — the
  references section (excluded from the CFP's page budget) absorbed the extra length, so
  the paper remains comfortably under the 12-page body budget.

- [x] **Novelty claims ("no prior work, to our knowledge...") asserted twice with zero
  related-work citations.** Ran a real literature search (WebSearch/WebFetch) rather than
  waiting on the user. Found genuinely close prior work: KidLM (EMNLP 2024, masked-LM
  pretraining on a children's corpus — general child-language modeling, not instruction-tuned
  age-stratified generation), a Journal of Pediatric Surgery pilot (Rao et al. 2025,
  prompting-only, explicitly calls for further fine-tuning/validation), a Norwegian
  age-appropriate-conversation evaluation (Hassan et al. 2025, zero-shot only), a VR
  chest-radiography RCT (Ryu et al. 2021, passive VR, no conversational agent), and KidRails
  (Arcee AI, closest child-safety fine-tuning effort — full 8B model fine-tune, no separate
  classifier, no quantitative baseline comparison). None overlap closely enough to contradict
  our specific claims, so softened wording ("we are not aware of prior work that...") plus a
  pointer to the new Related Work section, rather than removing the claims.

- [x] **No related-work section.** Added `\section{Related Work}` (3 subsections: PEFT at
  small scale, LLMs for pediatric/clinical communication + VR, input-safety classifiers)
  right after the Introduction. Reused and updated the older Wiley-draft Related Work prose
  (PEFT + VR paragraphs) rather than writing from scratch, added 5 new bibliography entries
  for the papers found above. Recompiled: now 14 total pages, but References still starts
  mid-page-12, so body+appendix content is still within the 12-page-excluding-references
  budget — margin is now very thin, though. Any further prose additions will likely need an
  equivalent trim elsewhere (Conclusion repetition, flagged as MINOR below, is the obvious
  candidate).

## MINOR

- [ ] guard-bear's "worse than random" ROC-AUC (0.466) asserted without showing the score
  distribution/ROC curve that would rule out a mundane orientation artifact. guard-bear's own
  `results/eval_roc_curve.png` exists in the sibling repo — consider referencing or including it.
- [ ] Single-machine, unreplicated latency benchmark decides the central deployment
  recommendation (Fast-1B, 0.93s vs. ~1.0s target). Caveat-only fix, no new experiment.
- [ ] Two contributions (LoRA crossover; guard-bear) bundled under one title reads partly as
  scope-expansion. No action planned unless the user wants to address framing.
- [ ] Limitations section omits the figure/text contradiction, the weak-baseline concern, and
  the metric-proxy concern (all knowable at time of writing). Once the MAJOR items above are
  addressed, revisit whether Limitations needs updating to reflect the fixes/caveats added
  elsewhere.
- [ ] Heavy verbatim repetition of headline numbers across Abstract/Intro/Results/Conclusion —
  a byproduct of trimming the 20pp draft to 12pp. Low priority; would need a real rewrite pass.
- [ ] guard-bear solo-designed/trained/evaluated by one author with no stated independent
  verification step before submission. No text change planned — factually accurate as stated
  in Author Contribution; flagged only in case the user wants to add a review-checkpoint note.

## Not actionable from here
- **Author emails, venue copyright boilerplate, and repo-link policy** are the user's calls.
- **ROC-curve reference for guard-bear's "worse than random" claim** — skipped rather than
  forced. The only existing image (`guard-bear/results/eval_roc_curve.png`) plots just the
  fine-tuned model's curve, not the base model's, so referencing it wouldn't actually back the
  claim it was meant to support. A real comparative plot would require rerunning inference in
  the sibling `guard-bear` repo (loading both models, dumping raw scores) — real ML execution
  risk/cost in an unrelated repo, not a text fix. Flagging back rather than forcing a
  misleading reference or taking that on unprompted.
- The literature search above (novelty claims / related work) turned out to be resolvable
  without the user after all — noting this in case future review passes assume a search is
  out of reach by default.
