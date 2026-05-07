#!/usr/bin/env bash
# Full Qwen 2.5 sweep pipeline: train → generate → evaluate.
# Runs all 12 adapters sequentially (GPU OOM if concurrent on M4 16 GB).
#
# Usage: bash scripts/run_qwen25.sh

set -euo pipefail
source .venv/bin/activate

GENERATE="python src/generate_outputs.py"
EVALUATE="python src/evaluate.py"

# ── Training ──────────────────────────────────────────────────────────────────

train() {
    local cfg="$1"
    echo ""
    echo "================================================================"
    echo "  Training: $cfg"
    echo "================================================================"
    mlx_lm.lora --config "$cfg" 2>&1 | tee -a "logs/$(basename "$cfg" .yaml).log"
}

# Qwen 2.5 0.5B
train configs/age_5_11_qwen25_05b_standard_lora.yaml
train configs/age_12_18_qwen25_05b_standard_lora.yaml
train configs/age_5_11_qwen25_05b_fast_lora.yaml
train configs/age_12_18_qwen25_05b_fast_lora.yaml

# Qwen 2.5 1.5B
train configs/age_5_11_qwen25_15b_standard_lora.yaml
train configs/age_12_18_qwen25_15b_standard_lora.yaml
train configs/age_5_11_qwen25_15b_fast_lora.yaml
train configs/age_12_18_qwen25_15b_fast_lora.yaml

# Qwen 2.5 3B
train configs/age_5_11_qwen25_3b_standard_lora.yaml
train configs/age_12_18_qwen25_3b_standard_lora.yaml
train configs/age_5_11_qwen25_3b_fast_lora.yaml
train configs/age_12_18_qwen25_3b_fast_lora.yaml

echo ""
echo "All 12 training runs complete."

# ── Generate + Evaluate ───────────────────────────────────────────────────────

gen_and_eval() {
    local model_key="$1"    # e.g. qwen25_05b_standard
    local adapter_dir="$2"  # e.g. adapters/qwen25_05b_standard
    local tag="$3"          # e.g. qwen25_05b_standard

    echo ""
    echo "================================================================"
    echo "  Generating: $tag"
    echo "================================================================"
    $GENERATE --model-size "$model_key" --adapter-path "${adapter_dir}/age_5_11" \
              --role age_5_11 --output-tag "${tag}"
    $GENERATE --model-size "$model_key" --adapter-path "${adapter_dir}/age_12_18" \
              --role age_12_18 --output-tag "${tag}"

    local combined="outputs/all_${tag}_outputs.jsonl"
    cat "outputs/${tag}_age_5_11_outputs.jsonl" \
        "outputs/${tag}_age_12_18_outputs.jsonl" > "$combined"

    echo ""
    echo "--- Evaluating: $tag ---"
    $EVALUATE --data "$combined" --latency --separation \
              --output "results/${tag}_eval.txt"
}

gen_and_eval "qwen25_05b_standard" "adapters/qwen25_05b_standard" "qwen25_05b_standard"
gen_and_eval "qwen25_05b"          "adapters/fast/qwen25_05b"     "qwen25_05b_fast"

gen_and_eval "qwen25_15b_standard" "adapters/qwen25_15b_standard" "qwen25_15b_standard"
gen_and_eval "qwen25_15b"          "adapters/fast/qwen25_15b"     "qwen25_15b_fast"

gen_and_eval "qwen25_3b_standard"  "adapters/qwen25_3b_standard"  "qwen25_3b_standard"
gen_and_eval "qwen25_3b"           "adapters/fast/qwen25_3b"      "qwen25_3b_fast"

echo ""
echo "================================================================"
echo "  Qwen 2.5 sweep complete."
echo "  Results: results/qwen25_*_eval.txt"
echo "================================================================"
