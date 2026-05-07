# Layer Sweep Results — rank=4 fixed, num_layers ∈ {4, 8, 16}

Models: Llama 1B, Llama 3B | Role: `age_5_11` | FK target: ≤ 7.0 | rank=4 (fixed)

num_layers=8 reuses rank sweep adapters (no additional training).

## Per-Run Results

Model  Layers   Seed  FK avg    FK ≤ 7.0   Avg lat      TPS
-----------------------------------------------------------
1b          4     42    6.06   40/50   80.0%     0.92s    102.6
1b          4   1337    6.26   35/50   70.0%     0.92s    100.6
1b          8     42    6.26   34/50   68.0%     0.93s     92.5
1b          8   1337    6.30   33/50   66.0%     0.93s     94.6
1b         16     42    6.33   37/50   74.0%     1.10s     83.7
1b         16   1337    6.60   34/50   68.0%     1.05s     83.0

3b          4     42    6.58   26/50   52.0%     2.56s     44.6
3b          4   1337    6.34   32/50   64.0%     2.34s     44.4
3b          8     42    6.74   30/50   60.0%     2.62s     42.2
3b          8   1337    6.51   28/50   56.0%     2.56s     42.2
3b         16     42    6.53   32/50   64.0%     2.24s     38.1
3b         16   1337    6.51   33/50   66.0%     2.15s     38.6


## Aggregated (mean ± std across seeds)

Model  Layers        FK avg    FK ≤ 7.0 %       Avg lat         TPS
-------------------------------------------------------------------
1b          4   6.16 ± 0.10    75.0 ± 5.0  0.92s ± 0.00  101.6 ± 1.0
1b          8   6.28 ± 0.02    67.0 ± 1.0  0.93s ± 0.00  93.5 ± 1.0
1b         16   6.46 ± 0.13    71.0 ± 3.0  1.07s ± 0.03  83.4 ± 0.4

3b          4   6.46 ± 0.12    58.0 ± 6.0  2.45s ± 0.11  44.5 ± 0.1
3b          8   6.62 ± 0.11    58.0 ± 2.0  2.59s ± 0.03  42.2 ± 0.0
3b         16   6.52 ± 0.01    65.0 ± 1.0  2.20s ± 0.05  38.4 ± 0.3


## Effect of num_layers at rank=4

Comparison of interest: layers=8 (Fast original) vs layers=16 (Standard original) at fixed rank=4.
Also includes layers=4 to show the lower end of the range.

Model     L=4 FK%    L=8 FK%    L=16 FK%    L=8→16 Δ    Winner (8 vs 16)
----------------------------------------------------------------------
1b          75.0%      67.0%       71.0%       +4.0%           layers=16
3b          58.0%      58.0%       65.0%       +7.0%           layers=16

Interpretation: if layers=16 >> layers=8 at fixed rank=4, num_layers
is an independent contributor to the crossover beyond rank alone.