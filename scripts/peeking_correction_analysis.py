"""
Two-stage (interim-look) correction for the 3B seed-campaign comparison.

The 3B campaign's n was raised from 15 to 30/config after a preliminary batch left the
comparison marginal (t=2.01, p=0.054). Because that extension decision was itself informed
by an unblinded interim look at the data, the naive pooled t-test on the resulting n=30 is
anti-conservative. This computes the valid alternative: a pre-specified equal-weight
inverse-normal combination test (Bauer-Kohne / Lehmacher-Wassmer style) combining the
interim-stage result with the independent 15-seed replication collected afterward.

Batch membership comes from scripts/gen_seed_campaign_configs.py (SEEDS_3B, the first 15
seeds) and scripts/gen_seed_campaign_batch2_3b.py (NEW_SEEDS, the 15 top-up seeds).
"""
import csv, re
import numpy as np
from scipy import stats

rows = list(csv.DictReader(open("results/seed_campaign/summary.csv")))
BATCH1 = {42, 1337, 7, 123, 256, 512, 777, 999, 2024, 2025, 3141, 8888, 31415, 55555, 100}
BATCH2 = {200, 300, 400, 500, 600, 700, 800, 900, 1000, 1111, 4242, 13370, 65537, 271828, 314159}


def vals(cfg, seedset=None):
    out = []
    for r in rows:
        if re.match(cfg + "_seed", r["config"]):
            s = int(r["seed"])
            if seedset is None or s in seedset:
                out.append(float(r["fk_pass_rate"]))
    return np.array(out)


std_b1, fast_b1 = vals("standard_3b", BATCH1), vals("fast_3b", BATCH1)
std_b2, fast_b2 = vals("standard_3b", BATCH2), vals("fast_3b", BATCH2)
std_all, fast_all = vals("standard_3b"), vals("fast_3b")

t1, p1_two = stats.ttest_ind(std_b1, fast_b1)
t2, p2_two = stats.ttest_ind(std_b2, fast_b2)
t_all, p_all_two = stats.ttest_ind(std_all, fast_all)

p1_one = p1_two / 2 if t1 > 0 else 1 - p1_two / 2
p2_one = p2_two / 2 if t2 > 0 else 1 - p2_two / 2
z1, z2 = stats.norm.ppf(1 - p1_one), stats.norm.ppf(1 - p2_one)
w = 1 / np.sqrt(2)
z_comb = w * z1 + w * z2
p_comb_one = 1 - stats.norm.cdf(z_comb)

print(f"Stage 1 (interim, n=15/arm):  t={t1:.3f}  p_two={p1_two:.4f}")
print(f"Stage 2 (fresh replication, n=15/arm):  t={t2:.3f}  p_two={p2_two:.4f}")
print(f"Naive pooled (n=30/arm, what the paper used to report):  t={t_all:.3f}  p_two={p_all_two:.6f}")
print(f"Combination test:  z1={z1:.3f}  z2={z2:.3f}  z_combined={z_comb:.3f}")
print(f"  one-sided p={p_comb_one:.6f}  two-sided-equivalent p={2*p_comb_one:.6f}")
