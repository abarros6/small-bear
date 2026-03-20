# Dr. Beary Good — Project Context

## What This Is

ECE9660 final project (Western University, Winter 2026). A role-adaptive LLM ("Dr. Beary Good")
for a VR pediatric hospital guide at Victoria Hospital, London ON. The system serves two
pediatric age groups — ages 5–11 and ages 12–18 — by switching between two LoRA adapters
trained on a purpose-built dataset. An ablation study compares 3B vs. 1B parameter base models.

**Project category**: Model Training & Alignment + Safety, Bias & Responsible AI

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

## Hardware & Stack

| Component | Detail |
|-----------|--------|
| Hardware | Mac Mini M4, 16 GB unified RAM |
| Python | 3.12 (Homebrew `/opt/homebrew/bin/python3.12`) |
| Framework | MLX (Apple Silicon, on-device GPU) |
| Base model (primary) | `mlx-community/Llama-3.2-3B-Instruct-4bit` |
| Base model (ablation) | `mlx-community/Llama-3.2-1B-Instruct-4bit` |
| Method | QLoRA — 4-bit quantized base, float32 LoRA adapters |
| mlx-lm | 0.30.7 (pinned — see Known Working Versions) |

## Project Structure

```
dr-beary-good-v2/
├── .gitignore
├── CLAUDE.md                               # This file
├── README.md                               # GitHub-facing docs
├── requirements.txt                        # Pinned to known working versions
├── configs/
│   ├── age_5_11_3b_lora.yaml
│   ├── age_12_18_3b_lora.yaml
│   ├── age_5_11_1b_lora.yaml
│   └── age_12_18_1b_lora.yaml
├── data/
│   ├── source/
│   │   ├── train/                          # One JSONL per category — training examples
│   │   └── validate/                       # One JSONL per category — hand-curated validation
│   ├── age_5_11/                           # train.jsonl + valid.jsonl (from prepare_data.py)
│   └── age_12_18/
├── adapters/                               # .gitignored — large binary LoRA weights
│   ├── 3b/
│   │   ├── age_5_11/
│   │   └── age_12_18/
│   └── 1b/
│       ├── age_5_11/
│       └── age_12_18/
├── outputs/                                # .gitignored — model-generated responses
├── logs/                                   # .gitignored — training logs
├── scripts/
│   ├── setup.sh                            # mkdir -p all required directories
│   ├── train_3b.sh                         # sequential training of both adapters on 3B
│   └── train_1b.sh                         # sequential training of both adapters on 1B
└── src/
    ├── constants.py                        # ROLES, BASE_MODEL_3B, BASE_MODEL_1B (no system prompts)
    ├── prepare_data.py                     # Source JSONL → per-role train/valid splits (no sys prompt)
    ├── evaluate.py                         # FK grade, safety (role-scoped), latency evaluation
    ├── inference.py                        # Explicit-role inference (adapter + optional sys prompt)
    └── generate_outputs.py                 # Run inference on valid set → outputs/ for evaluation
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

### Category Targets (100 examples each)
| Role | Category (exact string in JSONL) | Target |
|------|----------------------------------|--------|
| age_5_11 | what_to_expect | 100 |
| age_5_11 | who_are_these_people | 100 |
| age_5_11 | hospital_rules_and_routines | 100 |
| age_5_11 | emotional_reassurance | 100 |
| age_5_11 | faqs_general_curiosity | 100 |
| age_12_18 | what_to_expect | 100 |
| age_12_18 | who_are_these_people | 100 |
| age_12_18 | hospital_rules_and_routines | 100 |
| age_12_18 | emotional_reassurance | 100 |
| age_12_18 | faqs_general_curiosity | 100 |

Total: 1000 examples (500 per role)

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

### LoRA Architecture

**`num_layers: 16`**
How many transformer layers (counted from the top) receive LoRA adapter matrices.
The 3B model has 28 layers total — `num_layers: 16` adapts the upper 57%.
The 1B model has 16 layers total — `num_layers: 16` adapts all of them.
Upper layers handle high-level semantic and stylistic decisions, making them the
highest-value target for register adaptation. Lower layers handle token-level
representations and are left untouched (shared base behaviour is preserved there).
Increasing this on the 3B would provide more capacity but increase training memory and
risk overwriting general-purpose knowledge in the lower layers.

**`lora_parameters.rank: 8`**
The rank of the two low-rank matrices A and B inserted into each adapted layer
(the adapter's weight delta is `scale * A @ B^T`). Trainable parameters per adapted
layer ≈ `2 * rank * hidden_dim`. Rank 8 is the mlx-lm validated default and appropriate
for datasets of ~500 examples. Too low (rank 4) risks insufficient expressiveness — the
adapter may not have enough capacity to encode the full register shift. Too high
(rank 16–64) risks overfitting on this small dataset and exceeds the M4 memory budget
during training. The LIMA hypothesis suggests that data quality, not model capacity,
drives style adaptation — so rank 8 is the right tradeoff here.

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
# Primary (3B base model):
bash scripts/train_3b.sh               # trains age_5_11 and age_12_18 adapters on 3B

# Ablation (1B base model):
bash scripts/train_1b.sh               # trains age_5_11 and age_12_18 adapters on 1B

# Or individually:
mlx_lm.lora --config configs/age_5_11_3b_lora.yaml 2>&1 | tee logs/age_5_11_3b.log
mlx_lm.lora --config configs/age_12_18_3b_lora.yaml 2>&1 | tee logs/age_12_18_3b.log
mlx_lm.lora --config configs/age_5_11_1b_lora.yaml 2>&1 | tee logs/age_5_11_1b.log
mlx_lm.lora --config configs/age_12_18_1b_lora.yaml 2>&1 | tee logs/age_12_18_1b.log

# --- INFERENCE (no system prompt — matches training conditions) ---
python src/inference.py --role age_5_11 --query "Will the X-ray hurt?"
python src/inference.py --role age_12_18 --query "Will the X-ray hurt?"

# 1B ablation:
python src/inference.py --role age_5_11 --model-size 1b --query "Will the X-ray hurt?"

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

# Generate model outputs from the validation set (run AFTER training)
python src/generate_outputs.py                      # 3B adapters, both roles
python src/generate_outputs.py --model-size 1b      # 1B ablation

# Evaluate model outputs
python src/evaluate.py --data outputs/all_3b_outputs.jsonl --latency
python src/evaluate.py --data outputs/all_1b_outputs.jsonl --latency
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
```

## Ablation Study: 3B vs. 1B

Both roles are trained on both base models using identical hyperparameters and data.

| Experiment | Base model | Adapter paths | Config files |
|------------|------------|---------------|--------------|
| Primary | Llama-3.2-3B-Instruct-4bit | adapters/3b/{role}/ | *_3b_lora.yaml |
| Ablation | Llama-3.2-1B-Instruct-4bit | adapters/1b/{role}/ | *_1b_lora.yaml |

**Expected tradeoffs:**
- 1B: ~2× latency improvement; age_5_11 likely fine; age_12_18 more nuanced language may degrade
- Evaluation metrics to compare: FK grade, safety pass rate, latency, qualitative output quality

**Why Llama 1B (not Qwen or other small models):**
Same family as the 3B base — same tokenizer, same chat template, same `apply_chat_template`
behaviour. Drop-in replacement. Other small models require revalidating the entire data pipeline.

## Academic Context

- **Report due**: April 14, 2026 (IEEE Transactions format, 6-page double-column + appendix)
- **Presentation**: March 26, 2026 slides submission; present March 27 or April 10, 2026
- **Appendix must include**: GitHub link, member contributions, all Claude chat transcripts
- **Save ALL Claude conversation logs** as .txt — required for submission
- **Grading**: Report 30% + Code repo 3% + Presentation 15% + Proposal 2% = 50% of grade
