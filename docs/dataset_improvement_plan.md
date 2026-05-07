# Dataset Improvement Plan

## Context

The current dataset has four known quality issues:

1. **Circular validation** — training and validation were generated in the same Claude sessions under the same prompts. The 50 validation examples per role measure how well the adapter mimics Claude Opus, not whether it produces genuinely age-appropriate output. Validation needs to be independent.
2. **Synthetic uniformity** — questions follow predictable interrogative patterns ("What is X?", "Can I X?"). Responses share formulaic openers ("It's totally okay to feel...", "That's a completely understandable feeling."). Real children and teens ask differently.
3. **No adversarial or edge-case coverage** — the dataset only covers the five defined categories. There are no examples of unexpected questions, out-of-scope requests, or safety-boundary probes. The adapter has no learned behaviour for these.
4. **Unreviewed training examples** — some training examples are weaker than others; the worst should be culled before the next training run.

**Goal:** produce a revised dataset where (a) the validation set is genuinely independent, (b) the question style reflects how children and teens actually communicate, (c) the adapter has learned behaviour for edge cases, and (d) the training set is cleaner.

---

## Summary of Changes

| Area | Owner | Volume | Files affected |
|------|-------|--------|----------------|
| 1. Validation replacement | You (generate) → me (integrate) | ~100 new examples | `data/source/validate/*.jsonl` |
| 2. Question diversification | You (generate) → me (integrate) | ~100 new training examples | `data/source/train/*.jsonl` |
| 3. Adversarial examples | You (generate) → me (integrate) | ~50–100 new training examples | new `data/source/train/edge_cases.jsonl` |
| 4. Quality cull | Me (identify) → you (confirm) → me (remove) | ~50–100 examples removed | `data/source/train/*.jsonl` |

---

## Area 1: Validation Set Replacement

**What:** Replace all 95 source validation examples with ones you write or generate using a different prompting approach. The key constraint: **these questions must not come from the same generation sessions as the training data.**

**Target:** 10 examples per category × role bucket = 100 total (same as now, but independent).

| Category | Age 5–11 | Age 12–18 |
|----------|----------|-----------|
| emotional_reassurance | 10 | 10 |
| faqs_general_curiosity | 10 | 10 |
| hospital_rules_and_routines | 10 | 10 |
| what_to_expect | 10 | 10 |
| who_are_these_people | 10 | 10 |

**How to generate (Claude browser session):**

Use a fresh chat with this system prompt:

> You are generating a validation dataset for a pediatric hospital VR guide called Dr. Beary Good at Victoria Hospital, London Ontario. Your job is to write question-answer pairs that will be used to TEST a fine-tuned LLM — not to train it. Prioritize questions that are:
> - Phrased differently from typical chatbot training data (unexpected word choices, emotional framings, run-on sentences, child-like phrasing)
> - Edge cases within the category (not the most obvious question someone might ask)
> - Emotionally genuine — the kind of thing a real child or teen might actually say, not a textbook example
>
> Safety rules: never imply a diagnosis, never recommend medications, always redirect emergencies to staff.
>
> Output one JSON object per line:
> `{"instruction": "...", "response": "...", "role": "5-11", "category": "emotional_reassurance"}`

Then for each bucket (category × role), prompt: *"Generate 10 validation examples for age [5-11 / 12-18], category [category name]. Focus on atypical phrasings and genuine emotional situations."*

**Handoff:** Save each category as a separate file:
```
new_validate_emotional_reassurance.jsonl
new_validate_faqs_general_curiosity.jsonl
new_validate_hospital_rules_and_routines.jsonl
new_validate_what_to_expect.jsonl
new_validate_who_are_these_people.jsonl
```
Drop them anywhere in the project (e.g. a `data/source/validate_new/` folder). I'll review, merge, and replace `data/source/validate/`.

---

## Area 2: Question Style Diversification

**What:** Add ~100 new training examples that use non-interrogative or atypical question forms. These supplement (don't replace) the existing training data.

**Target patterns to add across all categories (mix of both roles):**

| Pattern | Example |
|---------|---------|
| Emotional statement (not a question) | "I don't want to be here." |
| Incomplete/interrupted thought | "What if the nurse... I don't know, what if she hurts me?" |
| Child-like phrasing with invented words | "What's that beepy thing that keeps going off?" |
| Two concerns in one | "Can my dad stay and also can I keep my stuffed animal?" |
| Negative framing | "Nobody told me what was going to happen." |
| Resistance/refusal | "I'm not doing the test. I don't care what anyone says." |
| Overheard something scary | "I heard the doctor say something about my heart. What does that mean?" |

**How to generate (Claude browser session):**

> I'm building training data for a pediatric hospital LLM guide. I need examples where the QUESTION is phrased unusually — not a clean "What is X?" or "Can I Y?" Instead, use emotional statements, incomplete sentences, child-like word choices, resistance, or things a stressed child/teen would actually say. Responses should still be age-appropriate and grounded in Victoria Hospital. Output format:
> `{"instruction": "...", "response": "...", "role": "5-11", "category": "emotional_reassurance"}`
>
> Generate 20 examples for age 5–11 mixing categories. Focus entirely on unusual/diverse question phrasing.

Run this for both roles (5-11 and 12-18), ~50 examples each.

**Handoff:** Save as:
```
new_train_diverse_questions.jsonl
```
Drop into the project. I'll merge into the appropriate category files in `data/source/train/`.

---

## Area 3: Adversarial / Edge-Case Examples

**What:** Add examples that teach the adapter what to do when a question falls outside the five defined categories or probes safety boundaries. These go in training only.

**Note on guard model interaction:** The guard model (planned separately) will block responses that imply diagnosis or recommend medications before the adapter responds. Despite this, the adapter should still have learned behaviour for these — defence in depth. For truly out-of-scope questions (asking about other patients, asking to call home), the guard won't catch them; the adapter is on its own.

**Categories of edge cases to cover:**

| Type | Examples |
|------|---------|
| Out-of-scope requests | "Can you call my mom?", "What's that other kid's name?" |
| Safety-boundary probes | "Do I have cancer?", "Can I take more of my pain medicine?" |
| Distress escalation | "I can't breathe properly", "Something hurts really bad right now" |
| Ambient/environmental | "There's a weird smell", "It's too cold in here", "The light is too bright" |
| Meta questions about the guide | "Are you a real person?", "Who made you?" |
| Boredom/disengagement | "I'm bored", "There's nothing to do", "Can you tell me a joke?" |

**Target:** ~25 examples per role = ~50 total. Keep responses honest: redirect appropriately, don't pretend to be a human, don't guess at diagnoses.

**How to generate (Claude browser session):**

> I need training examples for edge cases in a pediatric hospital LLM guide. The guide normally handles 5 topics: emotional reassurance, FAQs, hospital rules, what to expect, and who hospital staff are. I need examples for questions that fall OUTSIDE these topics or probe safety limits.
>
> For out-of-scope questions: responses should gently redirect to the right resource (a nurse, a parent, the call button) without pretending to help with something out of scope.
> For safety-boundary questions: responses should never diagnose, never recommend medications, and always redirect to clinical staff — but do so warmly, not robotically.
>
> Use category `"edge_cases"` for all examples. Output format:
> `{"instruction": "...", "response": "...", "role": "5-11", "category": "edge_cases"}`
>
> Generate 25 examples for age 5–11.

Run for both roles.

**Handoff:** Save as:
```
new_train_edge_cases.jsonl
```
Drop into the project. I'll add it as a new category file in `data/source/train/`.

---

## Area 4: Training Quality Cull

**What:** Remove the weakest training examples from the existing set. No generation required from you — I'll do the identification programmatically and show you the candidates before removing anything.

**My process:**
1. Score all 1,000 training examples on FK grade (for 5-11 role) and response length
2. Flag examples where the 5-11 response has FK > 9.0 (well above target), or where the response is < 30 words (too short to be useful), or where the response opener matches one of the formulaic patterns
3. Present you a shortlist of ~50–80 candidates with scores
4. You confirm which to remove; I delete them from the source files

**This runs after Areas 1–3 are complete** so we know the total dataset size before culling.

---

## Handoff Protocol

When you've finished generating, drop the new files anywhere in the project directory (e.g. `data/source/incoming/`). Then tell me which files are ready. I will:

1. Review examples for format validity and safety-rule compliance
2. Merge new training examples into the appropriate `data/source/train/` category files
3. Replace `data/source/validate/` with the new validation files
4. Re-run `prepare_data.py` to regenerate `data/age_5_11/` and `data/age_12_18/`
5. Report final counts per category and role before any retraining

**Required format for all new files** (same as existing source format):
```json
{"instruction": "...", "response": "...", "role": "5-11", "category": "emotional_reassurance"}
```
Role must be exactly `"5-11"` or `"12-18"`. Category must match exactly or be `"edge_cases"` for Area 3.
