#!/usr/bin/env bash
# Train a single sweep config.
# Usage: bash scripts/train_sweep.sh configs/sweeps/rank4_layers8_seed42_1b.yaml
set -e
CONFIG="${1:?Usage: bash scripts/train_sweep.sh <config_path>}"
NAME=$(basename "$CONFIG" .yaml)
source .venv/bin/activate
mkdir -p logs
mlx_lm.lora --config "$CONFIG" 2>&1 | tee "logs/${NAME}.log"
echo "Done: $NAME"
