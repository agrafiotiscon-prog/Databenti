---
type: result
date: 2026-10-03
tags: [phase-5, H-012, gates]
---
# H-012 evaluation (D-023/D-026): gate verdict **not promising**

FOMC-cycle even weeks - long only in even weeks of the FOMC cycle. 3943 dates 2010-06-07..2025-09-30; 13 folds (3 y / 1 y). DSR N = 140. Costs: 1 tick adverse per side + fees (stress 2 ticks + fees x1.5).

## Gates
```
                                                          requirement result                                                     evidence
gate                                                                                                                                     
G1                                                  >= 200 OOS trades   PASS                                               oos_trades=226
G2                                OOS net > 0 at 1.5x fees and 250 ms   PASS                             oos_net_stress=75846.11000000002
G3                      DSR >= 0.95 (raw N) and OOS mean-trade t >= 2   FAIL          dsr_raw=0.8799225723434574, oos_t=1.234385697665412
G4                                                        PBO <= 0.10   FAIL                                       pbo=0.9665889665889665
G5                                                 +-20% plateau test   PASS                                            plateau_pass=True
G6                                 not concentrated (red flags clear)   FAIL                                            concentrated=True
G7                       positive in >= 60% of OOS years (>= 2 years)   PASS          years_positive_share=0.6923076923076923, n_years=13
G8                           tier-B fill check does not flip the sign   PASS                                        tier_b_same_sign=True
G9                 MC 5th pct net > 0 and P(loss) <= 10% at 1.5x fees   PASS                  mc_net_p5=33831.6803386883, mc_p_loss=0.002
G10   cluster medoid; >= 70% of its cluster profitable; not an island   FAIL  is_medoid=False, cluster_share_profitable=1.0, island=False
G11                        DSR >= 0.95 with cluster-based effective K   FAIL                                      dsr_k=0.880385689033099
```

## Out-of-sample
```
{
 "trades": 226,
 "flag_few_trades": false,
 "net_pnl": 82005.74,
 "win_rate": 0.6018,
 "avg_trade": 362.8573,
 "median_trade": 414.24,
 "avg_ticks": 29.3894,
 "fees": 1019.26,
 "profit_factor": 1.3062,
 "t_stat": 1.2344
}
```
Net by scenario: {'base': 82005.7, 'fees1.5': 81496.1, 'stress': 75846.1, 'plus1tick': 76355.7}

### By year (OOS)
```
      oos_net  oos_trades
2013   -113.1          14
2014   6513.3          22
2015  13913.3          22
2016   4042.8          21
2017   7005.3          21
2018 -17201.7          17
2019   8765.3          16
2020   1395.9          12
2021   3599.4          14
2022  -6100.6          14
2023  27510.8          17
2024  33213.3          22
2025   -538.1          14
```

## Variant chosen per fold
```
 fold                   test    variant  train_net_p5
    0 2013-06-04..2014-05-30  weekseven       -1680.5
    1 2014-06-03..2015-05-29  weekseven       -8428.4
    2 2015-06-02..2016-05-31  weekseven        1323.7
    3 2016-06-02..2017-05-31  weekseven       -4963.6
    4 2017-06-02..2018-05-31  weekseven        2945.0
    5 2018-06-04..2019-05-31 weeksw0_w2      -20538.5
    6 2019-06-04..2020-05-29 weeksw0_w2      -19323.9
    7 2020-06-02..2021-05-31 weeksw0_w2      -31521.2
    8 2021-06-02..2022-05-31 weeksw0_w2      -30872.7
    9 2022-06-02..2023-05-31 weeksw0_w2      -34406.8
   10 2023-06-02..2024-05-31  weekseven      -46330.4
   11 2024-06-04..2025-05-30  weekseven      -15899.4
   12 2025-06-03..2025-09-30 weeksw0_w2      -48146.5
```

## Family: PBO = 0.967, K = 1

```
                net  trades  avg_ticks
weekseven   92911.3     319     23.661
weeksw0_w2  75121.3     217     28.055
```


## Interpretation (added by hand, session 6)
See [leaderboard](leaderboard.md).
