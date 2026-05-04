#!/usr/bin/env python3
"""
Shared constants for Dr. Beary Good.
Import from here — do NOT duplicate in other modules.

No system prompts are defined here. The adapter weights encode the
age-appropriate communication register. The VR application team injects
their own system prompt at deployment time.
"""

BASE_MODEL_3B       = "mlx-community/Llama-3.2-3B-Instruct-4bit"
BASE_MODEL_1B       = "mlx-community/Llama-3.2-1B-Instruct-4bit"
BASE_MODEL_QWEN     = "Qwen/Qwen2-0.5B-Instruct-MLX"
BASE_MODEL_QWEN4BIT = "mlx-community/Qwen2-0.5B-Instruct-4bit"

ROLES = ["age_5_11", "age_12_18"]
