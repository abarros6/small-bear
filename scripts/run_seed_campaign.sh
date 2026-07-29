#!/usr/bin/env bash
# Seed campaign: train -> generate -> evaluate for all 80 configs in
# configs/seed_campaign/, logging FK<=7.0 pass rate to results/seed_campaign/summary.csv.
#
# Resumable: skips training if the adapter already exists, skips generation if the
# output file already exists, skips evaluation if already logged in the CSV.
#
# Usage: bash scripts/run_seed_campaign.sh
set -uo pipefail

CONFIGS_DIR="configs/seed_campaign"
OUTPUTS_DIR="outputs/seed_campaign"
RESULTS_DIR="results/seed_campaign"
LOGS_DIR="logs/seed_campaign"
ROLE="age_5_11"
SUMMARY_CSV="$RESULTS_DIR/summary.csv"

mkdir -p "$OUTPUTS_DIR" "$RESULTS_DIR" "$LOGS_DIR"
source .venv/bin/activate

if [ ! -f "$SUMMARY_CSV" ]; then
    echo "config,model,seed,fk_pass_rate,fk_pass_n,fk_avg" > "$SUMMARY_CSV"
fi

hr() { printf '\n%.0s-' {1..70}; echo; }

CONFIGS=($(ls "$CONFIGS_DIR"/*.yaml | sort))
TOTAL=${#CONFIGS[@]}
N=0

for cfg in "${CONFIGS[@]}"; do
    N=$((N + 1))
    NAME=$(basename "$cfg" .yaml)

    # already logged? skip entirely
    if grep -q "^${NAME}," "$SUMMARY_CSV" 2>/dev/null; then
        continue
    fi

    ADAPTER_PATH="adapters/seed_campaign/${NAME}_${ROLE}"
    OUTPUT_FILE="$OUTPUTS_DIR/${NAME}_${ROLE}_outputs.jsonl"

    # parse model size from name: {config}_{model}_seed{seed}
    MODEL_SIZE=$(echo "$NAME" | sed -E 's/^(standard|fast)_([0-9a-z]+)_seed[0-9]+$/\2/')

    hr
    echo "[$N/$TOTAL] $NAME (model=$MODEL_SIZE)"

    if [ -f "$ADAPTER_PATH/adapter_config.json" ]; then
        echo "  SKIP train — adapter exists"
    else
        echo "  TRAIN"
        mkdir -p "$ADAPTER_PATH"
        mlx_lm.lora --config "$cfg" > "$LOGS_DIR/${NAME}.log" 2>&1
        if [ $? -ne 0 ]; then
            echo "  TRAIN FAILED — see $LOGS_DIR/${NAME}.log, skipping to next config"
            continue
        fi
    fi

    if [ -f "$OUTPUT_FILE" ]; then
        echo "  SKIP generate — outputs exist"
    else
        echo "  GENERATE"
        python src/generate_outputs.py \
            --model-size "$MODEL_SIZE" \
            --role       "$ROLE" \
            --adapter-path "$ADAPTER_PATH" \
            --output-tag   "seed_campaign/$NAME" \
            > "$LOGS_DIR/${NAME}_generate.log" 2>&1
    fi

    if [ ! -f "$OUTPUT_FILE" ]; then
        echo "  GENERATE FAILED — no output file, skipping eval"
        continue
    fi

    echo "  EVALUATE"
    EVAL_TXT=$(python src/evaluate.py --data "$OUTPUT_FILE" 2>&1)
    FK_LINE=$(echo "$EVAL_TXT" | grep "FK <= 7.0 target" | head -1)
    FK_N=$(echo "$FK_LINE" | grep -oE '[0-9]+/50' | head -1)
    FK_PCT=$(echo "$FK_LINE" | grep -oE '\([0-9.]+%\)' | tr -d '(%)')
    FK_AVG=$(echo "$EVAL_TXT" | grep "FK grade" | head -1 | grep -oE 'avg: [0-9.]+' | grep -oE '[0-9.]+')
    SEED=$(echo "$NAME" | grep -oE 'seed[0-9]+' | grep -oE '[0-9]+')
    if [ -z "$FK_PCT" ]; then
        echo "  EVAL PARSE FAILED — raw output saved to $LOGS_DIR/${NAME}_eval.log"
        echo "$EVAL_TXT" > "$LOGS_DIR/${NAME}_eval.log"
        continue
    fi
    echo "${NAME},${MODEL_SIZE},${SEED},${FK_PCT},${FK_N},${FK_AVG}" >> "$SUMMARY_CSV"
    echo "  LOGGED: FK<=7.0 = ${FK_PCT}% (${FK_N})"
done

hr
echo "Seed campaign pass complete. Results: $SUMMARY_CSV"
