#!/usr/bin/env bash
# Experiment §1 v2 — rank sweep retrain on the current (post-quality-pass) dataset vintage.
# Same as run_exp1.sh but reads configs/sweeps_v2 (identical hyperparameters, new adapter
# paths) so the original old-vintage results in adapters/sweeps and results/sweeps are
# preserved for provenance while this produces a vintage-consistent replacement.
#
# Runs all 32 configs (4 ranks × 4 models × 2 seeds) sequentially.
# Safe to interrupt and re-run: each step is skipped if its output already exists.
set -uo pipefail

CONFIGS_DIR="configs/sweeps_v2"
ADAPTERS_DIR="adapters/sweeps_v2"
OUTPUTS_DIR="outputs/sweeps_v2"
RESULTS_DIR="results/sweeps_v2"
LOGS_DIR="logs/sweeps_v2"
ROLE="age_5_11"

hr() { printf '\n%.0s-' {1..70}; echo; }
log() { echo "  $*"; }

source .venv/bin/activate
mkdir -p "$ADAPTERS_DIR" "$OUTPUTS_DIR" "$RESULTS_DIR" "$LOGS_DIR"

CONFIGS=($(ls "$CONFIGS_DIR"/rank*.yaml | sort))
TOTAL=${#CONFIGS[@]}

echo "Experiment §1 v2 — Rank Sweep (current dataset vintage)"
echo "  Configs : $TOTAL | Role: $ROLE"
hr

N=0
for cfg in "${CONFIGS[@]}"; do
    N=$((N + 1))
    NAME=$(basename "$cfg" .yaml)
    MODEL_SIZE=$(echo "$NAME" | cut -d_ -f4-)

    ADAPTER_PATH="$ADAPTERS_DIR/${NAME}_${ROLE}"
    OUTPUT_FILE="$OUTPUTS_DIR/${NAME}_${ROLE}_outputs.jsonl"
    RESULT_FILE="$RESULTS_DIR/${NAME}.txt"

    echo ""
    echo "[$N/$TOTAL] $NAME (model=$MODEL_SIZE)"

    if [ -f "$ADAPTER_PATH/adapter_config.json" ]; then
        log "SKIP train"
    else
        log "TRAIN"
        mkdir -p "$ADAPTER_PATH"
        mlx_lm.lora --config "$cfg" > "$LOGS_DIR/${NAME}.log" 2>&1
        if [ $? -ne 0 ]; then
            log "TRAIN FAILED -- see $LOGS_DIR/${NAME}.log, skipping"
            continue
        fi
    fi

    if [ -f "$OUTPUT_FILE" ]; then
        log "SKIP generate"
    else
        log "GENERATE"
        python src/generate_outputs.py \
            --model-size "$MODEL_SIZE" \
            --role       "$ROLE" \
            --adapter-path "$ADAPTER_PATH" \
            --output-tag   "sweeps_v2/$NAME" \
            > "$LOGS_DIR/${NAME}_generate.log" 2>&1
    fi

    if [ ! -f "$OUTPUT_FILE" ]; then
        log "GENERATE FAILED -- no output, skipping eval"
        continue
    fi

    if [ -f "$RESULT_FILE" ]; then
        log "SKIP evaluate"
    else
        log "EVALUATE"
        python src/evaluate.py --data "$OUTPUT_FILE" --latency --output "$RESULT_FILE" \
            > "$LOGS_DIR/${NAME}_eval.log" 2>&1
    fi
done

hr
echo "Rank sweep v2 complete. Results: $RESULTS_DIR/"
