#!/usr/bin/env bash
# Layer sweep — full pipeline: train → generate → evaluate → summarize.
#
# Experiment §1 optional depth: fixed rank=4, num_layers ∈ {4, 8, 16},
# Llama 1B and 3B, two seeds → 12 total runs (8 new, 4 reused from rank sweep).
#
# num_layers=8 configs point at existing rank sweep adapters — training is
# skipped automatically for those 4 runs. New training: 8 runs × ~45 min = ~6h.
#
# Resumable: each step is skipped if its output already exists.
# Interrupt with Ctrl-C and re-run to continue from where it stopped.
#
# Usage:
#   bash scripts/run_layer_sweep.sh
#   bash scripts/run_layer_sweep.sh --summary-only

set -euo pipefail

CONFIGS_DIR="configs/layer_sweep"
RESULTS_DIR="results/layer_sweep"
OUTPUTS_DIR="outputs"
LOGS_DIR="logs"
ROLE="age_5_11"

# ── helpers ──────────────────────────────────────────────────────────────────

hr() { printf '\n%.0s━' {1..70}; echo; }
log() { echo "  $*"; }

# ── summary-only mode ────────────────────────────────────────────────────────

if [[ "${1:-}" == "--summary-only" ]]; then
    source .venv/bin/activate
    python scripts/summarize_layer_sweep.py --output "$RESULTS_DIR/summary.md"
    exit 0
fi

# ── prerequisites ─────────────────────────────────────────────────────────────

source .venv/bin/activate
mkdir -p "$RESULTS_DIR" "$LOGS_DIR" "adapters/layer_sweep"

# Generate configs if the directory is empty
if [ -z "$(ls -A "$CONFIGS_DIR" 2>/dev/null)" ]; then
    echo "Generating layer sweep configs..."
    python scripts/gen_layer_sweep_configs.py
fi

CONFIGS=($(ls "$CONFIGS_DIR"/rank4_layers*.yaml | sort))
TOTAL=${#CONFIGS[@]}

echo ""
echo "Layer Sweep — rank=4 fixed, num_layers ∈ {4, 8, 16}"
echo "  Models  : Llama 1B, Llama 3B"
echo "  Seeds   : 42, 1337"
echo "  Configs : $TOTAL  (num_layers=8 reuses rank sweep adapters — no new training)"
echo "  Steps   : train → generate → evaluate → summarize"
echo ""
echo "Resumable: steps are skipped if their output already exists."
hr

N=0
for cfg in "${CONFIGS[@]}"; do
    N=$((N + 1))
    NAME=$(basename "$cfg" .yaml)   # e.g. rank4_layers8_seed42_1b

    # Parse fields from name: rank4_layers{n}_seed{s}_{model}
    MODEL_SIZE=$(echo "$NAME" | cut -d_ -f4)   # 1b or 3b
    NUM_LAYERS=$(echo "$NAME" | grep -oE 'layers[0-9]+' | grep -oE '[0-9]+')

    # Adapter path mirrors what the YAML specifies:
    #   layers=8  → adapters/sweeps/...   (existing rank sweep adapter)
    #   otherwise → adapters/layer_sweep/...
    if [ "$NUM_LAYERS" = "8" ]; then
        ADAPTER_PATH="adapters/sweeps/${NAME}_${ROLE}"
    else
        ADAPTER_PATH="adapters/layer_sweep/${NAME}_${ROLE}"
    fi

    OUTPUT_TAG="layer_sweep_${NAME}"
    OUTPUT_FILE="$OUTPUTS_DIR/${OUTPUT_TAG}_${ROLE}_outputs.jsonl"
    RESULT_FILE="$RESULTS_DIR/${NAME}.txt"

    echo ""
    echo "[$N/$TOTAL] $NAME  (layers=$NUM_LAYERS, model=$MODEL_SIZE)"
    hr

    # ── 1. Train ─────────────────────────────────────────────────────────────
    if [ -f "$ADAPTER_PATH/adapter_config.json" ]; then
        log "SKIP train — adapter exists: $ADAPTER_PATH"
    else
        log "TRAIN → $ADAPTER_PATH"
        mkdir -p "$ADAPTER_PATH"
        mlx_lm.lora --config "$cfg" 2>&1 | tee "$LOGS_DIR/${NAME}.log"
        log "DONE  train"
    fi

    # ── 2. Generate outputs ──────────────────────────────────────────────────
    if [ -f "$OUTPUT_FILE" ]; then
        log "SKIP generate — outputs exist: $OUTPUT_FILE"
    else
        log "GENERATE → $OUTPUT_FILE"
        python src/generate_outputs.py \
            --model-size   "$MODEL_SIZE" \
            --role         "$ROLE" \
            --adapter-path "$ADAPTER_PATH" \
            --output-tag   "$OUTPUT_TAG"
        log "DONE  generate"
    fi

    # ── 3. Evaluate ──────────────────────────────────────────────────────────
    if [ -f "$RESULT_FILE" ]; then
        log "SKIP evaluate — results exist: $RESULT_FILE"
    else
        log "EVALUATE → $RESULT_FILE"
        python src/evaluate.py \
            --data    "$OUTPUT_FILE" \
            --latency \
            --output  "$RESULT_FILE"
        log "DONE  evaluate"
    fi
done

# ── 4. Summarize ─────────────────────────────────────────────────────────────
hr
echo ""
echo "All $TOTAL runs complete. Generating summary..."
python scripts/summarize_layer_sweep.py --output "$RESULTS_DIR/summary.md"
echo ""
echo "Full results : $RESULTS_DIR/"
echo "Summary      : $RESULTS_DIR/summary.md"
