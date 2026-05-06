#!/bin/bash
# Train SmolLM2-360M Standard and Fast adapters sequentially.
# Do NOT run concurrently with other training — GPU OOM on M4 16 GB.
#
# Prerequisite: generate SmolLM2-specific training data first:
#   python src/prepare_data.py --data-dir data/smollm --add-empty-system
#
# Standard adapters → adapters/smollm2/{role}/
# Fast adapters     → adapters/fast/smollm2/{role}/

set -e

mkdir -p adapters/smollm2/age_5_11 adapters/smollm2/age_12_18
mkdir -p adapters/fast/smollm2/age_5_11 adapters/fast/smollm2/age_12_18
mkdir -p logs

echo "=== SmolLM2 Standard — age_5_11 ==="
mlx_lm.lora --config configs/smollm2_standard_age_5_11_lora.yaml 2>&1 | tee logs/smollm2_standard_age_5_11.log

echo "=== SmolLM2 Standard — age_12_18 ==="
mlx_lm.lora --config configs/smollm2_standard_age_12_18_lora.yaml 2>&1 | tee logs/smollm2_standard_age_12_18.log

echo "=== SmolLM2 Fast — age_5_11 ==="
mlx_lm.lora --config configs/smollm2_fast_age_5_11_lora.yaml 2>&1 | tee logs/smollm2_fast_age_5_11.log

echo "=== SmolLM2 Fast — age_12_18 ==="
mlx_lm.lora --config configs/smollm2_fast_age_12_18_lora.yaml 2>&1 | tee logs/smollm2_fast_age_12_18.log

echo "=== All SmolLM2 training complete ==="
