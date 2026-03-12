#!/usr/bin/env bash
# Train both role adapters on the 3B base model (primary experiment).
set -e
source .venv/bin/activate
mlx_lm.lora --config configs/age_5_11_3b_lora.yaml 2>&1 | tee logs/age_5_11_3b.log
mlx_lm.lora --config configs/age_12_18_3b_lora.yaml 2>&1 | tee logs/age_12_18_3b.log
echo "3B adapters trained."
