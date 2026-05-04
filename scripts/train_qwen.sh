#!/usr/bin/env bash
# Train both role adapters on Qwen2-0.5B bfloat16 base (standard LoRA).
# Do NOT run simultaneously with other training jobs — GPU OOM on M4 16GB.
set -e
source .venv/bin/activate
mlx_lm.lora --config configs/age_5_11_qwen_lora.yaml 2>&1 | tee logs/age_5_11_qwen.log
mlx_lm.lora --config configs/age_12_18_qwen_lora.yaml 2>&1 | tee logs/age_12_18_qwen.log
echo "Qwen (bfloat16) adapters trained."
