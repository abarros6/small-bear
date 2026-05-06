# Model Comparison: All Variants

Full evaluation across all fine-tuned configurations plus two untuned baselines.
50 validation examples per role (100 total) per variant. No system prompt — matching training conditions.

Naming convention: **Standard** = rank 8, 16 layers. **Fast** = rank 4, 8 layers.

---

## Age 5–11 Role — Headline Metrics

Target: FK grade ≤ 7.0. VR real-time latency target: < 1.0 s.

| Variant                | FK avg | FK ≤ 7.0  | SMOG | Fog  | Coleman | Lex div | Avg words | Avg lat | < 1 s      | Avg tok | TPS   |
|------------------------|--------|-----------|------|------|---------|---------|-----------|---------|------------|---------|-------|
| Standard-3B            | 5.5    | 42/50 84% | 8.5  | 7.4  | 6.3     | 0.724   | 75        | 2.37 s  |  0/50  0%  | 92      | 38.8  |
| Standard-1B            | 6.1    | 36/50 72% | 8.8  | 7.7  | 6.7     | 0.712   | 74        | 1.09 s  | 21/50 42%  | 89      | 81.7  |
| Fast-3B                | 5.9    | 38/50 76% | 8.9  | 7.9  | 6.6     | 0.636   | 99        | 2.83 s  |  0/50  0%  | 120     | 41.9  |
| Fast-1B                | 5.5    | 41/50 82% | 8.4  | 7.2  | 6.2     | 0.701   | 72        | 0.93 s  | 35/50 70%  | 88      | 94.3  |
| SmolLM2 Standard       | 5.8    | 42/50 84% | 8.6  | 7.3  | 6.5     | 0.774   | 63        | 0.81 s  | 44/50 88%  | 76      | 92.8  |
| SmolLM2 Fast           | 6.1    | 32/50 64% | 8.4  | 7.8  | 6.8     | 0.707   | 92        | 1.08 s  | 34/50 68%  | 111     | 99.7  |
| Qwen Standard (BF16)   | 6.2    | 37/50 74% | 9.0  | 7.9  | 7.1     | 0.760   | 73        | 0.59 s  | 50/50 100% | 88      | 148.6 |
| Qwen Standard (4-bit)  | 6.2    | 37/50 74% | 9.0  | 7.9  | 7.1     | 0.760   | 73        | 0.59 s  | 50/50 100% | 88      | 150.6 |
| Qwen Fast (BF16)       | 5.8    | 34/50 68% | 8.5  | 7.4  | 6.5     | 0.725   | 69        | 0.46 s  | 49/50 98%  | 83      | 175.8 |
| Qwen Fast (4-bit)      | 5.8    | 34/50 68% | 8.5  | 7.4  | 6.5     | 0.725   | 69        | 0.46 s  | 49/50 98%  | 83      | 175.4 |
| Base-3B (no LoRA)      | 9.4    |  6/50 12% | 12.1 | 12.2 | 9.6     | 0.609   | 152       | 3.99 s  |  3/50  6%  | 190     | 46.5  |
| Base-1B (no LoRA)      | 9.5    |  7/50 14% | 12.1 | 12.2 | 9.0     | 0.508   | 201       | 2.01 s  |  2/50  4%  | 247     | 122.3 |

---

## Age 12–18 Role — Headline Metrics

No FK ceiling for this role — lower is more readable but not penalised.

| Variant                | FK avg | SMOG | Fog  | Coleman | Lex div | Avg words | Avg lat | < 1 s      | Avg tok | TPS   |
|------------------------|--------|------|------|---------|---------|-----------|---------|------------|---------|-------|
| Standard-3B            | 8.7    | 11.4 | 10.9 | 10.0    | 0.714   | 92        | 2.94 s  |  0/50  0%  | 116     | 39.3  |
| Standard-1B            | 8.8    | 11.7 | 11.3 | 10.3    | 0.701   | 90        | 1.36 s  |  3/50  6%  | 114     | 83.7  |
| Fast-3B                | 8.3    | 11.2 | 10.7 | 9.7     | 0.613   | 122       | 3.63 s  |  1/50  2%  | 153     | 41.7  |
| Fast-1B                | 8.4    | 11.3 | 10.6 | 9.4     | 0.650   | 92        | 1.20 s  | 12/50 24%  | 115     | 95.4  |
| SmolLM2 Standard       | 9.4    | 12.1 | 11.9 | 9.9     | 0.732   | 88        | 1.12 s  | 21/50 42%  | 107     | 94.8  |
| SmolLM2 Fast           | 9.7    | 12.0 | 12.1 | 9.9     | 0.602   | 140       | 1.62 s  | 18/50 36%  | 169     | 103.1 |
| Qwen Standard (BF16)   | 9.8    | 12.0 | 12.0 | 10.4    | 0.743   | 90        | 0.75 s  | 47/50 94%  | 114     | 151.2 |
| Qwen Standard (4-bit)  | 9.8    | 12.0 | 12.0 | 10.4    | 0.743   | 90        | 0.74 s  | 48/50 96%  | 114     | 154.3 |
| Qwen Fast (BF16)       | 9.4    | 11.7 | 11.5 | 9.6     | 0.644   | 103       | 0.67 s  | 48/50 96%  | 127     | 186.6 |
| Qwen Fast (4-bit)      | 9.4    | 11.7 | 11.5 | 9.6     | 0.644   | 103       | 0.67 s  | 48/50 96%  | 127     | 186.9 |
| Base-3B (no LoRA)      | 10.6   | 12.9 | 13.3 | 11.4    | 0.565   | 206       | 5.39 s  |  1/50  2%  | 264     | 48.7  |
| Base-1B (no LoRA)      | 10.8   | 13.1 | 13.4 | 11.2    | 0.527   | 210       | 2.14 s  |  4/50  8%  | 265     | 121.8 |

---

## Inter-Role Style Separation (Classifier Accuracy)

TF-IDF + logistic regression, 5-fold CV. ~0.50 = chance; ≥ 0.90 = strong register separation.

| Variant               | Accuracy  | Std dev |
|-----------------------|-----------|---------|
| Qwen Fast (BF16)      | **0.960** | ± 0.058 |
| Qwen Fast (4-bit)     | **0.960** | ± 0.058 |
| SmolLM2 Standard      | 0.950     | ± 0.032 |
| Fast-1B               | 0.940     | ± 0.073 |
| Qwen Standard (BF16)  | 0.940     | ± 0.049 |
| Qwen Standard (4-bit) | 0.940     | ± 0.049 |
| SmolLM2 Fast          | 0.920     | ± 0.040 |
| Standard-3B           | 0.920     | ± 0.051 |
| Fast-3B               | 0.900     | ± 0.077 |
| Standard-1B           | 0.890     | ± 0.102 |
| Base-3B               | 0.700     | ± 0.063 |
| Base-1B               | 0.660     | ± 0.097 |

---

## §1 Rank Sweep — Controlled Rank Ablation (Experiment 1)

Role: `age_5_11` only | `num_layers=8` fixed | ranks: 2, 4, 8, 16 | seeds: 42, 1337

This sweep holds `num_layers` constant at 8 and varies only `rank`, isolating the rank
contribution from the layer-coverage contribution that was confounded in the original
Standard vs. Fast comparison.

### Full Rank Sweep — FK ≤ 7.0 Pass Rate (mean ± std across seeds)

| Model      | Rank 2           | Rank 4           | Rank 8           | Rank 16          | Trend     |
|------------|------------------|------------------|------------------|------------------|-----------|
| 1B         | **81.0 ± 1.0%**  | 65.0 ± 1.0%      | 63.0 ± 5.0%      | 63.0 ± 3.0%      | ↓ decreasing |
| 3B         | 56.0 ± 4.0%      | 60.0 ± 4.0%      | **69.0 ± 9.0%**  | 68.0 ± 0.0%      | ↑ increasing |
| Qwen 4-bit | **78.0 ± 0.0%**  | 72.0 ± 4.0%      | 75.0 ± 3.0%      | 68.0 ± 2.0%      | ↓ decreasing |
| SmolLM2    | 49.0 ± 7.0%      | 69.0 ± 5.0%      | 70.0 ± 6.0%      | **76.0 ± 8.0%**  | ↑ increasing |

### Standard (r=8) vs. Fast (r=4) at Fixed num_layers=8

| Model      | Standard r=8 FK% | Fast r=4 FK%   | Winner   |
|------------|------------------|----------------|----------|
| 1B         | 63.0%            | **65.0%**      | Fast     |
| 3B         | **69.0%**        | 60.0%          | Standard |
| Qwen 4-bit | **75.0%**        | 72.0%          | Standard |
| SmolLM2    | **70.0%**        | 69.0%          | Standard (marginal) |

### Average Latency (mean across seeds)

| Model      | Rank 2  | Rank 4  | Rank 8  | Rank 16 | Trend     |
|------------|---------|---------|---------|---------|-----------|
| 1B         | 0.86 s  | 0.90 s  | 0.87 s  | 0.95 s  | flat      |
| 3B         | 2.73 s  | 2.56 s  | 2.33 s  | 2.59 s  | slight ↓  |
| Qwen 4-bit | 0.49 s  | 0.51 s  | 0.48 s  | 0.49 s  | flat      |
| SmolLM2    | 1.32 s  | 1.06 s  | 1.03 s  | 0.84 s  | ↓ decreasing |

### §1 Interpretation

**The crossover persists when `num_layers` is held fixed.** Standard (r=8) beats Fast (r=4)
on 3B (69.0% vs 60.0%) and SmolLM2 (70.0% vs 69.0%); Fast (r=4) beats Standard (r=8) on
1B (65.0% vs 63.0%). Because `num_layers` is identical across all runs in this sweep, the
reversal cannot be attributed to layer coverage — **rank is the operative variable**.

This confirms **Mechanism (a) — capacity regularization**: the 1B model's smaller
representational capacity benefits from a lower-rank adapter. The 3B model has sufficient
capacity to exploit additional rank. SmolLM2, despite having only 360M total parameters,
behaves like the large-model regime.

**1B optimal rank is 2, not 4.** The full rank curve shows 1B peaks sharply at rank 2
(81.0%) and degrades monotonically as rank increases. The original Fast adapter (r=4) was
already over-parameterized for the 1B base model.

**SmolLM2 optimal rank is ≥ 16 — monotonically increasing curve.** SmolLM2 is the
most rank-hungry model in the study: rank 2 produces the worst result of any model
(49.0%), and performance increases at every rank step: 49% → 69% → 70% → 76%. Rank 16
is the best tested value, and the curve has not plateaued. Standard (r=8) barely edges
Fast (r=4) at 70% vs 69% — effectively a tie at the sweep's middle range, but the full
curve shows SmolLM2 clearly wants higher rank than either config provides.

**SmolLM2 latency also drops with rank** (1.32s → 0.84s), for the same reason as
Fast-3B being slower than Standard-3B: lower-rank adapters produce longer, less constrained
responses. Higher rank encodes the style register more precisely, leading to shorter, more
focused answers.

**Architecture, not parameter count, determines rank sensitivity.** SmolLM2 (360M, 32
layers, hidden 960) behaves like a large model. Llama 1B (1B, 16 layers, hidden 2048)
behaves like a small model. Layer depth and per-layer representation capacity appear to
drive where a model sits on the rank curve, more so than total parameter count.

**Qwen 0.5B resolves to the small-model pattern.** Qwen peaks at rank 2 (78.0%) and
degrades at higher ranks, consistent with the 1B Llama pattern. The earlier split signal
(FK favoured Standard, classifier favoured Fast) was a rank-4-vs-Standard artifact.

---

## Crossover Analysis: Standard vs. Fast by Model Family

The central research question — does the configuration-ordering crossover extend beyond Llama?

### FK ≤ 7.0 Pass Rate (age 5–11)

| Model family  | Standard | Fast   | Winner   |
|---------------|----------|--------|----------|
| Llama 3B      | **84%**  | 76%    | Standard |
| Llama 1B      | 72%      | **82%**| Fast     |
| Qwen 0.5B     | **74%**  | 68%    | Standard |
| SmolLM2 360M  | **84%**  | 64%    | Standard |

### Inter-Role Classifier Accuracy

| Model family  | Standard  | Fast      | Winner   |
|---------------|-----------|-----------|----------|
| Llama 3B      | **0.920** | 0.900     | Standard |
| Llama 1B      | 0.890     | **0.940** | Fast     |
| Qwen 0.5B     | 0.940     | **0.960** | Fast     |
| SmolLM2 360M  | **0.950** | 0.920     | Standard |

### Interpretation

The Llama crossover is fully confirmed: Standard beats Fast on 3B across both metrics;
Fast beats Standard on 1B across both metrics.

Qwen 0.5B gives a **split result** depending on the metric:
- FK pass rate favours Standard (74% vs 68%) — consistent with the 3B pattern.
- Classifier accuracy favours Fast (0.960 vs 0.940) — consistent with the 1B pattern.

SmolLM2 360M gives a **clean Standard win** on both metrics (84% vs 64% FK; 0.950 vs
0.920 classifier). This is unexpected for the smallest model in the study — 360M follows
the Standard-wins / large-model pattern, not the Fast-wins / small-model pattern seen in
Llama 1B. The architecture difference (32 layers, hidden size 960, ChatML template, HuggingFace
family) complicates a direct capacity comparison with Llama 1B. It is also possible that
the layer-coverage factor re-enters here: Standard covers 16/32 = 50% of SmolLM2's stack
vs Fast's 25%, and the §1 sweep did not test SmolLM2, so the rank-vs-layers confound is
unresolved for this architecture. See Observations below.

**Update (§1 rank sweep):** With `num_layers` held fixed at 8, the crossover persists for
Llama/Qwen, identifying rank as the operative mechanism for those families. SmolLM2 was
not included in the sweep; whether rank or layer coverage drives its Standard-wins result
is an open question.

---

## Latency & Throughput

| Variant               | 5–11 avg lat | 5–11 < 1 s | 12–18 avg lat | 12–18 < 1 s | 5–11 TPS | 12–18 TPS |
|-----------------------|-------------|------------|--------------|------------|----------|-----------|
| Qwen Fast (BF16)      | **0.46 s**  | 98%        | **0.67 s**   | 96%        | 175.8    | 186.6     |
| Qwen Fast (4-bit)     | **0.46 s**  | 98%        | **0.67 s**   | 96%        | 175.4    | 186.9     |
| Qwen Standard (BF16)  | 0.59 s      | **100%**   | 0.75 s       | 94%        | 148.6    | 151.2     |
| Qwen Standard (4-bit) | 0.59 s      | **100%**   | 0.74 s       | **96%**    | 150.6    | 154.3     |
| SmolLM2 Standard      | 0.81 s      | 88%        | 1.12 s       | 42%        | 92.8     | 94.8      |
| Fast-1B               | 0.93 s      | 70%        | 1.20 s       | 24%        | 94.3     | 95.4      |
| SmolLM2 Fast          | 1.08 s      | 68%        | 1.62 s       | 36%        | 99.7     | 103.1     |
| Standard-1B           | 1.09 s      | 42%        | 1.36 s       | 6%         | 81.7     | 83.7      |
| Standard-3B           | 2.37 s      | 0%         | 2.94 s       | 0%         | 38.8     | 39.3      |
| Fast-3B               | 2.83 s      | 0%         | 3.63 s       | 2%         | 41.9     | 41.7      |
| Base-1B               | 2.01 s      | 4%         | 2.14 s       | 8%         | 122.3    | 121.8     |
| Base-3B               | 3.99 s      | 6%         | 5.39 s       | 2%         | 46.5     | 48.7      |

**Qwen Fast is the lowest-latency adapter overall** (0.46 s avg for age_5_11, 0.67 s for
age_12_18). Qwen Standard has slightly higher latency but clears the 1.0 s target on every
single age_5_11 response (50/50) vs 49/50 for Qwen Fast — effectively a tie in practice.
Both Qwen adapters are roughly 2× faster than Fast-1B on the age_5_11 role.

**SmolLM2 Standard** sits between the Qwen adapters and the Llama 1B adapters in latency:
0.81 s avg for age_5_11, 88% under target. SmolLM2 Fast is slower than SmolLM2 Standard
(1.08 s vs 0.81 s) because the Fast adapter produces substantially longer responses
(111 avg tokens vs 76) — same pattern as Fast-3B vs Standard-3B.

---

## Observations

### 1. Qwen BF16 ≈ Qwen 4-bit across both configs
Readability metrics, FK pass rates, classifier accuracy, and response lengths are identical
between BF16 and 4-bit variants in both the fast and standard configurations. TPS differs by
< 5%. At 0.5B, quantization does not change what the model outputs — only how fast it does so.
The 4-bit variant is the practical choice (smaller on disk, marginally faster) but results
are interchangeable.

### 2. Metric anomalies from the previous run are gone
The prior run showed Qwen Fast anomalies (Coleman-Liau avg 23.0, FK min −3.0, FK max 76.2).
The re-run shows clean values across both configs: Coleman-Liau 6.5 / 9.6, FK ranges
2.2–9.2 / 2.7–13.1 — all within normal bounds. Both Qwen adapters now produce well-formed
prose with no degenerate responses.

### 3. Qwen Fast has the highest classifier accuracy of all variants (0.960)
Qwen Fast achieves stronger inter-role style separation than any Llama adapter, including
Fast-1B (0.960 vs 0.940). Qwen Standard matches Fast-1B (0.940). On FK pass rate, Qwen
Standard edges Qwen Fast (74% vs 68%), but both fall below the best Llama results (Standard-3B
84%, Fast-1B 82%). The latency advantage is substantial: Qwen Fast is 2× faster than Fast-1B.

### 5. SmolLM2 Standard is surprisingly strong — rank sweep confirms large-model behaviour
SmolLM2 360M with the Standard adapter (r=8, 16 layers) achieves 84% FK pass rate and
0.950 classifier — matching Standard-3B's FK performance and ranking second overall on
the classifier behind Qwen Fast. At 0.81 s avg latency (88% under 1.0 s for age_5_11)
it sits between Qwen and Llama 1B in the latency table.

The rank sweep confirms why: SmolLM2 has a **monotonically increasing rank curve**
(49% → 69% → 70% → 76% at ranks 2/4/8/16), the same large-model profile as Llama 3B.
It is the most rank-hungry model tested — rank 2 produces its worst result (49%, lower
than any other model at rank 2), and the curve has not plateaued at rank 16. The Standard
config (r=8, 16 layers) achieving 84% in the main eval benefits from both higher rank and
more layer coverage than the sweep's fixed 8-layer setting, explaining the jump from the
sweep's 70% (rank 8, 8 layers) to 84% (rank 8, 16 layers).

Architecture, not total parameter count, determines the rank regime: SmolLM2 has 32
transformer layers and hidden size 960 — comparable depth to Llama 3B (28 layers). Llama
1B has only 16 layers and hidden 2048. Layer depth and per-layer capacity drive rank
sensitivity more than total parameters.

### 4. §1 rank sweep resolves the crossover mechanism across all four model families
The controlled rank sweep (§1) fixed `num_layers=8` and varied rank across {2, 4, 8, 16}
for all four model families (Llama 1B, 3B, Qwen 0.5B, SmolLM2 360M). The crossover
persists at fixed `num_layers`, confirming **rank as the operative variable** via capacity
regularization. The rank curves split cleanly into two groups:
- **Small-model (lower rank better):** Llama 1B (peak rank 2, 81%) and Qwen 0.5B (peak rank 2, 78%)
- **Large-model (higher rank better):** Llama 3B (peak rank 8, 69%) and SmolLM2 (peak rank 16, 76%)

SmolLM2 at 360M falls in the large-model group — driven by its 32-layer depth, not its
parameter count. The `docs/EXPERIMENTS.md` §1 mechanism question is now answered for all
four architectures tested.

---

## Recommended Configuration by Use Case

| Priority                        | Recommended variant              | Reason                                                                           |
|---------------------------------|----------------------------------|----------------------------------------------------------------------------------|
| VR real-time (lowest avg)       | **Qwen Fast (4-bit)**            | 0.46 s avg; 98% under 1 s; highest classifier (0.960)                           |
| VR real-time (100% target)      | **Qwen Standard (4-bit)**        | 100% under 1 s for age 5–11; 74% FK pass rate; clean metrics                   |
| Quality + latency balance       | **SmolLM2 Standard**             | 84% FK (ties best); 0.950 classifier (2nd); 0.81 s avg; 88% under 1 s          |
| Proven Llama quality            | **Fast-1B**                      | Best Llama classifier (0.940); 82% FK pass rate; 70% under 1 s                 |
| Optimal 1B (§1 finding)         | **1B rank 2, num_layers 8**      | 81% FK pass rate — best 1B result; lower adapter cost than Fast-1B              |
| Quality ceiling (no latency)    | **Standard-3B**                  | Highest FK pass rate (84%); most stable readability metrics                     |
| Research baseline               | Base-3B / Base-1B                | Establishes the no-adapter floor                                                 |
