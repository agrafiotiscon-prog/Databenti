---
type: result
date: 2026-10-04
tags: [R9, H-037, gates]
---
# H-037 FX month-end hedge rebalancing: gate verdict **not promising**

FX month-end hedge rebalancing - sell USD (long foreign-currency futures) into month-end after US equities rose during the month, buy USD after they fell. 3968 dates 2010-06-07..2025-09-30; 13 folds (3 y / 1 y). DSR N = 229. Capital $1,000,000. outright FX, side = sign(ES MTD), 1 tick + fees per side.

## Coverage (before P&L, D-042)
```
market      first       last  events_on_market_k3  es_events_k3
    6E 2010-06-07 2025-09-30                  183           183
    6J 2010-06-07 2025-09-30                  183           183
    6B 2010-06-07 2025-09-30                  183           183
    6A 2010-06-07 2025-09-30                  183           183
    6C 2010-06-07 2025-09-30                  183           183
    6S 2010-06-07 2025-09-30                  183           183
```

OOS (walk-forward): {'ann_return_pct': 0.62, 'ann_vol_pct': 2.35, 'sharpe': 0.262, 'max_dd_pct': -4.24, 't_daily': 0.932}
OOS contract trades: 672

## Gates
```
                                                          requirement result                                                     evidence
gate                                                                                                                                     
G1                                                  >= 200 OOS trades   PASS                                               oos_trades=672
G2                                OOS net > 0 at 1.5x fees and 250 ms   PASS                            oos_net_stress=58005.029999999846
G3                      DSR >= 0.95 (raw N) and OOS mean-trade t >= 2   FAIL                      dsr_raw=0.5955621208666283, oos_t=0.932
G4                                                        PBO <= 0.10   FAIL                                       pbo=0.6491841491841492
G5                                                 +-20% plateau test   PASS                                            plateau_pass=True
G6                                 not concentrated (red flags clear)   FAIL                                            concentrated=True
G7                       positive in >= 60% of OOS years (>= 2 years)   PASS          years_positive_share=0.6923076923076923, n_years=13
G8                           tier-B fill check does not flip the sign   PASS                                        tier_b_same_sign=True
G9                 MC 5th pct net > 0 and P(loss) <= 10% at 1.5x fees   FAIL                mc_net_p5=-70203.57924999892, mc_p_loss=0.195
G10   cluster medoid; >= 70% of its cluster profitable; not an island   FAIL  is_medoid=False, cluster_share_profitable=1.0, island=False
G11                        DSR >= 0.95 with cluster-based effective K   FAIL                                     dsr_k=0.7954881313489226
G12   beats a placebo / random-timing benchmark (one-sided p <= 0.05)   FAIL                               placebo_p=0.056666666666666664
```

Placebo: real OOS net 77,805 vs placebo median -71,625 (95th pct 80,464); p = 0.057

Net by scenario (OOS): {'base': 77805, 'fees1.5': 74653, 'stress': 58005, 'plus1tick': 61158}

### By year (OOS)
```
      oos_net  return_pct
2013  20047.0        2.00
2014   7736.0        0.77
2015   2134.0        0.21
2016  -9329.0       -0.93
2017  37808.0        3.78
2018  -4531.0       -0.45
2019   8307.0        0.83
2020    380.0        0.04
2021  -4533.0       -0.45
2022  16704.0        1.67
2023  18220.0        1.82
2024   2611.0        0.26
2025 -17750.0       -1.78
```

## Variant chosen per fold
```
 fold                   test variant  train_net_p5
    0 2013-06-04..2014-05-30    5|g3         -5311
    1 2014-06-03..2015-05-29    5|g3          3737
    2 2015-06-02..2016-05-31    3|g6          7219
    3 2016-06-02..2017-05-31    5|g3          7458
    4 2017-06-02..2018-05-31    3|g3          5727
    5 2018-06-04..2019-05-31    3|g3         40060
    6 2019-06-04..2020-05-29    3|g3          3260
    7 2020-06-02..2021-05-31    3|g6         -5556
    8 2021-06-02..2022-05-31    3|g6        -62657
    9 2022-06-02..2023-05-31    3|g6        -26673
   10 2023-06-02..2024-05-31    5|g6        -26577
   11 2024-06-04..2025-05-30    5|g6          8575
   12 2025-06-03..2025-09-30    5|g6        -39636
```

## Family (full period): PBO = 0.649, K = 2
```
      ann_return_pct  ann_vol_pct  sharpe  max_dd_pct  t_daily  net_full  trades
3|g3            1.17         2.33   0.500       -7.95    1.986  183939.0   549.0
3|g6            1.14         2.15   0.528       -5.22    2.096  178803.0  1098.0
5|g3            1.24         2.93   0.421       -4.44    1.673  194523.0   549.0
5|g6            1.01         2.67   0.379       -4.53    1.504  159567.0  1098.0
```

