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
