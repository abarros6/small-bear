# Dr. Beary Good

A role-adaptive LLM for a VR pediatric hospital guide at Victoria Hospital, London ON.
Serves two pediatric age groups via LoRA adapters on a shared quantized base model.
Adapters are trained and evaluated without a system prompt — the communication register
is encoded in the weights, not in prompt engineering.

## Roles

| Role | Age group | FK target |
|------|-----------|-----------|
| `age_5_11` | Ages 5–11 | ≤ 7.0 |
| `age_12_18` | Ages 12–18 | measured, no ceiling |

## Paper & Findings

The full write-up is at `paper/Paper.tex`. Two adapter configurations were trained across two
model sizes (8 runs total): **Standard** (`rank=8`, `num_layers=16`) and **Fast**
(`rank=4`, `num_layers=8`).

Headline result: a **configuration-ordering crossover** — Standard wins on 3B, Fast wins on 1B,
consistent across all five readability metrics and the inter-role classifier. Mechanism is
unresolved (rank and layer count co-vary). **Fast-1B is the deployment recommendation**: the
only configuration meeting the 1.0 s real-time latency target for the 5–11 adapter (0.93 s avg)
while topping the inter-role classifier (0.940 accuracy).

See `docs/EXPERIMENTS.md` for the planned follow-up to identify the crossover mechanism and test
whether it generalizes to other model families.

## Stack

- Base model (primary): `mlx-community/Llama-3.2-3B-Instruct-4bit`
- Base model (ablation): `mlx-community/Llama-3.2-1B-Instruct-4bit`
- Framework: MLX (Apple Silicon)
- Method: QLoRA — 4-bit quantized base + float32 LoRA adapters
- Hardware: Mac Mini M4, 16 GB unified RAM

## Hyperparameters

All four configs use identical values — the ablation is only valid if every variable other
than the base model is held constant. Inline comments in the YAML files explain each setting.

### LoRA (training)

Two adapter configurations exist. All other hyperparameters are identical between them.

| Parameter | Standard | Fast (current configs) | Why |
|-----------|----------|------------------------|-----|
| `num_layers` | 16 | 8 | Standard adapts upper 57% of 3B (all of 1B). Fast halves this — style signal lives in the top layers; results confirmed comparable separation at half the layers. |
| `rank` | 8 | 4 | Standard is the mlx-lm default for ~500 examples. Fast halves adapter parameter count — register is a simple style shift, not knowledge acquisition, so rank 4 is sufficient. |
| `scale` | 20.0 | 20.0 | Multiplier on adapter output. mlx-lm default. **Do not compute as alpha/rank** — that gives 1.0 and effectively disables the adapter. |
| `dropout` | 0.0 | 0.0 | No regularisation. Dataset is small and high-quality (LIMA-style), so dropout adds noise with no benefit. |

### Training schedule

| Parameter | Value | Why |
|-----------|-------|-----|
| `batch_size` | 4 | Memory ceiling on M4 16 GB with 3B 4-bit model at seq_length=768. |
| `iters` | 600 | ~5 passes over ~475 examples. Validation loss curves determined this range — fewer steps leave style weak; more cause overfitting. |
| `learning_rate` | 1e-5 | mlx-lm validated default for QLoRA on Llama 3.2. Higher causes loss spikes/NaN; lower doesn't converge in 600 steps. |
| `lr_schedule` | cosine_decay + 100-step warmup | Warmup stabilises early training when gradients are noisiest. Cosine decay smoothly reduces step size toward the end of training. |
| `mask_prompt` | true | Loss computed only on assistant tokens — the model learns to generate responses, not predict questions. Without this, style adaptation is diluted. |
| `max_seq_length` | 768 | ~550 words; all Q&A pairs fit. Attention cost scales quadratically, so this is set to the minimum safe ceiling. |
| `seed` | 42 | Fixed for reproducibility. Change to verify result stability across seeds. |

### Inference

| Parameter | Value | Why |
|-----------|-------|-----|
| `temperature` | 0.0 (default) | Greedy decoding — deterministic, no randomness. Correct for a pediatric medical context where consistency and safety matter. Raise to ~0.3 for natural variation. |
| `top_p` | 1.0 (default) | Nucleus sampling disabled; irrelevant at temperature=0. |
| `top_k` | 0 (default) | Top-k sampling disabled; irrelevant at temperature=0. |
| `repetition_penalty` | 1.0 (default) | No repetition penalty. Raise to 1.1–1.3 if greedy decoding produces looping responses on long outputs. |
| `max_tokens` | 300 | ~200–250 words. EOS fires before this on well-trained adapters. Decrease for lower latency in VR; increase if responses are truncated. |

See `CLAUDE.md` for full rationale on every parameter.

## Quick Start

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
bash scripts/setup.sh

# Drop source JSONL files into data/source/, then:
python src/prepare_data.py

# Train Fast adapters (current configs: rank=4, num_layers=8 → adapters/fast/{size}/):
# 3B primary first, then 1B ablation. Do not run simultaneously — GPU OOM on M4 16 GB.
# To train Standard adapters (rank=8, num_layers=16 → adapters/{size}/), edit the YAMLs
# and re-run; see CLAUDE.md "Hyperparameters & Inference Settings".
bash scripts/train_3b.sh
bash scripts/train_1b.sh

# Inference (no system prompt — matches training)
python src/inference.py --role age_5_11 --query "Will the X-ray hurt?"
python src/inference.py --role age_12_18 --query "Will the X-ray hurt?"
python src/inference.py --benchmark

# Fast variant inference
python src/inference.py --role age_5_11 --variant fast --query "Will the X-ray hurt?"

# Base model comparison (no adapter)
python src/inference.py --base --query "Will the X-ray hurt?"

# With system prompt (VR deployment context)
python src/inference.py --role age_5_11 --query "Will the X-ray hurt?" \
    --system-prompt "You are Dr. Beary Good at Victoria Hospital."
```

See `docs/COMMANDS.md` for the full reproduction sequence from clone to evaluated results.

## Evaluation

```bash
# Training data quality
cat data/source/train/*.jsonl > /tmp/all_train.jsonl
python src/evaluate.py --data /tmp/all_train.jsonl

# Generate outputs — run one at a time (GPU OOM if concurrent)
python src/generate_outputs.py                             # standard 3B
python src/generate_outputs.py --model-size 1b            # standard 1B
python src/generate_outputs.py --variant fast             # fast 3B
python src/generate_outputs.py --variant fast --model-size 1b  # fast 1B
python src/generate_outputs.py --base                     # base 3B (no adapter)
python src/generate_outputs.py --base --model-size 1b    # base 1B

# Evaluate — all metrics, save to results/
python src/evaluate.py --data outputs/all_3b_outputs.jsonl --latency --separation --output results/standard_3b_eval.txt
python src/evaluate.py --data outputs/all_1b_outputs.jsonl --latency --separation --output results/standard_1b_eval.txt
python src/evaluate.py --data outputs/all_fast_3b_outputs.jsonl --latency --separation --output results/fast_3b_eval.txt
python src/evaluate.py --data outputs/all_fast_1b_outputs.jsonl --latency --separation --output results/fast_1b_eval.txt
python src/evaluate.py --data outputs/all_base_3b_outputs.jsonl --latency --separation --output results/base_3b_eval.txt
python src/evaluate.py --data outputs/all_base_1b_outputs.jsonl --latency --separation --output results/base_1b_eval.txt
```

### Evaluation Metrics

| Metric | Description |
|--------|-------------|
| Flesch-Kincaid Grade | Primary readability target — age_5_11 must stay ≤ 7.0 |
| SMOG | Readability designed for health text; more sensitive to medical vocabulary than FK |
| Gunning Fog | Penalises polysyllabic words; complements FK |
| Coleman-Liau | Character-based grade level; cross-check for FK/SMOG |
| Lexical Diversity (TTR) | Unique words / total words — lower expected for age_5_11 |
| Tokens/second | Generation throughput — key VR deployment metric |
| Inter-role classifier | TF-IDF + LR accuracy distinguishing roles — high score = strong style separation |

## Project Structure

See `CLAUDE.md` for full project context, command reference, and lessons learned.
