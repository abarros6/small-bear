# Forward Experiments Roadmap

This file is the source of truth for follow-up work after the paper (`../paper/Paper.tex`).
Sections are ordered by priority. Each entry includes a run count and a rough wall-clock
estimate so compute cost is visible at a glance. Sections 1–3 are active work. Sections 4–5
are infrastructure prerequisites and unscheduled future work, respectively.

For project context, hardware constraints, and the Critical Lessons that constrain training
choices, see `../CLAUDE.md`. For full results, methodology, and the limitations that motivate
this roadmap, see `../paper/Paper.tex` §§5–6.

---

## §1 — Primary: Investigate the Crossover Mechanism

**Question.** The paper reports a configuration-ordering crossover (Standard wins on 3B,
Fast wins on 1B). Standard and Fast differ in two parameters simultaneously — `rank` (8 vs. 4)
and `num_layers` (16 vs. 8) — so the responsible factor cannot be identified from existing
data. Two plausible mechanisms:

- **(a) Capacity regularization** — the 1B model's smaller representational capacity benefits
  from a smaller adapter; the 3B model can exploit the additional degrees of freedom of rank 8.
- **(b) Layer coverage saturation** — the Standard adapter (`num_layers = 16`) covers 100% of
  the 1B model's transformer stack but only 57% of the 3B's. Over-coverage on 1B may explain
  the reversal independently of rank.

**Recommended design — controlled rank sweep, fixed `num_layers`:**

| Axis | Values |
|------|--------|
| `num_layers` | 8 (fixed) |
| `lora_parameters.rank` | 2, 4, 8, 16 |
| Model | Llama 3.2 1B-Instruct-4bit, Llama 3.2 3B-Instruct-4bit |
| Role | `age_5_11` only (deployment target — halves run count) |
| Seed | 42, 1337 |

Total: 4 ranks × 2 models × 2 seeds = **16 runs**. Wall-clock ~8 h sequentially on M4.

**Decision criterion.** Plot FK pass rate and classifier accuracy versus rank for each model
size. If the crossover reverses smoothly as rank changes (Fast-1B optimal at low rank,
Standard-3B optimal at higher rank), capacity regularization is the mechanism. If the crossover
persists at every rank, layer coverage is the mechanism.

**Optional depth (if time permits):**

- **Layer sweep at fixed rank.** `rank = 4`, `num_layers ∈ {4, 8, 16}`, both model sizes,
  age_5_11, 2 seeds = 12 runs (~6 h). Discriminating evidence for mechanism (b).
- **Third seed (2718) on the rank sweep.** 8 additional runs (~4 h). Lets the rank sweep
  report mean ± std and judge whether differences are seed-noise-sized.

---

## §2 — Secondary: Alternative Model Family + Smaller Scales

**Question.** Is the crossover Llama-specific or architecture-general? Does it persist at
even smaller scales where capacity is more constrained?

**Recommended design — Qwen 2.5 family sweep:**

| Axis | Values |
|------|--------|
| Model | Qwen 2.5 0.5B-Instruct-4bit, Qwen 2.5 1.5B-Instruct-4bit, Qwen 2.5 3B-Instruct-4bit |
| Adapter config | Standard (r=8, 16 layers), Fast (r=4, 8 layers) |
| Role | both age groups |
| Seed | 42 |

Total: 2 configs × 3 models × 2 roles = **12 runs**. Wall-clock ~5–6 h.

The 0.5B model gives a third capacity point below Llama 3.2 1B and is independently interesting:
4-bit quantized it is ~300 MB and could be the lowest-latency deployment candidate (plausibly
sub-0.5s on M4).

**Stretch probe — SmolLM2 360M (different family, extreme small scale):**

| Axis | Values |
|------|--------|
| Model | SmolLM2 360M Instruct |
| Adapter config | Standard, Fast |
| Role | both |
| Seed | 42 |

Total: **4 runs**. Wall-clock ~1 h.

**Risk.** Below ~500M parameters, instruction-following can degrade to where 500 training
examples cannot imprint a coherent age-register. A null result is informative — it establishes
a capacity floor for this task — but should not block other work.

**Shared prerequisite.** Each new model family uses its own chat template. Validate
`apply_chat_template` end-to-end on a handful of training examples before committing to
training (Critical Lesson L9 in `../CLAUDE.md`). Confirm the first token is the family's BOS
token and not a duplicate (Critical Lesson L6). One dry-run tokenization per family.

---

## §3 — Quick Wins

### Standard adapter perplexity

The paper's Table 1 reports Fast-adapter perplexity but not Standard. Fix: val-loss-only pass
over `data/{role}/valid.jsonl` using each existing Standard adapter checkpoint at step 600.
No retraining required — the adapters are already in `adapters/{1b,3b}/{role}/`.

Total: **4 eval passes**. Wall-clock ~10 min.

Implementation: either add a `--perplexity` mode to `src/evaluate.py` that loads an adapter
and computes mean cross-entropy, or write a small standalone script. The `mlx_lm.lora` CLI
also supports `--test` for val-only loss computation; check whether that is sufficient.

---

## §4 — Infrastructure Prerequisites

These are not experiments themselves — they are the changes needed before the §1 rank sweep
can be executed cleanly. Without them, every new run requires hand-editing a YAML.

1. **Parameterize training scripts.** `scripts/train_3b.sh` and `scripts/train_1b.sh` currently
   hardcode config paths. Accept `$1` as the config path so a sweep driver can invoke them
   in a loop. Default to the existing config for backwards compatibility.
2. **Sweep config generator.** A small Python script that writes per-experiment YAML configs
   into `configs/sweeps/` with deterministic names — e.g.
   `rank4_layers8_seed42_3b_age_5_11.yaml` — and matching `adapter_path` pointing into
   `adapters/sweeps/<config_name>/`. Generates the rank sweep configs in §1 from a single
   command.
3. **Multi-seed aggregation in `src/evaluate.py`.** Extend to accept a glob of output JSONLs
   (e.g. `outputs/sweeps/rank4_layers8_*_3b_age_5_11_outputs.jsonl`) and report mean ± std
   for each metric across seeds.
4. **(Optional) Perplexity mode in `src/evaluate.py`.** Required only if the standalone
   approach in §3 is not used.

These changes are deferred to the session that begins executing §1 — there is no value in
landing them ahead of the experiments they enable.

---

## §5 — TODO (future, not scheduled)

Tracked here so they are not lost. None are blocking the §1–§3 work.

- **Dataset quality pass.** User-owned. The user will curate or rewrite existing examples to
  raise quality. Should land before any further training rounds that depend on the dataset
  (i.e. before §1 if practical, otherwise §1 results are interpreted as "lower bound on
  achievable quality with current data").
- **Human evaluation.** Recruit peer raters to score outputs on age-appropriateness.
  Addresses the paper's "learned stylistic imitation vs. genuinely age-appropriate" limitation
  that no automated metric can resolve. Needs a rating protocol, sample selection (~30 outputs
  per adapter), and an inter-rater agreement check.
- **Safety evaluation.** Automated safety eval — guard model (e.g. Llama Guard) or trained
  classifier — referenced in paper Limitations as planned. Most useful once the deployment
  configuration is locked in (i.e. after §1 picks a winning config).

---

## §6 — Existing Files to Reference

For the session that implements the sweep:

- `configs/age_5_11_3b_lora.yaml` — template for sweep configs (every parameter is documented
  inline with rationale).
- `scripts/train_3b.sh`, `scripts/train_1b.sh` — to be parameterized per §4.
- `src/evaluate.py` — existing readability / latency / separation metrics; extend per §4.
- `src/generate_outputs.py` — already supports `--variant` flag; extend for sweep naming.
- `src/constants.py` — add Qwen 2.5 and SmolLM2 base model IDs for §2.
- `src/inference.py` — supports `--variant` and `--base` already; should accept the sweep
  config naming used by the generator script.
