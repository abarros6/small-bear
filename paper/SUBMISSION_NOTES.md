# AECAI-PRiSM 2026 Submission — Status Notes

Canonical manuscript: `paper/WileyDesign/Optimal-Design-layout/Optimal-Design-layout.tex`
(two-column, USG.cls, ASNA style — matches what your partner compiled). Currently compiles
clean to **9 pages**, no errors, no undefined references, no overfull-hbox warnings.

Deadline: **July 16, 2026** (CMT submission).

---

## TODO before submitting

### Must fix — currently blank or placeholder
- [ ] `\editor{\textbf{Academic Editor:} \textbf{Guest Editor:} }` — empty fields, may need to stay blank until assigned, confirm with CfP/CMT instructions
- [ ] `\received{}` / `\revised{}` / `\accepted{}` — empty (normal pre-acceptance, but confirm CMT doesn't want anything here)
- [ ] `\journal{AE-CAI-PRiSM 2026?}` — stray `?`, confirm exact workshop/journal name string to print
- [ ] `\volume{}` / `\copyyear{}` / `\articledoi{}` / `\subarticletype{}` — all empty
- [ ] `\keywords{keywords here}` / `\transkeywords{keywords here}` — literal placeholder text, needs real keywords
- [ ] `\fundingInfo{}` — empty, confirm if you have funding to disclose
- [ ] **Copyright/license block** (right after `\dedicated{}`) — currently says *"© 2024 The Author(s) AIChE Journal published by Wiley Periodicals LLC on behalf of American Institute of Chemical Engineers"* — this is leftover boilerplate from a totally different Wiley journal (AIChE Journal, not HTL/AECAI-PRiSM). There's a literal comment above it: `%FOR THE LOVE OF GOD MAKE SURE THE ABOVE IS OKAY AND CORRECT` — someone already flagged this and it's still wrong. **Fix before submitting.**
- [ ] **Repository link in Appendix** (`https://github.com/abarros6/small-bear`) — contains your GitHub username. If this needs to stay a blind submission, this link deanonymizes you. Either remove it for the submission copy or confirm the venue allows a repo link in blind review.

### Worth a second look
- [ ] Author Contributions / Acknowledgments currently read `[withheld for double-blind review]` — fine for now, but you'll need real text if/when you de-anonymize post-acceptance
- [ ] `docs/dataset_creation_prompts.md` describes a "v2" dataset regeneration (VR-navigation-framed questions, `claude-opus-4-7`, explicit voice rules) that — based on file timestamps — **has not actually been run yet**. The paper's Dataset/Methodology sections still correctly describe the *current* on-disk data. If you run that regeneration before submitting, the paper will need another numbers pass.
- [ ] `WileyNJDv5_Template/wileyNJDv5_AMA.tex` (the other, single-column template) received the same content fixes earlier in this session and is fully functional at 12 pages, but is **not** what you're submitting — it's now a stale fork. Fine to ignore/delete, just don't let it confuse future edits.
- [ ] Visual proof pass — everything below was checked via text-extraction + compile logs, not a human read of the rendered two-column PDF. Worth opening `Optimal-Design-layout.pdf` once yourself to eyeball table placement and column breaks before submitting.

---

## What changed, section by section

**Title/author block** — Fixed a real bug: `\author[1]{Keep These Anonymous?}` and `\authormark{ANON?}` had literal `?` characters that broke a LaTeX name-filter macro (`\filtername`) on every compile pass. Replaced with clean "Anonymous Author 1" / "Anonymous Author 2" (matching your real 2-author paper), address/corresponding-author fields reworded to read as intentionally withheld rather than forgotten template filler.

**Abstract** — "500 synthetic examples per adapter" → "approximately 560 ... (1123 total across six topic categories)" — the old number was from before your dataset quality pass; this now matches what's actually on disk.

**Introduction** — Same dataset-count fix as the abstract. No other changes.

**Related Work (all 3 subsections)** — Trimmed for length only, no content removed: tightened sentences in Parameter-Efficient Fine-Tuning, LLMs in Clinical/Health Communication, and VR in Pediatric Care. Citations and claims unchanged.

**Dataset (§3)** — Substantive rewrite: was describing the *old* dataset (five categories, 1000 examples, 100/role/category). Now correctly describes six categories (added `edge_cases`, training-only), 1123 source examples with the real uneven per-category counts, and the actual 562/561 per-adapter split after role-based splitting. Also fixed a typo ("desigining"→"designing"), straight `"quotes"` → proper LaTeX curly quotes, and dash-style consistency — this section previously didn't match the polish of the rest of the paper.

**Methodology (§4)**
- *System Overview* / *Base Models*: trimmed for length, no content change.
- *LoRA as Declarative Programming*: cut the "declarative programming" conceptual aside entirely — decorative framing, not load-bearing for the empirical results.
- *Synthetic Data Generation*: added the sixth category (Edge Cases) to the itemized list, fixed the "500 training examples across five categories" claim to the real 1123/six-category numbers, noted edge_cases has no validation counterpart.
- *Training Protocol*: fixed the pass-count arithmetic ("500 examples → ~5 passes" was wrong; it's ~560 examples → ~4 passes at batch size 4, 600 steps).
- *Evaluation Framework*: same content, condensed into tighter parenthetical form (no metric or citation dropped).

**Results (§5)** — Only the Discussion subsection changed: shortened the crossover-mechanism paragraph (removed a redundant alternative-mechanism explanation that's superseded by the later rank sweep). All four results tables and their surrounding numbers are untouched — verified byte-for-byte against `results/*.txt` and confirmed correct before any edits.

**Extended Experiments (§6)** — Removed a redundant "Updated deployment recommendation" bullet list from §6.2 (Cross-Architecture), since §6.3 (Qwen 2.5) already has the final, superseding version — replaced with a one-line forward reference. No data or findings changed.

**Limitations (§7)** — Trimmed each of the five bullet paragraphs for length; no claims removed or softened.

**Conclusion (§8)** — Condensed from 4 paragraphs to 3, removing restatement that duplicated the Discussion and Extended Experiments sections. The deployment-recommendation paragraph now points to §6.3 instead of repeating the same four-way breakdown a third time.

**Backmatter** — Author Contributions and Acknowledgments were literal repeated filler text ("This is an author contribution text." / "This is acknowledgment text. Provide text here." × 9) — replaced with a single clear `[withheld for double-blind review]` placeholder each.

**Appendix** — Cut the "Claude Transcripts" subsection from a full page of verbatim prompt text down to a 3-sentence "Data Generation Provenance" paragraph pointing back to §4.4 (where the same category/safety-rule detail already lives). This was the single biggest page-count contributor.

**Housekeeping (not content)** — Removed 6 genuinely unused files from this folder (Chicago `.bib`/`.bst` — bibliography here is manual `thebibliography`, not BibTeX-driven — plus 3 unused `.sty` files), verified via full recompile with no regression. Untracked generated LaTeX build artifacts (`.aux`/`.log`/`.pag`/`.bbl`/`.synctex.gz`) from git, kept the compiled PDF tracked.
