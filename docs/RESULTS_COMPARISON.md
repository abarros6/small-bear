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
| Qwen Standard (BF16)   | 5.8    | 42/50 84% | 8.4  | 7.5  | 6.5     | 0.689   | 75        | 0.58 s  | 50/50 100% | 90      | 153.5 |
| Qwen Standard (4-bit)  | 5.8    | 42/50 84% | 8.4  | 7.5  | 6.5     | 0.689   | 75        | 0.58 s  | 50/50 100% | 90      | 152.8 |
| Qwen Fast (BF16)       | 4.7    | 48/50 96% | 7.5  | 6.6  | 23.0 ⚠  | 0.539   | 98        | 0.70 s  | 39/50 78%  | 131     | 177.5 |
| Qwen Fast (4-bit)      | 4.7    | 48/50 96% | 7.5  | 6.6  | 23.0 ⚠  | 0.539   | 98        | 0.68 s  | 39/50 78%  | 131     | 184.7 |
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
| Qwen Standard (BF16)   | 8.2    | 11.1 | 10.6 | 10.0    | 0.667   | 84        | 0.69 s  | 49/50 98%  | 108     | 155.7 |
| Qwen Standard (4-bit)  | 8.2    | 11.1 | 10.6 | 10.0    | 0.667   | 84        | 0.69 s  | 49/50 98%  | 108     | 155.3 |
| Qwen Fast (BF16)       | 8.8    | 10.5 | 11.0 | 11.2    | 0.521   | 109       | 0.73 s  | 41/50 82%  | 140     | 186.9 |
| Qwen Fast (4-bit)      | 8.8    | 10.5 | 11.0 | 11.2    | 0.521   | 109       | 0.73 s  | 41/50 82%  | 140     | 187.6 |
| Base-3B (no LoRA)      | 10.6   | 12.9 | 13.3 | 11.4    | 0.565   | 206       | 5.39 s  |  1/50  2%  | 264     | 48.7  |
| Base-1B (no LoRA)      | 10.8   | 13.1 | 13.4 | 11.2    | 0.527   | 210       | 2.14 s  |  4/50  8%  | 265     | 121.8 |

---

## Inter-Role Style Separation (Classifier Accuracy)

TF-IDF + logistic regression, 5-fold CV. ~0.50 = chance; ≥ 0.90 = strong register separation.

| Variant               | Accuracy | Std dev |
|-----------------------|----------|---------|
| Fast-1B               | **0.940**| ± 0.073 |
| Standard-3B           | 0.920    | ± 0.051 |
| Qwen Standard (BF16)  | 0.920    | ± 0.093 |
| Qwen Standard (4-bit) | 0.920    | ± 0.093 |
| Fast-3B               | 0.900    | ± 0.077 |
| Standard-1B           | 0.890    | ± 0.102 |
| Qwen Fast (BF16)      | 0.860    | ± 0.092 |
| Qwen Fast (4-bit)     | 0.860    | ± 0.092 |
| Base-3B               | 0.700    | ± 0.063 |
| Base-1B               | 0.660    | ± 0.097 |

---

## Crossover Analysis: Standard vs. Fast by Model Family

The central research question — does the configuration-ordering crossover extend beyond Llama?

### FK ≤ 7.0 Pass Rate (age 5–11)

| Model family | Standard | Fast   | Winner   |
|--------------|----------|--------|----------|
| Llama 3B     | **84%**  | 76%    | Standard |
| Llama 1B     | 72%      | **82%**| Fast     |
| Qwen 0.5B    | 84%      | **96%**| Fast ⚠  |

### Inter-Role Classifier Accuracy

| Model family | Standard  | Fast      | Winner   |
|--------------|-----------|-----------|----------|
| Llama 3B     | **0.920** | 0.900     | Standard |
| Llama 1B     | 0.890     | **0.940** | Fast     |
| Qwen 0.5B    | **0.920** | 0.860     | Standard |

### Interpretation

The Llama crossover is fully confirmed: Standard beats Fast on 3B across both metrics;
Fast beats Standard on 1B across both metrics.

Qwen 0.5B gives a **split result** depending on the metric:
- FK pass rate favours Fast (96% vs 84%) — consistent with the 1B pattern and the hypothesis
  that smaller models benefit more from the fast config.
- Classifier accuracy favours Standard (0.920 vs 0.860) — consistent with the 3B pattern
  and opposite to what model size would predict.

The split is likely explained by the metric anomalies in Qwen Fast outputs (Coleman-Liau 23.0,
FK min −3.0, FK max 76.2 — see Observations below). Qwen Fast appears to generate some
responses that are unusually short or poorly formatted, which artificially deflates FK grades
and inflates the pass rate. Qwen Standard produces clean metric values across the board,
suggesting the standard config is the more reliable Qwen adapter. **The FK advantage of Qwen
Fast should not be taken at face value without manual inspection of the outlier responses.**

---

## Latency & Throughput

| Variant               | 5–11 avg lat | 5–11 < 1 s | 12–18 avg lat | 12–18 < 1 s | 5–11 TPS | 12–18 TPS |
|-----------------------|-------------|------------|--------------|------------|----------|-----------|
| Qwen Standard (BF16)  | **0.58 s**  | **100%**   | **0.69 s**   | **98%**    | 153.5    | 155.7     |
| Qwen Standard (4-bit) | **0.58 s**  | **100%**   | **0.69 s**   | **98%**    | 152.8    | 155.3     |
| Qwen Fast (BF16)      | 0.70 s      | 78%        | 0.73 s       | 82%        | 177.5    | 186.9     |
| Qwen Fast (4-bit)     | 0.68 s      | 78%        | 0.73 s       | 82%        | 184.7    | 187.6     |
| Fast-1B               | 0.93 s      | 70%        | 1.20 s       | 24%        | 94.3     | 95.4      |
| Standard-1B           | 1.09 s      | 42%        | 1.36 s       | 6%         | 81.7     | 83.7      |
| Standard-3B           | 2.37 s      | 0%         | 2.94 s       | 0%         | 38.8     | 39.3      |
| Fast-3B               | 2.83 s      | 0%         | 3.63 s       | 2%         | 41.9     | 41.7      |
| Base-1B               | 2.01 s      | 4%         | 2.14 s       | 8%         | 122.3    | 121.8     |
| Base-3B               | 3.99 s      | 6%         | 5.39 s       | 2%         | 46.5     | 48.7      |

**Qwen Standard is the fastest adapter overall**, clearing the 1.0 s VR target on every single
age_5_11 response (50/50) and 98% of age_12_18 responses — despite having higher rank and more
adapted layers than Qwen Fast. The reason: Standard produces shorter responses (75 vs 98 avg
words), so even with lower TPS it finishes sooner. The same token-length effect was observed
with Fast-3B being slower than Standard-3B.

---

## Observations

### 1. Qwen BF16 ≈ Qwen 4-bit across both configs
Readability metrics, FK pass rates, classifier accuracy, and response lengths are identical
between BF16 and 4-bit variants in both the fast and standard configurations. TPS differs by
< 5%. At 0.5B, quantization does not change what the model outputs — only how fast it does so.
The 4-bit variant is the practical choice (smaller on disk, marginally faster) but results
are interchangeable.

### 2. Qwen Fast has metric anomalies; Qwen Standard does not
Qwen Fast outputs show three abnormal values absent from all other variants:
- **Coleman-Liau avg 23.0** (normal range: 0–20) — indicates sentence segmentation failure,
  likely from Qwen Fast using bullet lists or non-prose formatting.
- **FK min −3.0** — at least one response is trivially short or non-prose.
- **FK max 76.2 (age 12–18)** — a clear degenerate response.

Qwen Standard shows none of these: Coleman-Liau 6.5 / 10.0, FK min 2.4 / 4.3,
FK max 9.2 / 12.4 — all within expected ranges. The standard config (more parameters,
more layers) appears to produce more stable, well-formed prose from this model.

### 3. Qwen Standard is a strong all-around performer
Qwen Standard (BF16 or 4-bit) matches Standard-3B on FK pass rate (84%) and classifier
accuracy (0.920), while being 4× faster (0.58 s vs 2.37 s avg) and clearing the 1.0 s
target 100% of the time. It also matches Llama metrics without any anomalies. For a 0.5B
model, this is a strong result.

### 4. The Llama crossover mechanism remains unresolved
Adding Qwen does not clarify whether rank or num_layers drives the crossover, since both
co-vary between Standard and Fast configs. The Qwen result muddies the picture further:
the metric that tracks the crossover (FK or classifier) determines whether Qwen 0.5B
looks like a 1B (Fast wins) or a 3B (Standard wins). See `docs/EXPERIMENTS.md` §1 for
the controlled single-variable ablation needed to resolve this.

---

## Recommended Configuration by Use Case

| Priority             | Recommended variant      | Reason                                                        |
|----------------------|--------------------------|---------------------------------------------------------------|
| VR real-time         | **Qwen Standard (4-bit)**| 100%/98% under 1 s; clean metrics; matches 3B quality at 0.5B|
| Proven Llama quality | **Fast-1B**              | Best Llama classifier (0.940); 70% under 1 s on age 5–11     |
| Quality ceiling      | **Standard-3B**          | Highest readability consistency; most stable metrics          |
| Research baseline    | Base-3B / Base-1B        | Establishes the no-adapter floor                              |
