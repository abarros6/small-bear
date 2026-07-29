import json, glob, re
import numpy as np
import textstat
from scipy import stats
from sklearn.linear_model import LogisticRegression

def load_examples(pattern):
    rows = []
    for fp in glob.glob(pattern):
        m = re.match(r".*/(fast|standard)_(1b|3b)_seed(\d+)_age_5_11_outputs\.jsonl", fp)
        if not m:
            continue
        cfg, size, seed = m.group(1), m.group(2), int(m.group(3))
        with open(fp) as f:
            for line in f:
                ex = json.loads(line)
                resp = ex["response"]
                wc = textstat.lexicon_count(resp, removepunct=True)
                fk = textstat.flesch_kincaid_grade(resp)
                rows.append(dict(config=cfg, size=size, seed=seed, word_count=wc, fk=fk, fk_pass=1 if fk <= 7.0 else 0))
    return rows

rows = load_examples("outputs/seed_campaign/*.jsonl")
print("total examples:", len(rows))

import collections
by_size = collections.defaultdict(list)
for r in rows:
    by_size[r["size"]].append(r)

for size in ["1b", "3b"]:
    data = by_size[size]
    fast = [r for r in data if r["config"] == "fast"]
    std  = [r for r in data if r["config"] == "standard"]
    wc_fast = np.array([r["word_count"] for r in fast])
    wc_std  = np.array([r["word_count"] for r in std])
    fk_fast = np.array([r["fk"] for r in fast])
    fk_std  = np.array([r["fk"] for r in std])
    pass_fast = np.array([r["fk_pass"] for r in fast])
    pass_std  = np.array([r["fk_pass"] for r in std])

    print(f"\n=== {size.upper()} ===")
    print(f"n_fast={len(fast)} n_std={len(std)}")
    print(f"avg word count: fast={wc_fast.mean():.1f} std={wc_std.mean():.1f}")
    t_wc, p_wc = stats.ttest_ind(wc_fast, wc_std)
    print(f"word-count t-test: t={t_wc:.2f} p={p_wc:.2e}")

    print(f"raw FK pass rate: fast={pass_fast.mean()*100:.1f}% std={pass_std.mean()*100:.1f}%")

    # length-adjusted: residualize FK grade on word count (pooled), compare residuals
    all_wc = np.concatenate([wc_fast, wc_std])
    all_fk = np.concatenate([fk_fast, fk_std])
    all_cfg = np.array([1]*len(fast) + [0]*len(std))  # 1=fast, 0=standard
    # linear regression fk ~ word_count (pooled, config-blind)
    A = np.vstack([all_wc, np.ones_like(all_wc)]).T
    coef, *_ = np.linalg.lstsq(A, all_fk, rcond=None)
    slope, intercept = coef
    pred = slope*all_wc + intercept
    resid = all_fk - pred
    resid_fast = resid[all_cfg == 1]
    resid_std = resid[all_cfg == 0]
    t_resid, p_resid = stats.ttest_ind(resid_fast, resid_std)
    print(f"FK~word_count slope={slope:.4f} (per word)")
    print(f"length-adjusted FK residual: fast_mean={resid_fast.mean():.3f} std_mean={resid_std.mean():.3f}")
    print(f"length-adjusted t-test: t={t_resid:.2f} p={p_resid:.2e}")

    # logistic regression: fk_pass ~ config + word_count
    X = np.column_stack([all_cfg, all_wc])
    y = np.concatenate([pass_fast, pass_std])
    clf = LogisticRegression()
    clf.fit(X, y)
    print(f"logistic coef (config, word_count): {clf.coef_[0]}")
    # naive t-test on raw pass rate for reference
    t_raw, p_raw = stats.ttest_ind(pass_fast, pass_std)
    print(f"raw pass-rate t-test (example-level, not run-level): t={t_raw:.2f} p={p_raw:.2e}")
