#!/usr/bin/env bash
# Train both role adapters on Qwen2-0.5B 4-bit quantized base (QLoRA).
# Do NOT run simultaneously with other training jobs — GPU OOM on M4 16GB.
set -e
source .venv/bin/activate
mlx_lm.lora --config configs/age_5_11_qwen4bit_lora.yaml 2>&1 | tee logs/age_5_11_qwen4bit.log
mlx_lm.lora --config configs/age_12_18_qwen4bit_lora.yaml 2>&1 | tee logs/age_12_18_qwen4bit.log
echo "Qwen (4-bit) adapters trained."
