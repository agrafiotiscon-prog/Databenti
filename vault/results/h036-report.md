---
type: result
date: 2026-10-04
tags: [R9, H-036, gates]
---
# H-036 volatility-managed trend: gate verdict **not promising**

Volatility-managed trend - the trend252 portfolio with a short-window book volatility target (21/63/126 days instead of 252). 3980 dates 2010-06-07..2025-09-30; 13 folds (3 y / 1 y). DSR N = 217. Capital $1,000,000. trend252 engine, book vol target on scale_win days, 1 tick + fees.

## Coverage (before P&L, D-042)
```
 markets      first       last  days
      26 2010-06-07 2025-09-30  3980
```

OOS (walk-forward): {'ann_return_pct': 6.19, 'ann_vol_pct': 16.42, 'sharpe': 0.377, 'max_dd_pct': -43.3, 't_daily': 1.343}
OOS contract trades: 9767

## Gates
```
                                                          requirement result                                                    evidence
gate                                                                                                                                    
G1                                                  >= 200 OOS trades   PASS                                             oos_trades=9767
G2                                OOS net > 0 at 1.5x fees and 250 ms   PASS                            oos_net_stress=536719.2999999989
G3                      DSR >= 0.95 (raw N) and OOS mean-trade t >= 2   FAIL                     dsr_raw=0.8583748487947186, oos_t=1.343
G4                                                        PBO <= 0.10   FAIL                                       pbo=0.937995337995338
G5                                                 +-20% plateau test   PASS                                           plateau_pass=True
G6                                 not concentrated (red flags clear)   PASS                                          concentrated=False
G7                       positive in >= 60% of OOS years (>= 2 years)   FAIL         years_positive_share=0.5384615384615384, n_years=13
G8                           tier-B fill check does not flip the sign   PASS                                       tier_b_same_sign=True
G9                 MC 5th pct net > 0 and P(loss) <= 10% at 1.5x fees   FAIL              mc_net_p5=-237124.72387500058, mc_p_loss=0.097
G10   cluster medoid; >= 70% of its cluster profitable; not an island   PASS  is_medoid=True, cluster_share_profitable=1.0, island=False
G11                        DSR >= 0.95 with cluster-based effective K   FAIL                                    dsr_k=0.8986207475325242
G12   beats a placebo / random-timing benchmark (one-sided p <= 0.05)   FAIL                               placebo_p=0.24666666666666667
```

Placebo: real OOS net 784,182 vs placebo median 338,245 (95th pct 1,264,095); p = 0.247

Net by scenario (OOS): {'base': 784182, 'fees1.5': 757089, 'stress': 536719, 'plus1tick': 563813}

### By year (OOS)
```
       oos_net  return_pct
2013  175539.0       17.55
2014  389997.0       39.00
2015   97601.0        9.76
2016 -299874.0      -29.99
2017   85039.0        8.50
2018  -55437.0       -5.54
2019  -51465.0       -5.15
2020  351279.0       35.13
2021  -47957.0       -4.80
2022  287661.0       28.77
2023 -153721.0      -15.37
2024  113911.0       11.39
2025 -108390.0      -10.84
```

## Variant chosen per fold
```
 fold                   test variant  train_net_p5
    0 2013-06-04..2014-05-30     126       -316120
    1 2014-06-03..2015-05-29     126       -367510
    2 2015-06-02..2016-05-31      21         80535
    3 2016-06-02..2017-05-31      21        104475
    4 2017-06-02..2018-05-31      63       -336713
    5 2018-06-04..2019-05-31      21       -579702
    6 2019-06-04..2020-05-29     126       -527668
    7 2020-06-02..2021-05-31      21       -117454
    8 2021-06-02..2022-05-31      63       -169408
    9 2022-06-02..2023-05-31     126         -7617
   10 2023-06-02..2024-05-31     126        -49930
   11 2024-06-04..2025-05-30     126       -267466
   12 2025-06-03..2025-09-30      63       -521026
```

## Family (full period): PBO = 0.938, K = 2
```
     ann_return_pct  ann_vol_pct  sharpe  max_dd_pct  t_daily   net_full   trades
21             6.01        16.66   0.361      -42.28    1.434   949667.0  15720.0
63             6.57        16.00   0.411      -38.78    1.632  1037924.0  10939.0
126            6.48        16.08   0.403      -39.46    1.601  1023429.0   9924.0
```


## Reading (2026-10-04)
Not promising (6/12). Shorter vol-targeting windows give the same Sharpe as the 252-day book (0.36-0.41 vs 0.41 for
trend252) with more trading; placebo p 0.25. Volatility management does not improve this trend sleeve. Closed.
