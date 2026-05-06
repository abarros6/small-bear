#!/usr/bin/env bash
# Experiment §1 — full pipeline: train → generate → evaluate → summarize.
#
# Runs all 24 configs (4 ranks × 3 models × 2 seeds) sequentially.
# Safe to interrupt and re-run: each step is skipped if its output already exists.
#
# Usage:
#   bash scripts/run_exp1.sh          # run everything
#   bash scripts/run_exp1.sh --summary-only   # re-print summary from existing results
set -euo pipefail

CONFIGS_DIR="configs/sweeps"
ADAPTERS_DIR="adapters/sweeps"
OUTPUTS_DIR="outputs"
RESULTS_DIR="results/sweeps"
LOGS_DIR="logs"
ROLE="age_5_11"

# ── helpers ──────────────────────────────────────────────────────────────────

hr() { printf '\n%.0s━' {1..70}; echo; }
log() { echo "  $*"; }

# ── summary-only mode ────────────────────────────────────────────────────────

if [[ "${1:-}" == "--summary-only" ]]; then
    source .venv/bin/activate
    python scripts/summarize_sweep.py --output "$RESULTS_DIR/summary.md"
    exit 0
fi

# ── prerequisites ────────────────────────────────────────────────────────────

source .venv/bin/activate
mkdir -p "$ADAPTERS_DIR" "$RESULTS_DIR" "$LOGS_DIR"

# Generate configs if the directory is empty
if [ -z "$(ls -A "$CONFIGS_DIR" 2>/dev/null)" ]; then
    echo "Generating sweep configs..."
    python scripts/gen_sweep_configs.py
fi

CONFIGS=($(ls "$CONFIGS_DIR"/rank*.yaml | sort))
TOTAL=${#CONFIGS[@]}

echo ""
echo "Experiment §1 — Rank Sweep"
echo "  Configs : $TOTAL"
echo "  Role    : $ROLE"
echo "  Steps   : train → generate → evaluate → summarize"
echo ""
echo "Resumable: steps are skipped if their output already exists."
echo "Interrupt with Ctrl-C and re-run to continue from where it stopped."
hr

N=0
for cfg in "${CONFIGS[@]}"; do
    N=$((N + 1))
    NAME=$(basename "$cfg" .yaml)

    # Parse model size from name: rank{r}_layers{n}_seed{s}_{model}
    MODEL_SIZE=$(echo "$NAME" | cut -d_ -f4-)

    ADAPTER_PATH="$ADAPTERS_DIR/${NAME}_${ROLE}"
    OUTPUT_FILE="$OUTPUTS_DIR/${NAME}_${ROLE}_outputs.jsonl"
    RESULT_FILE="$RESULTS_DIR/${NAME}.txt"

    echo ""
    echo "[$N/$TOTAL] $NAME"
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
            --model-size "$MODEL_SIZE" \
            --role       "$ROLE" \
            --adapter-path "$ADAPTER_PATH" \
            --output-tag   "$NAME"
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
python scripts/summarize_sweep.py --output "$RESULTS_DIR/summary.md"
echo ""
echo "Full results : $RESULTS_DIR/"
echo "Summary      : $RESULTS_DIR/summary.md"
