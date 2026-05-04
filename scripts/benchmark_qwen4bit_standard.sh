#!/usr/bin/env bash
# Benchmark Qwen2-0.5B 4-bit standard adapters (rank 8, 16 layers) across both roles.
set -e
source .venv/bin/activate
python src/inference.py --model-size qwen4bit_standard --benchmark --verbose
