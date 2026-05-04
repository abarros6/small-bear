#!/usr/bin/env bash
# Train both role adapters on Qwen2-0.5B bfloat16, standard config (rank 8, 16 layers).
# Do NOT run simultaneously with other training jobs — GPU OOM on M4 16GB.
set -e
source .venv/bin/activate
mlx_lm.lora --config configs/age_5_11_qwen_standard_lora.yaml 2>&1 | tee logs/age_5_11_qwen_standard.log
mlx_lm.lora --config configs/age_12_18_qwen_standard_lora.yaml 2>&1 | tee logs/age_12_18_qwen_standard.log
echo "Qwen standard (bfloat16) adapters trained."
