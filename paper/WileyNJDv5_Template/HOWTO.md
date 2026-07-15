# How to use the Wiley NJDv5 LaTeX template

This is Wiley's official "NJDv5" journal article class. The file you actually edit is
**`wileyNJDv5_AMA.tex`** — everything else is machinery (the class, packages, fonts,
citation styles) or generated output. This guide covers compiling it, the parts you need
to change, and how we share it between the two of us.

## What's in this folder

| File / folder | What it is | Touch it? |
|---|---|---|
| `wileyNJDv5_AMA.tex` | **The manuscript.** This is your paper. | ✅ Edit this |
| `wileyNJD-AMA.bib` | Bibliography database (your references go here) | ✅ Edit this |
| `WileyNJDv5.cls` | The Wiley document class — defines the whole layout | ❌ Don't edit |
| `*.sty` | LaTeX packages the class depends on | ❌ Don't edit |
| `wileyNJD-*.bib` / `wileyNJD-*.bst` | 10 citation-style sets (AMA, APA, Harvard, MLA, Vancouver, …) | Pick one (see below) |
| `Fonts/` | Bundled fonts the class can use | ❌ Leave as-is |
| `empty.pdf` / `empty.eps` | Placeholder figure used by the template | Replace with your figures |
| `NJDv5_Authorguideline-document/` | Wiley's official author instructions (PDF + tex) | 📖 Read for reference |
| `*.aux .log .bbl .blg .synctex .pdf` | **Generated** when you compile — not source | ❌ Ignore (regenerated) |

## Prerequisites

You need a LaTeX distribution installed:

- **macOS:** [MacTeX](https://tug.org/mactex/) — `brew install --cask mactex-no-gui`
- **Windows:** [MiKTeX](https://miktex.org/)
- **Linux:** TeX Live — `sudo apt install texlive-full`
- **No install / easiest for collaboration:** upload the folder to [Overleaf](https://overleaf.com)
  (see "Sharing" below) — nothing to install.

## How to compile

Because the bibliography uses BibTeX, you need the classic 4-step sequence (run from inside
this folder):

```bash
pdflatex wileyNJDv5_AMA
bibtex   wileyNJDv5_AMA
pdflatex wileyNJDv5_AMA
pdflatex wileyNJDv5_AMA
```

The result is `wileyNJDv5_AMA.pdf`.

- In a GUI editor (TeXShop, TeXworks, VS Code + LaTeX Workshop), set the build recipe to
  **pdfLaTeX → BibTeX → pdfLaTeX → pdfLaTeX**, or use the editor's "LaTeX + BibTeX" preset.
- On Overleaf this happens automatically — just hit "Recompile".

> If references show up as `[?]` or are missing, you skipped the `bibtex` step or didn't run
> `pdflatex` enough times afterward. Run the full 4-step sequence again.

## What to change in `wileyNJDv5_AMA.tex`

The top of the file (the preamble, before `\begin{document}`) is where your metadata lives:

| Line area | Command | Replace with |
|---|---|---|
| Top | `\documentclass[AMA,Times1COL]{WileyNJDv5}` | Citation style + layout (see options below) |
| ~4 | `\articletype{Article Type}` | e.g. `Research Article` |
| ~9 | `\journal{Journal}` | Target journal name |
| ~20 | `\title{...}` | Your title |
| ~22 | `\author[1]{Mark Taylor}` | Your names (the `[1]` ties to an address block) |
| ~28 | `\authormark{...}` | Running header, e.g. `BARROS \textsc{et al.}` |
| ~31 | `\address[1]{...}` | Your department / institution |
| ~37 | `\corres{...}` | Corresponding author + email |
| ~44 | `\abstract[Abstract]{...}` | Your abstract |
| ~51 | `\keywords{...}` | Your keywords |

Then the body is plain LaTeX: `\section{...}`, `\cite{...}`, `\begin{figure}`, etc. Replace
the lorem-ipsum sections with your content.

### Document class options

`\documentclass[AMA,Times1COL]{WileyNJDv5}`

- **First option = citation style.** `AMA` selects the AMA reference style and its `.bst`.
  Other choices map to the other `wileyNJD-*` files: `APA`, `APS`, `AMS`, `Harvard`,
  `Chicago`, `MLA`, `MPS`, `Vancouver`, `WCMS`. **Check your target journal's required
  style** in the author guideline PDF.
- **Layout option:** `Times1COL`, `STIX1COL`, `STIX2COL`, or `STIXSMALL` (commented hints
  are on line 1 of the tex).

If you change the citation style, also update the bibliography line near the end of the
document so it points at the matching `.bib`:

```latex
\bibliography{wileyNJD-AMA}   % <- change AMA to your chosen style's bib
```

## Adding references

1. Put your BibTeX entries in `wileyNJD-AMA.bib` (or your chosen style's `.bib`).
2. Cite them in the text with `\cite{key}`.
3. Recompile with the full 4-step sequence.

Note: line ~868 of the tex has `\nocite{*}`, which forces **every** entry in the `.bib` to
appear in the reference list whether cited or not. Comment that line out once you're using
real references so only cited works show up.

## Adding figures

Replace `empty` in the `\includegraphics{empty}` calls with your figure file (PDF, PNG, or
EPS works). Drop the image file in this folder and reference it by name without the
extension. Remove the `draft` option from `\includegraphics` to show the actual image
instead of an outline box.

## Sharing between us

Two easy options:

- **Overleaf (recommended, zero setup):** Compress this whole folder to a `.zip`, then in
  Overleaf → *New Project → Upload Project*. Overleaf detects `wileyNJDv5_AMA.tex` as the
  main file and compiles automatically. Use Overleaf's share link for live collaboration.
- **Git (this repo):** The whole folder is committed, so a `git pull` gets you everything —
  class, fonts, styles, and all. You can ignore the generated `.aux/.log/.pdf` churn; just
  recompile locally.

When sharing, you don't need to send the generated files (`.aux`, `.log`, `.bbl`,
`.synctex`, `.pdf`) — your collaborator regenerates them by compiling. But keeping them
doesn't break anything.

## Reference

The authoritative instructions from Wiley are in
`NJDv5_Authorguideline-document/Author-guideline_Wiley.pdf` — consult it for journal-specific
requirements before submitting.



add a diagram with the lora adapters and the underlying llm 

add some future works statements about the size of the adapters being negligable to the underlying model so there is potential for creeating as many as we want to adapt to 

what is the rouge test?