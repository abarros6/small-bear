#!/usr/bin/env bash
# Generic train -> generate -> evaluate runner for a directory of configs.
# Usage: bash scripts/run_generic_batch.sh <configs_dir> <outputs_dir> <logs_dir> <role> <model_size_field>
#   model_size_field: "auto" to parse from filename (rank{r}_layers{n}_seed{s}_{model}),
#                      or a literal model-size string if all configs in the dir share one
#                      (e.g. crossarch configs mix models, so use "auto" with a name->model map file)
set -uo pipefail

CONFIGS_DIR="$1"
OUTPUTS_DIR="$2"
LOGS_DIR="$3"
ROLE="$4"
MODEL_MAP="${5:-}"   # optional: path to a "name model_size" mapping file for non-standard names

hr() { printf '\n%.0s-' {1..70}; echo; }
log() { echo "  $*"; }

source .venv/bin/activate
mkdir -p "$OUTPUTS_DIR" "$LOGS_DIR"

CONFIGS=($(ls "$CONFIGS_DIR"/*.yaml | sort))
TOTAL=${#CONFIGS[@]}
echo "Batch: $CONFIGS_DIR ($TOTAL configs, role=$ROLE)"
hr

N=0
for cfg in "${CONFIGS[@]}"; do
    N=$((N + 1))
    NAME=$(basename "$cfg" .yaml)

    if [ -n "$MODEL_MAP" ] && [ -f "$MODEL_MAP" ]; then
        MODEL_SIZE=$(grep "^${NAME} " "$MODEL_MAP" | awk '{print $2}')
    else
        MODEL_SIZE=$(echo "$NAME" | cut -d_ -f4-)
    fi

    ADAPTER_PATH=$(grep "^adapter_path:" "$cfg" | sed -E 's/adapter_path: *"([^"]+)"/\1/')
    OUTPUT_FILE="$OUTPUTS_DIR/${NAME}_${ROLE}_outputs.jsonl"

    echo ""
    echo "[$N/$TOTAL] $NAME (model=$MODEL_SIZE, adapter=$ADAPTER_PATH)"

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
            --output-tag   "$(basename $OUTPUTS_DIR)/$NAME" \
            > "$LOGS_DIR/${NAME}_generate.log" 2>&1
    fi

    if [ ! -f "$OUTPUT_FILE" ]; then
        log "GENERATE FAILED -- no output, skipping eval"
        continue
    fi

    RESULT_FILE="$LOGS_DIR/${NAME}_eval.txt"
    if [ -f "$RESULT_FILE" ]; then
        log "SKIP evaluate"
    else
        log "EVALUATE"
        python src/evaluate.py --data "$OUTPUT_FILE" --latency --output "$RESULT_FILE" 2>&1 | tail -3
    fi
done

hr
echo "Batch complete: $CONFIGS_DIR"
