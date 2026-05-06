#!/usr/bin/env python3
"""
Dr. Beary Good — inference script.

Role is always specified explicitly via --role. No automatic role detection.
No system prompt is applied by default — the adapter weights carry the
age-appropriate communication register. Pass --system-prompt to inject
application context (e.g. for VR deployment testing).

Modes:
  default         Load base model + LoRA adapter from adapters/{model_size}/{role}/
  --base          Load the raw base model (no adapter) — for comparison
  --model-size    Select 3b (default) or 1b base model for ablation

Usage:
    # Fine-tuned adapter, no system prompt (weights carry the style):
    python src/inference.py --role age_5_11 --query "Will the X-ray hurt?"
    python src/inference.py --role age_12_18 --query "Will the X-ray hurt?"

    # 1B model ablation:
    python src/inference.py --role age_5_11 --model-size 1b --query "Will the X-ray hurt?"

    # Base model for comparison (no adapter, no system prompt):
    python src/inference.py --base --query "Will the X-ray hurt?"

    # With system prompt (VR deployment testing):
    python src/inference.py --role age_5_11 --query "Will the X-ray hurt?" \\
        --system-prompt "You are Dr. Beary Good at Victoria Hospital."

    # Interactive mode:
    python src/inference.py --role age_5_11 --interactive

    # Benchmark across both roles (no system prompt):
    python src/inference.py --benchmark
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from constants import BASE_MODEL_3B, BASE_MODEL_1B, BASE_MODEL_QWEN, BASE_MODEL_QWEN4BIT, ROLES

_BASE_MODEL = {
    "3b":          BASE_MODEL_3B,
    "1b":          BASE_MODEL_1B,
    "qwen":        BASE_MODEL_QWEN,
    "qwen4bit":    BASE_MODEL_QWEN4BIT,
    "qwen_standard":    BASE_MODEL_QWEN,
    "qwen4bit_standard": BASE_MODEL_QWEN4BIT,
}

ADAPTER_DIR = Path("adapters")


def load_model(role: str, model_size: str = "3b", use_base: bool = False, variant: str = "",
               adapter_path_override: str = ""):
    """Load model and tokenizer.

    Args:
        role: One of the values in ROLES.
        model_size: '3b', '1b', 'qwen', or 'qwen4bit' — selects base model.
        use_base: Load the raw base model with no adapter (for comparison).
        variant: Adapter subdirectory prefix, e.g. 'fast' → adapters/fast/{size}/{role}.
                 Empty string (default) → adapters/{size}/{role}.
        adapter_path_override: Explicit path to an adapter directory, bypassing the
                               default path construction. Used for sweep runs.

    Returns:
        (model, tokenizer)
    """
    from mlx_lm import load

    base_model = _BASE_MODEL[model_size]

    if use_base:
        print(f"Loading base model (no adapter): {base_model}", file=sys.stderr)
        return load(base_model)

    if adapter_path_override:
        adapter_path = Path(adapter_path_override)
    elif variant:
        adapter_path = ADAPTER_DIR / variant / model_size / role
    else:
        adapter_path = ADAPTER_DIR / model_size / role

    if not adapter_path.exists():
        print(f"Error: adapter not found at {adapter_path}", file=sys.stderr)
        print(f"  Train first: mlx_lm.lora --config configs/{role}_{model_size}_lora.yaml",
              file=sys.stderr)
        raise SystemExit(1)
    print(f"Loading {base_model} + adapter: {adapter_path}", file=sys.stderr)
    return load(base_model, adapter_path=str(adapter_path))


def generate_response(
    model,
    tokenizer,
    query: str,
    system_prompt: str | None = None,
    max_tokens: int = 200,
    temp: float = 0.0,
    top_p: float = 1.0,
    top_k: int = 0,
    repetition_penalty: float = 1.2,
) -> tuple:
    """Generate a response for the given query.

    Args:
        system_prompt: Optional. If None, only the user message is sent —
                       matching the no-system-prompt training setup.

    Returns:
        (response_text: str, latency_seconds: float)

    Inference settings in use
    -------------------------
    temperature  : 0.0  (mlx-lm default — greedy decoding)
        Scales the logit distribution before sampling.
        0.0 = always pick the single highest-probability token (deterministic, no variation).
        0.0–0.5 = low randomness, focused and consistent — appropriate for a medical/safety context.
        0.7–1.0 = natural conversational variation; same question may get slightly different answers.
        >1.0 = increasingly incoherent / "creative"; not suitable here.
        For a VR pediatric guide, 0.0 maximises safety (no chance of unexpected outputs) but
        produces identical answers to identical questions. A value of ~0.3 would add natural
        variation while staying conservative.

    top_p        : 1.0  (mlx-lm default — nucleus sampling disabled)
        Restricts sampling to the smallest set of tokens whose cumulative probability ≥ top_p.
        1.0 = no restriction (all tokens eligible, but temp=0.0 makes this irrelevant anyway).
        0.9 = sample only from tokens covering the top 90% of probability mass.
        Only meaningful when temperature > 0.

    top_k        : 0    (mlx-lm default — top-k sampling disabled)
        Restricts sampling to the K most probable tokens at each step.
        0 = disabled. Again irrelevant at temp=0.0.

    repetition_penalty : 1.2  (default set here — mlx-lm default is 1.0)
        Multiplicative penalty applied to logits of already-generated tokens.
        1.0 = no penalty. 1.1–1.3 reduces looping at temp=0.0. Applied over
        the last 20 tokens via make_logits_processors().

    max_tokens   : 300  (set in argparse; ~200–250 words)
        Hard cap on generated tokens. Generation stops at this limit OR at the model's EOS token,
        whichever comes first. The EOS token usually fires before the cap for well-trained adapters.
        Increase if responses are being cut off mid-sentence.
        Decrease to enforce brevity or reduce latency.
    """
    from mlx_lm import generate
    from mlx_lm.sample_utils import make_sampler, make_logits_processors

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": query.strip()})

    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )

    sampler = make_sampler(temp=temp, top_p=top_p, top_k=top_k)
    logits_processors = make_logits_processors(repetition_penalty=repetition_penalty)

    t0 = time.perf_counter()
    response = generate(
        model,
        tokenizer,
        prompt=prompt,
        max_tokens=max_tokens,
        verbose=False,
        sampler=sampler,
        logits_processors=logits_processors,
    )
    latency = time.perf_counter() - t0

    return response, latency


def main():
    parser = argparse.ArgumentParser(
        description="Dr. Beary Good — explicit-role inference"
    )

    parser.add_argument("--base", action="store_true",
                        help="Load raw base model (no adapter) — for comparison")
    parser.add_argument("--role", "-r", choices=ROLES,
                        help=f"Role adapter to load: {' | '.join(ROLES)}")
    parser.add_argument("--model-size", choices=["3b", "1b", "qwen", "qwen4bit", "qwen_standard", "qwen4bit_standard"], default="3b",
                        help="Base model size: 3b (default), 1b, qwen, qwen4bit, qwen_standard, qwen4bit_standard")
    parser.add_argument("--system-prompt", "-s",
                        help="Optional system prompt (e.g. for VR deployment testing). "
                             "Omit to run without one — matching training conditions.")
    parser.add_argument("--query", "-q", help="Single query string")
    parser.add_argument("--interactive", "-i", action="store_true",
                        help="Interactive mode — loop until quit")
    parser.add_argument("--benchmark", action="store_true",
                        help="Run standard queries across all roles (no system prompt)")
    parser.add_argument("--max-tokens", type=int, default=300,
                        help="Maximum tokens to generate (default: 300). "
                             "~300 tokens ≈ 200-250 words. Increase if responses are truncated; "
                             "decrease to reduce latency. EOS usually fires before this cap.")
    parser.add_argument("--temp", type=float, default=0.0,
                        help="Sampling temperature (default: 0.0 = greedy). "
                             "0.3–0.5 adds variation; >1.0 is incoherent.")
    parser.add_argument("--top-p", type=float, default=1.0,
                        help="Nucleus sampling threshold (default: 1.0 = disabled). "
                             "Only meaningful when --temp > 0.")
    parser.add_argument("--top-k", type=int, default=0,
                        help="Top-k sampling (default: 0 = disabled). "
                             "Only meaningful when --temp > 0.")
    parser.add_argument("--repetition-penalty", type=float, default=1.2,
                        help="Repetition penalty applied to already-generated tokens (default: 1.2). "
                             "1.0 = no penalty. 1.1–1.3 reduces looping at temp=0.0.")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Show latency after each response")
    parser.add_argument("--variant", default="",
                        help="Adapter variant subdirectory, e.g. 'fast' → adapters/fast/{size}/{role}")
    parser.add_argument("--adapter-path", default="",
                        help="Explicit adapter directory path, overrides default path construction. "
                             "Use for sweep runs: --adapter-path adapters/sweeps/rank4_layers8_seed42_1b_age_5_11")

    args = parser.parse_args()

    if not args.base and not args.role and not args.benchmark:
        parser.error(f"--role is required ({' | '.join(ROLES)})")

    if args.benchmark:
        benchmark_queries = [
            ("Will the X-ray hurt?",                                        "age_5_11"),
            ("I'm scared. Can my teddy bear come with me?",                 "age_5_11"),
            ("Why do I have to stay in bed?",                               "age_5_11"),
            ("What does that beeping machine do?",                          "age_5_11"),
            ("Who are all these people in scrubs?",                         "age_5_11"),
            ("Will the X-ray hurt?",                                        "age_12_18"),
            ("What actually happens during an MRI?",                        "age_12_18"),
            ("Why do I have to wear a hospital gown?",                      "age_12_18"),
            ("Can I have my phone with me during the procedure?",           "age_12_18"),
            ("What are the nurses actually doing when they check on me?",   "age_12_18"),
        ]

        models = {}
        print("Dr. Beary Good — Benchmark (no system prompt)")
        print("=" * 70)

        latencies = []
        for query, role in benchmark_queries:
            key = f"{role}_{args.model_size}"
            if key not in models:
                models[key] = load_model(role, model_size=args.model_size, use_base=args.base,
                                         variant=args.variant, adapter_path_override=args.adapter_path)
            model, tokenizer = models[key]
            response, latency = generate_response(
                model, tokenizer, query,
                system_prompt=args.system_prompt,  # None by default
                max_tokens=args.max_tokens,
                temp=args.temp,
                top_p=args.top_p,
                top_k=args.top_k,
                repetition_penalty=args.repetition_penalty,
            )
            latencies.append(latency)
            print(f"\n[{role}] Q: {query}")
            print(f"A: {response[:300]}{'...' if len(response) > 300 else ''}")
            if args.verbose:
                print(f"   Latency: {latency*1000:.0f}ms")

        print("\n" + "=" * 70)
        print(f"Latency avg: {sum(latencies)/len(latencies):.2f}s  "
              f"min={min(latencies):.2f}s  max={max(latencies):.2f}s")
        return

    if args.interactive:
        role = args.role
        print("Dr. Beary Good — Interactive Inference")
        print(f"Role:          {role}")
        print(f"Model size:    {args.model_size}")
        print(f"System prompt: {'none' if not args.system_prompt else repr(args.system_prompt[:60] + '...')}")
        print("Type a query and press Enter. Type 'quit' to exit.\n")

        model, tokenizer = load_model(role, model_size=args.model_size, use_base=args.base,
                                      variant=args.variant, adapter_path_override=args.adapter_path)

        while True:
            try:
                query = input("Query> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not query:
                continue
            if query.lower() in ("quit", "exit", "q"):
                break

            response, latency = generate_response(
                model, tokenizer, query,
                system_prompt=args.system_prompt,
                max_tokens=args.max_tokens,
                repetition_penalty=args.repetition_penalty,
            )
            print(f"\n{response}\n")
            if args.verbose:
                print(f"[Latency: {latency*1000:.0f}ms]\n")

    elif args.query:
        role = args.role or ROLES[0]
        model, tokenizer = load_model(role, model_size=args.model_size, use_base=args.base,
                                      variant=args.variant, adapter_path_override=args.adapter_path)
        response, latency = generate_response(
            model, tokenizer, args.query,
            system_prompt=args.system_prompt,
            max_tokens=args.max_tokens,
            repetition_penalty=args.repetition_penalty,
        )
        print(response)
        if args.verbose:
            print(f"\n[Latency: {latency*1000:.0f}ms]")

    else:
        parser.print_help()
        raise SystemExit(1)


if __name__ == "__main__":
    main()
