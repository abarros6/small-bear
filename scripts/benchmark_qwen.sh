#!/usr/bin/env bash
# Benchmark Qwen2-0.5B bfloat16 fast adapters (rank 4, 8 layers) across both roles.
set -e
source .venv/bin/activate
python src/inference.py --model-size qwen --benchmark --verbose
