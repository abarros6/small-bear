# Small-Bear for Dummies

A plain-language explanation of what this project is, what we built, and what we found.

---

## What is this project?

Victoria Hospital in London, Ontario has a VR experience for pediatric patients — kids who
are about to have a procedure and are scared or confused. The VR world has a character called
**Dr. Beary Good**, a friendly bear who explains what's going to happen, answers questions, and
helps the kid feel less anxious.

The problem: a 7-year-old and a 16-year-old need very different explanations. "The X-ray
machine takes a picture of your bones, it doesn't hurt!" works for a young child. A teenager
finds that patronizing and wants more clinical detail.

This project builds Dr. Beary Good as a small AI language model that automatically speaks in
the right way depending on the patient's age — without needing to be told how in the moment.

---

## What's a language model and why is it "small"?

A language model (LLM) is a program trained on enormous amounts of text that learns to predict
what word comes next. That's literally all it does — but doing it well enough produces
surprisingly coherent, useful responses.

"Large" language models (like GPT-4) have tens of billions of parameters — tunable numbers
that determine how the model behaves. They're powerful but slow and expensive, running on
data centres, not a VR headset.

We used "small" models: **Llama 3.2 at 3B and 1B parameters** (3 billion and 1 billion
respectively). Small enough to run on a Mac Mini M4 in real time. The tradeoff is that they
need help to behave correctly for a specific use case — which is where fine-tuning comes in.

---

## What is fine-tuning and why did we do it?

A base language model is trained to be generally useful. It doesn't naturally talk like a
pediatric hospital guide. Left alone, it gives long, adult, clinical-sounding answers because
most of the text it was trained on reads that way.

Fine-tuning means showing the model ~500 carefully written examples of *exactly* the kind of
responses we want — short, warm, age-appropriate — and adjusting a small subset of its
parameters to move it toward that style. Think of it as giving the model a very targeted
coaching session rather than retraining it from scratch.

We wrote ~1,100 example question-and-answer pairs for two audiences: kids aged 5–11 and kids
aged 12–18. The questions cover things like "will the X-ray hurt?", "why do nurses wear those
clothes?", "what if I feel scared?". The responses are written to match each age group's
vocabulary and emotional register.

---

## What is LoRA and why not just fine-tune the whole model?

Full fine-tuning means adjusting every parameter in the model. For a 3B parameter model,
that's expensive, slow, and requires enormous GPU memory.

**LoRA** (Low-Rank Adaptation) is a clever shortcut. Instead of adjusting all parameters,
you freeze the original model and insert small, trainable "adapter" matrices alongside certain
layers. These adapters are tiny compared to the base model — a few million parameters versus
billions. Training is fast, the base model is unchanged, and you can swap adapters at runtime.

This is important for us because we have **two adapters** — one for each age group — sharing
one base model. At runtime, the VR app loads whichever adapter matches the patient's age.
You get two distinct communication styles from one model with minimal overhead.

**QLoRA** just means the base model is additionally compressed (quantized) to 4-bit precision
to reduce memory further. We run on a Mac Mini M4 with 16 GB of RAM — this compression is
what makes it feasible.

---

## What did we actually measure?

We care about two things:

1. **Does the 5–11 adapter actually sound age-appropriate?** We measured this using the
   **Flesch-Kincaid (FK) grade level** — a formula that estimates the US school grade needed
   to understand a piece of text, based on word length and sentence length. A FK score ≤ 7.0
   means a 7th grader (around age 12) can comfortably read it — appropriate for our younger
   group. The base model (no fine-tuning) scores around FK 9.5. Our best adapters get to FK 5.5.

2. **Are the two adapters actually different from each other?** We measured this with an
   **inter-role classifier** — a simple machine learning model that reads an output and tries
   to guess which adapter produced it. If the outputs are genuinely stylistically distinct, the
   classifier scores near 1.0. If they're similar, it scores near 0.5 (chance). Our adapters
   score 0.89–0.96, meaning the style difference is real and consistent.

We also tracked **latency** — how long it takes to generate a response. The VR target is under
1.0 second, otherwise the conversation feels unnatural.

---

## What did we find?

### Finding 1: Fine-tuning works

The base model (no adapter) passes the FK ≤ 7.0 bar only 12% of the time. Our best adapter
passes 84% of the time. The fine-tuning is doing real work.

### Finding 2: The style lives in the weights, not a prompt

We trained without any system prompt — no "you are a friendly hospital bear for children"
instruction in the training data. The age-appropriate communication style had to be encoded
directly into the adapter weights. This was a deliberate design choice: if style depends on
a prompt, removing that prompt degrades the output. If style is in the weights, it's always
there, and the VR app team can add their own system prompt on top without conflict.

### Finding 3: The crossover

This is the main research finding. We trained two configurations:
- **Standard**: larger adapter (rank 8, 16 layers of the model adapted)
- **Fast**: smaller adapter (rank 4, 8 layers adapted)

Intuition says: bigger adapter = better performance. Reality: it depends on the base model.

- On the **3B model**, Standard wins (84% FK vs 76%).
- On the **1B model**, Fast wins (82% FK vs 72%).

The ordering of the two configurations is completely reversed between model sizes. This is
the crossover. It's counterintuitive because Fast-1B is *smaller* than Standard-1B in every
way — fewer parameters, less of the model adapted — yet it outperforms.

### Finding 4: Why the crossover happens (capacity regularization)

We ran a controlled experiment: fixed the layer count constant and varied only the rank
({2, 4, 8, 16}) across four different model architectures and two random seeds. The crossover
persisted, meaning **rank — not layer coverage — is what drives it**.

The explanation is **capacity regularization**: the 1B model has limited representational
capacity. A high-rank adapter has more parameters than the model can meaningfully use for this
task (simple style adaptation, not knowledge acquisition). The extra parameters become noise.
A lower-rank adapter fits the task to the model's actual capacity. The 3B model has enough
capacity to use the additional rank productively.

### Finding 5: Depth, not size, predicts rank sensitivity

Here's where it gets surprising. SmolLM2 is a 360M parameter model — smaller than either
Llama variant. You'd expect it to follow the small-model pattern (lower rank = better). It
doesn't: it follows the *large-model* pattern, and it's the most rank-hungry model we tested
(performance keeps improving as rank increases, even up to rank 16).

Why? SmolLM2 has **32 transformer layers**. Llama 1B has only 16. Despite having fewer
total parameters, SmolLM2 is architecturally deeper — more layers means more per-layer
representational capacity that higher-rank adapters can exploit. Total parameter count is
a misleading proxy; **layer depth is what actually matters**.

### Finding 6: We checked whether the crossover was just luck — it wasn't (mostly)

Early results (Findings 3–5 above) each came from training one adapter once per configuration.
A routine re-check retrained the "same" configuration a second time and got a wildly different
score — a 17-point swing with nothing changed on paper. That's a red flag: if identical setups
can swing that much, maybe the crossover itself was never real, just two lucky/unlucky draws.

So we retrained every configuration dozens of times each (110 training runs total) and ran
proper statistics. The verdict: **the crossover is real on both sides**, but not identical in
kind. On the 1B model, Fast's advantage holds up even after controlling for response length —
a genuine "communicates better" effect. On the 3B model, Standard's advantage turns out to be
mostly because it writes shorter responses, not because it writes more simply *for a given
length*. Both are real findings; the 3B one is a more modest claim than we originally thought.
Full statistical detail: `EXPERIMENTS.md` §6.

### A second, related project: guard-bear

Alongside this adapter work, a companion project called **guard-bear** was built to sit in
front of the response model: a small classifier that checks whether an incoming question is
safe to answer at all (catching things like distress escalation) before the age-appropriate
adapter ever sees it. It lives in its own repo (`../guard-bear/`) and is evaluated separately,
but it's presented together with this crossover work as the two contributions of the same
paper submission.

---

## What's the practical upshot?

| If you care about...              | Use this                  |
|-----------------------------------|---------------------------|
| Fastest possible response (VR)    | Qwen 2 0.5B Fast (0.46 s avg) |
| Best readability + speed balance  | SmolLM2 Standard (84% FK, 0.81 s) |
| Best Llama option within 1.0 s    | Llama 1B Fast (82% FK, 0.93 s) |
| Highest readability, latency OK   | Llama 3B Standard (84% FK, 2.37 s) |

The broader lesson: when choosing a LoRA configuration for a new model, don't default to
the biggest adapter you can fit. First consider the model's layer depth and capacity — a
smaller adapter may outperform on constrained architectures.

---

## What's left to do?

- **Human evaluation**: automated readability scores are a proxy. Real peer raters scoring
  whether outputs actually sound right to a 7-year-old vs. a 15-year-old would strengthen the
  claim.
- **guard-bear's leakage check**: its near-perfect discrimination score hasn't yet been checked
  for whether it's cheating on some shortcut in the training data rather than genuinely
  understanding the query.
- **Dataset quality cull**: programmatic scoring to remove the weakest training examples before
  the next retraining pass.
