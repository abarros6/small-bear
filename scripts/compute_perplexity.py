#!/usr/bin/env python3
"""Compute validation loss and perplexity for a trained adapter.

Loss is computed only over assistant response tokens (mask_prompt=True),
consistent with training.

Usage:
    python scripts/compute_perplexity.py \
        --model mlx-community/Llama-3.2-3B-Instruct-4bit \
        --adapter adapters/3b/age_5_11 \
        --data data/age_5_11/valid.jsonl \
        --label "Standard-3B age_5_11"
"""

import argparse
import json
import math

import mlx.core as mx
import mlx.nn as nn
import numpy as np
from mlx_lm import load


def compute_val_loss(model, tokenizer, valid_path: str) -> tuple[float, float, int]:
    examples = [json.loads(l) for l in open(valid_path) if l.strip()]
    total_loss = 0.0
    total_tokens = 0

    for ex in examples:
        messages = ex["messages"]

        full_tokens = tokenizer.apply_chat_template(
            messages, tokenize=True, add_generation_prompt=False
        )
        # Prefix = user turn + assistant header (add_generation_prompt appends it)
        # full_tokens[n_prefix] is the first assistant content token
        prefix_tokens = tokenizer.apply_chat_template(
            messages[:-1], tokenize=True, add_generation_prompt=True
        )
        n_prefix = len(prefix_tokens)
        N = len(full_tokens)

        if n_prefix >= N:
            continue

        ids = mx.array(full_tokens)
        x = ids[:-1][None]  # (1, N-1) — input
        y = ids[1:]          # (N-1,)   — targets

        logits = model(x)
        if isinstance(logits, tuple):
            logits = logits[0]
        logits = logits[0]  # (N-1, vocab)

        per_token_loss = nn.losses.cross_entropy(logits, y)  # (N-1,)
        mx.eval(per_token_loss)

        # Mask: 1 for assistant tokens — y[n_prefix-1] through y[N-2]
        mask_np = np.zeros(N - 1, dtype=np.float32)
        mask_np[n_prefix - 1 :] = 1.0
        mask = mx.array(mask_np)

        loss_sum = (per_token_loss * mask).sum()
        mx.eval(loss_sum)

        total_loss += loss_sum.item()
        total_tokens += int(mask_np.sum())

    avg_loss = total_loss / total_tokens
    return avg_loss, math.exp(avg_loss), total_tokens


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--adapter", required=True)
    parser.add_argument("--data", required=True)
    parser.add_argument("--label", default="")
    args = parser.parse_args()

    print(f"Loading {args.model} + {args.adapter} ...")
    model, tokenizer = load(args.model, adapter_path=args.adapter)

    print(f"Evaluating on {args.data} ...")
    loss, ppl, n_tok = compute_val_loss(model, tokenizer, args.data)

    label = args.label or args.adapter
    print(f"\n{'─' * 52}")
    print(f"  {label}")
    print(f"  Val loss  : {loss:.3f}")
    print(f"  Perplexity: {ppl:.2f}")
    print(f"  Tokens    : {n_tok}")
    print(f"{'─' * 52}\n")


if __name__ == "__main__":
    main()
