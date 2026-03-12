#!/usr/bin/env bash
# Train both role adapters on the 1B base model (ablation study).
set -e
source .venv/bin/activate
mlx_lm.lora --config configs/age_5_11_1b_lora.yaml 2>&1 | tee logs/age_5_11_1b.log
mlx_lm.lora --config configs/age_12_18_1b_lora.yaml 2>&1 | tee logs/age_12_18_1b.log
echo "1B adapters trained."
