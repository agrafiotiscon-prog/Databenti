---
type: result
date: 2026-10-04
tags: [R9, H-039, gates]
---
# H-039 quarter-end USD funding: gate verdict **insufficient data**

Quarter-end dollar funding squeeze - long USD (short foreign-currency futures) over the last days of each calendar quarter. 3968 dates 2010-06-07..2025-09-30; 13 folds (3 y / 1 y). DSR N = 229. Capital $1,000,000. short FX futures (long USD) into quarter-end, 1 tick + fees.

## Coverage (before P&L, D-042)
```
market  quarter_ends  windows_k5  other_month_ends
    6E            62          62               122
    6J            62          62               122
    6B            62          62               122
    6A            62          62               122
    6C            62          62               122
    6S            62          62               122
```

OOS (walk-forward): {'ann_return_pct': -0.23, 'ann_vol_pct': 1.53, 'sharpe': -0.149, 'max_dd_pct': -7.51, 't_daily': -0.528}
OOS contract trades: 180

## Gates
```
                                                          requirement result                                                    evidence
gate                                                                                                                                    
G1                                                  >= 200 OOS trades   FAIL                                              oos_trades=180
G2                                OOS net > 0 at 1.5x fees and 250 ms   FAIL                          oos_net_stress=-35423.005000000034
G3                      DSR >= 0.95 (raw N) and OOS mean-trade t >= 2   FAIL                  dsr_raw=0.031136899098135884, oos_t=-0.528
G4                                                        PBO <= 0.10   FAIL                                      pbo=0.2306915306915307
G5                                                 +-20% plateau test   FAIL                                          plateau_pass=False
G6                                 not concentrated (red flags clear)   FAIL                                           concentrated=True
G7                       positive in >= 60% of OOS years (>= 2 years)   PASS         years_positive_share=0.6153846153846154, n_years=13
G8                           tier-B fill check does not flip the sign   FAIL                                      tier_b_same_sign=False
G9                 MC 5th pct net > 0 and P(loss) <= 10% at 1.5x fees   FAIL               mc_net_p5=-130890.04500000046, mc_p_loss=0.68
G10   cluster medoid; >= 70% of its cluster profitable; not an island   FAIL  is_medoid=False, cluster_share_profitable=0.5, island=True
G11                        DSR >= 0.95 with cluster-based effective K   FAIL                                   dsr_k=0.20040916804207098
G12   beats a placebo / random-timing benchmark (one-sided p <= 0.05)   FAIL                                               placebo_p=1.0
```

Placebo: real OOS net -28,650 vs placebo median 51,011 (95th pct 84,468); p = 1.000

Net by scenario (OOS): {'base': -28650, 'fees1.5': -29703, 'stress': -35423, 'plus1tick': -34370}

### By year (OOS)
```
      oos_net  return_pct
2013   3761.0        0.38
2014   6662.0        0.67
2015  12505.0        1.25
2016 -10911.0       -1.09
2017 -11737.0       -1.17
2018  21088.0        2.11
2019   8600.0        0.86
2020 -45567.0       -4.56
2021  17181.0        1.72
2022 -31689.0       -3.17
2023   5850.0        0.58
2024   5147.0        0.51
2025  -9539.0       -0.95
```

## Variant chosen per fold
```
 fold                   test variant  train_net_p5
    0 2013-06-04..2014-05-30    3|g3        -49706
    1 2014-06-03..2015-05-29    3|g3        -15035
    2 2015-06-02..2016-05-31    3|g3         -8715
    3 2016-06-02..2017-05-31    3|g3        -16066
    4 2017-06-02..2018-05-31    3|g3        -24765
    5 2018-06-04..2019-05-31    5|g3        -29232
    6 2019-06-04..2020-05-29    5|g3        -12846
    7 2020-06-02..2021-05-31    3|g3        -50653
    8 2021-06-02..2022-05-31    3|g3        -52967
    9 2022-06-02..2023-05-31    3|g3        -57127
   10 2023-06-02..2024-05-31    5|g6        -32222
   11 2024-06-04..2025-05-30    5|g6        -20583
   12 2025-06-03..2025-09-30    5|g6        -23783
```

## Family (full period): PBO = 0.231, K = 2
```
      ann_return_pct  ann_vol_pct  sharpe  max_dd_pct  t_daily  net_full  trades
3|g3           -0.29         1.28  -0.223       -5.96   -0.886  -44971.0   186.0
3|g6           -0.36         1.22  -0.298       -6.95   -1.183  -57317.0   372.0
5|g3            0.00         1.71   0.002       -5.10    0.008     577.0   186.0
5|g6           -0.20         1.59  -0.124       -4.89   -0.493  -31062.0   372.0
```

