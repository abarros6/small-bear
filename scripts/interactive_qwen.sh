#!/usr/bin/env bash
# Interactive session with Qwen2-0.5B bfloat16 fast adapters (rank 4, 8 layers).
# Usage: bash scripts/interactive_qwen.sh <role>
#   role: age_5_11 | age_12_18
set -e
ROLE="${1:?Usage: $0 <role>  (age_5_11 | age_12_18)}"
source .venv/bin/activate
python src/inference.py --model-size qwen --role "$ROLE" --interactive --verbose
