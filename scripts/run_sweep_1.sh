#!/usr/bin/env bash
# Run all Experiment §1 rank-sweep configs sequentially.
# GPU can only run one training at a time on M4 16GB.
# Generates configs first if configs/sweeps/ is empty.
#
# Usage: bash scripts/run_sweep_1.sh
set -e

SWEEP_DIR="configs/sweeps"

if [ -z "$(ls -A "$SWEEP_DIR" 2>/dev/null)" ]; then
    echo "No sweep configs found — generating..."
    python scripts/gen_sweep_configs.py
fi

source .venv/bin/activate
mkdir -p logs

CONFIGS=$(ls "$SWEEP_DIR"/rank*.yaml | sort)
TOTAL=$(echo "$CONFIGS" | wc -l | tr -d ' ')
N=0

for cfg in $CONFIGS; do
    N=$((N + 1))
    NAME=$(basename "$cfg" .yaml)
    echo ""
    echo "[$N/$TOTAL] $NAME"
    mlx_lm.lora --config "$cfg" 2>&1 | tee "logs/${NAME}.log"
    echo "[$N/$TOTAL] Done: $NAME"
done

echo ""
echo "All $TOTAL sweep runs complete."
