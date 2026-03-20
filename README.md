# Dr. Beary Good

A role-adaptive LLM for a VR pediatric hospital guide at Victoria Hospital, London ON.
Serves two pediatric age groups via LoRA adapters on a shared quantized base model.
Adapters are trained and evaluated without a system prompt — the communication register
is encoded in the weights, not in prompt engineering.

**ECE9660 Final Project — Western University, Winter 2026**

## Roles

| Role | Age group | FK target |
|------|-----------|-----------|
| `age_5_11` | Ages 5–11 | ≤ 7.0 |
| `age_12_18` | Ages 12–18 | measured, no ceiling |

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

| Parameter | Value | Why |
|-----------|-------|-----|
| `num_layers` | 16 | Adapts the upper 57% of the 3B model's 28 layers (all 16 of the 1B). Upper layers carry stylistic/semantic decisions — the highest-value target for register adaptation. |
| `rank` | 8 | Dimensionality of the adapter's low-rank matrices. mlx-lm default; right-sized for ~500 training examples. Too low → insufficient style capacity; too high → overfitting. |
| `scale` | 20.0 | Multiplier on the adapter output before adding to the base layer. mlx-lm default. **Do not compute as alpha/rank** — that convention gives 1.0 and effectively disables the adapter. |
| `dropout` | 0.0 | No regularisation. Dataset is small and high-quality (LIMA-style), so dropout adds noise with no benefit. Raise to 0.05–0.1 only if validation loss diverges. |

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

# Train (3B primary, then 1B ablation):
bash scripts/train_3b.sh
bash scripts/train_1b.sh

# Inference (no system prompt — matches training)
python src/inference.py --role age_5_11 --query "Will the X-ray hurt?"
python src/inference.py --role age_12_18 --query "Will the X-ray hurt?"
python src/inference.py --benchmark

# With system prompt (VR deployment context)
python src/inference.py --role age_5_11 --query "Will the X-ray hurt?" \
    --system-prompt "You are Dr. Beary Good at Victoria Hospital."
```

## Evaluation

```bash
# Training data quality
cat data/source/train/*.jsonl > /tmp/all_train.jsonl
python src/evaluate.py --data /tmp/all_train.jsonl

# Model output quality (after training)
python src/generate_outputs.py
python src/evaluate.py --data outputs/all_3b_outputs.jsonl --latency
```

## Project Structure

See `CLAUDE.md` for full project context, command reference, and lessons learned.
