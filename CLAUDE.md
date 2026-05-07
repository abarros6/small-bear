# Dr. Beary Good — Project Context

## What This Is

A role-adaptive LLM ("Dr. Beary Good") for a VR pediatric hospital guide at Victoria Hospital,
London ON. The system serves two pediatric age groups — ages 5–11 and ages 12–18 — by switching
between two LoRA adapters trained on a purpose-built dataset. An ablation study compares
3B vs. 1B parameter base models across two adapter configurations (rank 8/16 layers and rank 4/8 layers).

## Research Contributions

1. **Multi-LoRA Architecture** — Two separate LoRA adapters share one quantized base model.
   Role is supplied explicitly by the calling application (VR app knows the patient's age).
2. **LIMA Validation** — ~500 high-quality examples per role produce measurable style
   adaptation without any system prompt, validating the LIMA hypothesis at small scale.
3. **No-System-Prompt Proof** — Adapters are trained and evaluated with zero system prompt.
   The communication register is encoded entirely in the adapter weights, not in prompt
   engineering. The VR application team injects their own system prompt at deployment time.
4. **1B vs. 3B Ablation** — Same training pipeline, same dataset, two base models. Compares
   latency vs. style quality tradeoff for VR real-time usage.

## Paper

The full write-up of this work is at `paper/Paper.tex` (IEEEtai format). It is the canonical
reference for results, methodology rationale, and the limitations that drive forward work.

Headline empirical finding from the paper: a **configuration-ordering crossover** —
Standard ($r=8$, 16 layers) outperforms Fast on 3B; Fast ($r=4$, 8 layers) outperforms Standard
on 1B. The reversal is consistent across all five readability metrics and the inter-role
classifier. The mechanism is resolved: rank is the dominant factor (rank sweep) and layer depth
is an independent secondary contributor (layer sweep). See `docs/EXPERIMENTS.md` §1 for details.

## Hardware & Stack

| Component | Detail |
|-----------|--------|
| Hardware | Mac Mini M4, 16 GB unified RAM |
| Python | 3.12 (Homebrew `/opt/homebrew/bin/python3.12`) |
| Framework | MLX (Apple Silicon, on-device GPU) |
| Base model (primary) | `mlx-community/Llama-3.2-3B-Instruct-4bit` |
| Base model (ablation) | `mlx-community/Llama-3.2-1B-Instruct-4bit` |
| Base model (cross-arch) | `mlx-community/Qwen2-0.5B-Instruct-4bit`, `mlx-community/SmolLM2-360M-Instruct`, `mlx-community/Qwen2.5-{0.5,1.5,3}B-Instruct-4bit` |
| Method | QLoRA — 4-bit quantized base, float32 LoRA adapters |
| mlx-lm | 0.30.7 (pinned — see Known Working Versions) |

## Project Structure

```
small-bear/
├── .gitignore
├── CLAUDE.md                               # This file
├── README.md                               # GitHub-facing docs
├── requirements.txt                        # Pinned to known working versions
├── docs/
│   ├── COMMANDS.md                         # Full reproduction sequence from clone to results
│   ├── EXPERIMENTS.md                      # Forward research roadmap (crossover ablation, etc.)
│   └── dataset_creation_prompts.md         # exact prompts used to generate the synthetic dataset
├── paper/
│   └── Paper.tex                           # IEEEtai write-up — canonical results & rationale
├── configs/
│   ├── age_5_11_3b_lora.yaml              # rank 4, 8 layers → adapters/fast/3b/
│   ├── age_12_18_3b_lora.yaml
│   ├── age_5_11_1b_lora.yaml              # rank 4, 8 layers → adapters/fast/1b/
│   └── age_12_18_1b_lora.yaml
├── data/
│   ├── source/
│   │   ├── train/                          # One JSONL per category — training examples
│   │   └── validate/                       # One JSONL per category — hand-curated validation
│   ├── age_5_11/                           # train.jsonl + valid.jsonl (from prepare_data.py)
│   └── age_12_18/
├── adapters/                               # .gitignored — large binary LoRA weights
│   ├── 3b/                                 # Standard adapters (rank 8, 16 layers)
│   │   ├── age_5_11/
│   │   └── age_12_18/
│   ├── 1b/                                 # Standard adapters (rank 8, 16 layers)
│   │   ├── age_5_11/
│   │   └── age_12_18/
│   └── fast/                               # Fast adapters (rank 4, 8 layers) — current configs write here
│       ├── 3b/
│       │   ├── age_5_11/
│       │   └── age_12_18/
│       └── 1b/
│           ├── age_5_11/
│           └── age_12_18/
├── outputs/                                # .gitignored — model-generated responses
├── results/                                # tracked — evaluation reports (committed for reproducibility)
├── logs/                                   # .gitignored — training logs
├── scripts/
│   ├── setup.sh                            # mkdir -p all required directories
│   ├── train_3b.sh                         # sequential training of both adapters on 3B
│   └── train_1b.sh                         # sequential training of both adapters on 1B
└── src/
    ├── constants.py                        # ROLES, BASE_MODEL_3B, BASE_MODEL_1B (no system prompts)
    ├── prepare_data.py                     # Source JSONL → per-role train/valid splits (no sys prompt)
    ├── evaluate.py                         # Readability (FK/SMOG/Fog/Coleman/TTR), latency,
    │                                       #   tokens/sec, inter-role style separation classifier
    ├── inference.py                        # Explicit-role inference (adapter + optional sys prompt)
    │                                       #   --variant flag selects adapter subdirectory (e.g. fast)
    └── generate_outputs.py                 # Run inference on valid set → outputs/ for evaluation
                                            #   --variant, --base flags; writes token_count + tps
```

**NOT in this repo:**
- `src/role_detector.py` — dead code; VR app supplies role explicitly from patient age
- `fused/` directory — never fuse adapters back into base weights; that defeats the
  multi-adapter purpose and loses the ability to switch roles at runtime
- `--fused` flag in inference.py
- System prompts in `constants.py` — they are external to this project

## Dataset Format

Source JSONL files live in two subdirectories:
- `data/source/train/` — one file per category, training examples
- `data/source/validate/` — one file per category, hand-curated validation examples

Both use the same format:
```json
{"instruction": "...", "response": "...", "role": "5-11|12-18", "category": "..."}
```

Source files use `"role": "5-11"` / `"12-18"`. `prepare_data.py` maps these to
`"age_5_11"` / `"age_12_18"` via `ROLE_MAP` on load. Do not rename source files.

Training JSONL (after `prepare_data.py`, in `data/{role}/`):
```json
{"messages": [
  {"role": "user",      "content": "<instruction>"},
  {"role": "assistant", "content": "<response>"}
]}
```

**Role name normalisation:** Source files use `"role": "5-11"` and `"role": "12-18"`.
`prepare_data.py` maps these to `"age_5_11"` and `"age_12_18"` via `ROLE_MAP` on load.
Do not rename source files — the mapping is handled in code.

**No system prompt in training data.** This is a deliberate design choice — see
"No-System-Prompt Design" section below.

### Current Training Counts (post dataset quality pass, May 2026)

| File | Source examples | age_5_11 train | age_12_18 train |
|------|-----------------|----------------|-----------------|
| `edge_cases.jsonl` | 50 | 25 | 25 |
| `emotional_reassurance.jsonl` | 225 | 110 | 115 |
| `faqs_general_curiosity.jsonl` | 213 | 105 | 108 |
| `hospital_rules_and_routines.jsonl` | 212 | 109 | 103 |
| `what_to_expect.jsonl` | 218 | 109 | 109 |
| `who_are_these_people.jsonl` | 205 | 104 | 101 |
| **Total** | **1123** | **562** | **561** |

Validation: 100 examples total (20 per category, 10 per role each). Replaced with
independent examples in May 2026 — see `docs/EXPERIMENTS.md` §5.

`edge_cases` is a sixth training-only category covering out-of-scope requests,
safety-boundary probes, distress escalation, meta questions, and boredom/disengagement.
It is not represented in the validation set.

## No-System-Prompt Design

**Why train without a system prompt:**

When a system prompt is present in training data, the model learns to condition its style on
that prompt being present. Remove the prompt at inference and style degrades. The adapter has
learned a prompt-following association, not an intrinsic register.

When training uses only `[user, assistant]` pairs, the model must encode the register directly
in the adapter weights. The style then appears regardless of what system prompt (if any) is
present at inference.

**What this means for deployment:**
- The VR application team supplies their own system prompt (hospital name, character name,
  any safety rules they want). This adds application context.
- The adapter already provides the age-appropriate communication register.
- The two layers complement each other cleanly — there is no conflict.

**What this means for evaluation:**
- Evaluation is always run without a system prompt (matching training conditions).
- Any style difference between `age_5_11` and `age_12_18` outputs is entirely
  attributable to the adapter weights.
- A side-by-side comparison with the base model (no adapter, no system prompt) isolates
  exactly what fine-tuning contributed.

## Hyperparameters & Inference Settings

All four configs share identical hyperparameter values. The only differences between them are
`model`, `data`, and `adapter_path`. This is intentional — the ablation study is valid only
if every other variable is held constant.

Two adapter configurations exist. The current configs produce the fast variant (`adapters/fast/`).
Standard adapters (`adapters/3b/` and `adapters/1b/`) were trained with rank 8 / 16 layers.

| Parameter | Standard | Fast (current configs) |
|-----------|----------|------------------------|
| `num_layers` | 16 | **8** |
| `rank` | 8 | **4** |
| `scale` | 20.0 | 20.0 |
| `dropout` | 0.0 | 0.0 |

### LoRA Architecture

**`num_layers: 8`** (current configs; standard was 16)
How many transformer layers (counted from the top) receive LoRA adapter matrices.
The 3B model has 28 layers total — `num_layers: 8` adapts the upper 29%.
The 1B model has 16 layers total — `num_layers: 8` adapts the upper 50%.
Upper layers handle high-level semantic and stylistic decisions, making them the
highest-value target for register adaptation. Halving from 16 to 8 layers tests whether
the style signal lives primarily in the top layers — results confirmed it does, with
comparable or superior style separation at reduced adapter size.

**`lora_parameters.rank: 4`** (current configs; standard was 8)
The rank of the two low-rank matrices A and B inserted into each adapted layer
(the adapter's weight delta is `scale * A @ B^T`). Trainable parameters per adapted
layer ≈ `2 * rank * hidden_dim`. Rank 4 halves the adapter parameter count versus rank 8.
Register adaptation is a simple style shift, not knowledge acquisition, so rank 4 is
sufficient — results confirmed comparable or superior style separation on most variants.

**`lora_parameters.scale: 20.0`**
Scalar multiplier applied to the adapter's output before it is added to the base layer's
output. Controls how aggressively the adapter overrides base model behaviour. 20.0 is the
mlx-lm default. Lower values (8–10) produce subtler style shifts that stay closer to the
base model; higher values (40+) risk degrading response coherence on out-of-distribution
queries. **Do not compute this as alpha/rank** — mlx-lm treats it as a direct scalar,
not a ratio. Using alpha/rank gives 1.0, which effectively disables the adapter
(Critical Lesson L3).

**`lora_parameters.dropout: 0.0`**
Fraction of LoRA activations randomly zeroed during each training forward pass —
a regularisation technique to reduce overfitting. 0.0 is correct here: the dataset
is small and already high-quality (LIMA-style curation), so adding noise via dropout
would slow convergence without benefit. If validation loss diverges upward while
training loss keeps falling, increasing dropout to 0.05–0.10 is the first thing to try.

### Training Schedule

**`batch_size: 4`**
Number of training examples processed per gradient update step. Larger batches produce
smoother, lower-variance gradient estimates and a more stable loss curve, but require more
GPU memory. 4 is the practical ceiling on M4 16 GB unified RAM with the 3B 4-bit model
at `max_seq_length: 768`. The 1B configs could potentially run at batch_size=8 given the
smaller memory footprint, but keeping it at 4 preserves identical training dynamics for
a clean ablation comparison.

**`iters: 600`**
Total gradient update steps — not epochs. With ~475 training examples per role and
`batch_size: 4`, 600 steps ≈ 5 passes over the data. Chosen by watching validation loss
curves during early experiments: fewer than ~400 steps left the style signal too weak;
beyond ~700 steps validation loss began to rise (overfitting). The `save_every: 100`
checkpoints allow post-hoc selection of the best step if the final checkpoint overfits.

**`learning_rate: 1e-5`**
Step size for each gradient update. 1e-5 is the mlx-lm validated default for QLoRA on
Llama 3.2 (Critical Lesson L3). Values above ~5e-5 cause loss spikes; above 1e-4 produce
NaN gradients from step 1 on a 4-bit quantized model. Values below 1e-6 converge too
slowly — the style adaptation would not emerge within 600 steps. This is the most
consequential single hyperparameter in the config.

**`lr_schedule.name: cosine_decay` + `warmup: 100`**
The learning rate ramps linearly from 0 to `learning_rate` over the first 100 steps
(warmup), then follows a cosine curve decaying toward 0 at step 600. Warmup prevents
large destabilising weight updates in the early steps when gradient estimates are noisiest
and the adapter weights are freshly initialised near zero. Without warmup, early loss
spikes are more likely and the initial weight changes can be hard to recover from.
The cosine decay (vs. constant LR) smoothly reduces the step size toward the end of
training, allowing fine-grained convergence without requiring a manually tuned decay point.

**`mask_prompt: true`**
When true, the cross-entropy loss is computed only over assistant response tokens —
the user turn tokens contribute zero gradient. This is the single most important
training setting after the data format. Without it, the model spends capacity learning
to predict the user's question, which adds noise, slows convergence, and dilutes the
adapter's register signal. Always true for this project.

**`max_seq_length: 768`**
Sequences longer than 768 tokens are truncated before entering the model.
768 tokens ≈ 550 words, sufficient for all hospital-guide Q&A pairs in the dataset.
Attention memory scales quadratically with sequence length — increasing this to 1024+
would significantly slow training on M4. Decreasing to 512 risks truncating longer
assistant responses, which would produce broken training targets and degrade output quality.

**`seed: 42`**
Random seed for adapter weight initialisation and training data shuffling. Fixed for
fully reproducible runs. Changing this produces a different but equally valid adapter —
useful for verifying result stability across seeds, or building a seed ensemble.

### Inference Settings

All inference uses `mlx_lm.generate` with no sampling parameters explicitly set.
All values below are mlx-lm defaults — they are documented here because they are
consequential and not visible in the source without reading the mlx-lm internals.

**`temperature: 0.0`** (default — greedy decoding)
Scales the model's output logits before token selection. At 0.0, the highest-probability
token is always chosen — fully deterministic, no randomness. This is the right choice for
a pediatric medical context: identical queries always produce identical responses, and
there is zero chance of an unexpected output. The tradeoff is that responses can sound
slightly formulaic. Values of 0.3–0.5 would introduce natural conversational variation
while remaining conservative. Values above 1.0 produce increasingly unpredictable outputs
and are not appropriate here.

**`top_p: 1.0`** (default — nucleus sampling disabled)
At each generation step, restricts sampling to the smallest set of tokens whose cumulative
probability ≥ top_p. At 1.0 all tokens remain eligible. This setting only matters when
temperature > 0; at temperature=0.0 there is no sampling so top_p has no effect.

**`top_k: 0`** (default — top-k sampling disabled)
Restricts sampling to the K highest-probability tokens at each step. 0 = disabled.
Like top_p, irrelevant at temperature=0.0.

**`repetition_penalty: 1.0`** (default — no penalty)
Divides the logits of previously generated tokens by this factor to discourage the model
from repeating itself. At 1.0 there is no penalty. Greedy decoding (temperature=0.0) is
somewhat prone to repetitive loops on long outputs — if this is observed, increasing to
1.1–1.3 is the first mitigation to try before raising temperature.

**`max_tokens: 300`** (set in `inference.py`, overridable via `--max-tokens`)
Hard ceiling on the number of tokens generated per response. ~300 tokens ≈ 200–250 words.
Generation stops at this limit OR at the model's EOS token, whichever comes first.
Well-trained adapters consistently produce EOS before reaching 300 tokens. Increase this
if responses are being cut off mid-sentence on longer queries. Decrease it to enforce
brevity and reduce latency — relevant for VR real-time usage where response time matters.

## Complete Command Reference

```bash
# --- SETUP (one time) ---
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
bash scripts/setup.sh                   # creates all required directories

# --- DATA PREPARATION ---
# Drop source JSONL files into data/source/, then:
python src/prepare_data.py              # reads ALL *.jsonl from data/source/, splits per-role

# --- TRAINING ---
# Configs use rank 4, 8 layers → adapters/fast/{size}/{role}/
# Do NOT run both simultaneously — GPU OOM on M4 16 GB.
bash scripts/train_3b.sh               # → adapters/fast/3b/{role}/
bash scripts/train_1b.sh               # → adapters/fast/1b/{role}/

# --- INFERENCE (no system prompt — matches training conditions) ---
python src/inference.py --role age_5_11 --query "Will the X-ray hurt?"
python src/inference.py --role age_12_18 --query "Will the X-ray hurt?"

# 1B ablation:
python src/inference.py --role age_5_11 --model-size 1b --query "Will the X-ray hurt?"

# Fast variant:
python src/inference.py --role age_5_11 --variant fast --query "Will the X-ray hurt?"

# Compare against untuned base model (no adapter, no system prompt):
python src/inference.py --base --query "Will the X-ray hurt?"

# VR deployment testing (with application system prompt):
python src/inference.py --role age_5_11 --query "Will the X-ray hurt?" \
    --system-prompt "You are Dr. Beary Good at Victoria Hospital."

python src/inference.py --role age_5_11 --interactive
python src/inference.py --benchmark    # runs standard queries across both roles, no system prompt

# --- EVALUATION ---
# Evaluate training data quality (combine source files into a temp file first)
cat data/source/train/*.jsonl > /tmp/all_train.jsonl
python src/evaluate.py --data /tmp/all_train.jsonl

# Generate model outputs — run one at a time (GPU OOM if concurrent)
# Naming convention written by generate_outputs.py:
#   per-role:   <variant>_<role>_<size>_outputs.jsonl
#   aggregate:  all_<variant>_<size>_outputs.jsonl
# Where <variant> is "fast" (--variant fast), "base" (--base), or absent for Standard.
# Example: standard 3B age 5-11 → outputs/age_5_11_3b_outputs.jsonl
#          fast 1B aggregate    → outputs/all_fast_1b_outputs.jsonl
python src/generate_outputs.py                              # standard 3B
python src/generate_outputs.py --model-size 1b             # standard 1B
python src/generate_outputs.py --variant fast              # fast 3B
python src/generate_outputs.py --variant fast --model-size 1b   # fast 1B
python src/generate_outputs.py --base                      # base 3B (no adapter)
python src/generate_outputs.py --base --model-size 1b     # base 1B

# Evaluate model outputs — saves to results/ and prints to stdout
python src/evaluate.py --data outputs/all_3b_outputs.jsonl --latency --separation --output results/standard_3b_eval.txt
python src/evaluate.py --data outputs/all_1b_outputs.jsonl --latency --separation --output results/standard_1b_eval.txt
python src/evaluate.py --data outputs/all_fast_3b_outputs.jsonl --latency --separation --output results/fast_3b_eval.txt
python src/evaluate.py --data outputs/all_fast_1b_outputs.jsonl --latency --separation --output results/fast_1b_eval.txt
python src/evaluate.py --data outputs/all_base_3b_outputs.jsonl --latency --separation --output results/base_3b_eval.txt
python src/evaluate.py --data outputs/all_base_1b_outputs.jsonl --latency --separation --output results/base_1b_eval.txt
```

## Critical Lessons — DO NOT REPEAT THESE MISTAKES

### L1. NEVER pre-format chat strings as training data
Using `<|begin_of_text|><|start_header_id|>...` in training data causes double-BOS tokens
(`[128000, 128000, ...]`) because `tokenizer.encode()` prepends BOS again. This produces NaN
gradients from step 1. **Always use `{"messages": [...]}` format** and let mlx-lm handle
tokenization via `apply_chat_template`.

### L2. Use the `mlx_lm.lora` CLI, NOT a custom Python training script
The mlx-lm Python API changed repeatedly between versions. The CLI is stable across versions.
Never write a custom training loop for mlx-lm.

### L3. Use mlx-lm default hyperparameters — do not invent your own
| Parameter | Wrong | Correct |
|-----------|-------|---------|
| learning_rate | 2e-4 | 1e-5 |
| lora scale | alpha/rank = 2.0 | 20.0 (mlx-lm default) |
| rank | 16 | 8 |

### L4. `adapter_config.json` is required for loading adapters
The CLI saves this automatically. If you manually move adapter files, carry the JSON too.

### L5. Cannot run inference while training — GPU OOM on M4 16GB
Schedule all inference/testing AFTER training finishes.

### L6. Test tokenization before committing to a training run
Run `tokenizer.encode(your_sample)` and confirm the first token is `128000` (BOS), not
`[128000, 128000, ...]`.

### L7. Create all required directories before training
`tee logs/training.log` fails silently if `logs/` doesn't exist. Use `bash scripts/setup.sh`.

### L8. Use `mlx_lm.lora`, not `python -m mlx_lm.lora`
As of mlx-lm 0.30.7, `python -m mlx_lm.lora` shows a deprecation warning.

### L9. Always use `apply_chat_template` — even without a system prompt
Training and inference without a system prompt does NOT mean skipping the chat template.
The tokenizer still wraps messages in Llama's `<|begin_of_text|>...<|eot_id|>` format.
`apply_chat_template` handles this correctly whether or not a system message is present.
Never pass a raw query string directly as the prompt — always build a messages list first.

### L10. prepare_data.py must load from a directory, not a single file
Use `glob("*.jsonl")` over the source directory. Multiple source files are normal.

### L11. Do NOT fuse adapters
`mlx_lm.fuse` merges adapter weights permanently into the base model. This defeats the
entire purpose of multi-adapter role switching — you end up with N separate full models
instead of one shared base + N small adapter files. Never use `mlx_lm.fuse` in this project.

### L12. No system prompts in training data
System prompts in training create a prompt-following association, not weight-encoded style.
The model learns "produce this style when you see this prompt", not "always produce this style."
Evaluation without the same system prompt then shows degraded register. Train on
`[user, assistant]` pairs only — the style must live in the weights.

## Known Working Versions (2026-02-28)

```
Python          3.12.x (Homebrew)
mlx             0.30.6
mlx-lm          0.30.7
mlx-metal       0.30.6
transformers    5.2.0
datasets        4.6.0
textstat        0.7.13
numpy           >=1.26.0
scikit-learn    >=1.4.0   (inter-role style separation classifier in evaluate.py)
```

## Ablation Study: 3B vs. 1B vs. Standard vs. Fast

All variants have been trained and evaluated. Results live in `results/`. Full numbers and
the inter-role classifier setup are in `paper/Paper.tex` §§5–6.

| Variant | Base model | Adapter paths |
|---------|------------|---------------|
| Standard 3B | Llama-3.2-3B-Instruct-4bit | adapters/3b/{role}/ |
| Standard 1B | Llama-3.2-1B-Instruct-4bit | adapters/1b/{role}/ |
| Fast 3B | Llama-3.2-3B-Instruct-4bit | adapters/fast/3b/{role}/ |
| Fast 1B | Llama-3.2-1B-Instruct-4bit | adapters/fast/1b/{role}/ |
| Qwen Standard/Fast | Qwen2-0.5B-Instruct-4bit | adapters/qwen4bit_standard/{role}/, adapters/fast/qwen4bit/{role}/ |
| SmolLM2 Standard | SmolLM2-360M-Instruct | adapters/smollm2/{role}/ |
| SmolLM2 Fast | SmolLM2-360M-Instruct | adapters/fast/smollm2/{role}/ |
| Qwen2.5-0.5B Standard | Qwen2.5-0.5B-Instruct-4bit | adapters/qwen25_05b_standard/{role}/ |
| Qwen2.5-0.5B Fast | Qwen2.5-0.5B-Instruct-4bit | adapters/fast/qwen25_05b/{role}/ |
| Qwen2.5-1.5B Standard | Qwen2.5-1.5B-Instruct-4bit | adapters/qwen25_15b_standard/{role}/ |
| Qwen2.5-1.5B Fast | Qwen2.5-1.5B-Instruct-4bit | adapters/fast/qwen25_15b/{role}/ |
| Qwen2.5-3B Standard | Qwen2.5-3B-Instruct-4bit | adapters/qwen25_3b_standard/{role}/ |
| Qwen2.5-3B Fast | Qwen2.5-3B-Instruct-4bit | adapters/fast/qwen25_3b/{role}/ |

**Headline metrics (5–11 group; full tables in `paper/Paper.tex` §§5–6 and `docs/RESULTS_COMPARISON.md`):**

| Variant          | FK ≤ 7.0 pass | Avg latency | Classifier acc. |
|------------------|---------------|-------------|-----------------|
| Standard-3B      | 84%           | 2.37 s      | 0.920           |
| Standard-1B      | 72%           | 1.09 s      | 0.890           |
| Fast-3B          | 76%           | 2.83 s      | 0.900           |
| Fast-1B          | 82%           | 0.93 s      | 0.940           |
| Qwen Fast (4bit)      | 68%           | **0.46 s**  | 0.960           |
| Qwen Std (4bit)       | 74%           | 0.59 s      | 0.940           |
| SmolLM2 Standard      | **84%**       | 0.81 s      | 0.950           |
| SmolLM2 Fast          | 64%           | 1.08 s      | 0.920           |
| Qwen2.5-0.5B Fast     | 76%           | **0.46 s**  | 0.950           |
| Qwen2.5-0.5B Standard | 72%           | 0.57 s      | 0.940           |
| Qwen2.5-1.5B Fast     | 70%           | 0.98 s      | **0.980**       |
| Qwen2.5-1.5B Standard | 48%           | 1.31 s      | 0.890           |
| Qwen2.5-3B Fast       | 76%           | 1.89 s      | 0.970           |
| Qwen2.5-3B Standard   | 58%           | 2.23 s      | 0.930           |
| Base-3B               | 12%           | 3.99 s      | 0.700           |
| Base-1B               | 14%           | 2.01 s      | 0.660           |

**Key findings:**
- **Configuration-ordering crossover**: Standard wins on 3B; Fast wins on 1B. Consistent across
  all five readability metrics and the inter-role classifier. Mechanism resolved: rank is
  dominant (rank sweep), depth is a secondary independent contributor (layer sweep).
- **Fast-1B is the deployment recommendation**: only configuration meeting the 1.0s real-time
  latency target for the 5–11 adapter (0.93s avg, 70% under target) while topping the
  classifier and clearing the FK ≤ 7.0 bar.
- **Fast-3B is slower than Standard-3B** despite fewer adapter parameters — rank/layer reduction
  changed output length behaviour (120 vs 92 avg tokens). Tokens/sec is comparable; longer
  responses explain the latency increase.

**Why Llama 1B (not Qwen or other small models) for the original ablation:**
Same family as the 3B base — same tokenizer, same chat template, same `apply_chat_template`
behaviour. Drop-in replacement. Other small models require revalidating the data pipeline.
`docs/EXPERIMENTS.md` §2 documents the completed Qwen 2.5 sweep (0.5B/1.5B/3B, both configs).

### Known Gaps (paper Limitations §)

Status updated after §1 rank sweep and §2 cross-architecture experiments:

- **Confounded comparison — RESOLVED.** A controlled rank sweep (fixed `num_layers=8`,
  ranks 2/4/8/16, 4 models, 2 seeds) confirms **rank** as the dominant variable via capacity
  regularization. A subsequent layer sweep (fixed rank=4, `num_layers ∈ {4, 8, 16}`, Llama
  1B/3B, 2 seeds) confirms depth as an independent secondary contributor: layers=16 beats
  layers=8 by +4–7% FK at fixed rank; small models peak at layers=4. Crossover reflects
  joint rank+depth effect. (`docs/EXPERIMENTS.md` §1.)
- **Single-seed runs — PARTIALLY RESOLVED.** The rank sweep reports mean ± std across 2 seeds.
  The original 8 runs and the cross-architecture evals (Qwen, SmolLM2) still use seed 42 only.
- **Standard adapter perplexity — RESOLVED.** Post-hoc `--test` pass on all 8 Llama adapters. Perplexity crossover corroborates FK crossover: Standard-3B < Fast-3B; Fast-1B < Standard-1B. Paper Table 1 updated. (`docs/EXPERIMENTS.md` §3.)
- **Single model family — RESOLVED.** Qwen 2 0.5B, SmolLM2 360M, and Qwen 2.5 (0.5B/1.5B/3B)
  evaluated; crossover confirmed not Llama-specific. Rank sweep covers all four architectures.
  Qwen 2.5 Fast dominates Standard uniformly across all sizes (no crossover within that family).
  Models above 3B remain untested.

### Forward Roadmap

See `docs/EXPERIMENTS.md` for current status. All of §1 (rank sweep + layer sweep), §2
(SmolLM2, Qwen 2 0.5B, Qwen 2.5 0.5B/1.5B/3B), and §3 (Standard perplexity) are complete.
Remaining work: longer-term items only (human eval, safety eval, dataset quality pass).

