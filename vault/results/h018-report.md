---
type: result
date: 2026-10-03
tags: [phase-5, H-018, gates]
---
# H-018 evaluation (D-023/D-026): gate verdict **not promising**

Monday reversal - fade Friday's RTH move during Monday's RTH session. 3943 dates 2010-06-07..2025-09-30; 13 folds (3 y / 1 y). DSR N = 160. Costs: 1 tick adverse per side + fees (stress 2 ticks + fees x1.5).

## Gates
```
                                                          requirement result                                                     evidence
gate                                                                                                                                     
G1                                                  >= 200 OOS trades   PASS                                               oos_trades=329
G2                                OOS net > 0 at 1.5x fees and 250 ms   PASS                                     oos_net_stress=27899.315
G3                      DSR >= 0.95 (raw N) and OOS mean-trade t >= 2   FAIL         dsr_raw=0.8715617820246667, oos_t=1.6384296905737605
G4                                                        PBO <= 0.10   FAIL                                       pbo=0.6447552447552447
G5                                                 +-20% plateau test   PASS                                            plateau_pass=True
G6                                 not concentrated (red flags clear)   FAIL                                            concentrated=True
G7                       positive in >= 60% of OOS years (>= 2 years)   FAIL          years_positive_share=0.5384615384615384, n_years=13
G8                           tier-B fill check does not flip the sign   PASS                                        tier_b_same_sign=True
G9                 MC 5th pct net > 0 and P(loss) <= 10% at 1.5x fees   PASS                mc_net_p5=18970.507266517125, mc_p_loss=0.001
G10   cluster medoid; >= 70% of its cluster profitable; not an island   FAIL  is_medoid=False, cluster_share_profitable=1.0, island=False
G11                        DSR >= 0.95 with cluster-based effective K   FAIL                                     dsr_k=0.9499598067135845
G12   beats a placebo / random-timing benchmark (one-sided p <= 0.05)   FAIL                                             placebo_p=0.2419
```

## Out-of-sample
```
{
 "trades": 329,
 "flag_few_trades": false,
 "net_pnl": 36866.21,
 "win_rate": 0.5137,
 "avg_trade": 112.0553,
 "median_trade": 20.49,
 "avg_ticks": 9.3252,
 "fees": 1483.79,
 "profit_factor": 1.3451,
 "t_stat": 1.6384
}
```
Net by scenario: {'base': 36866.2, 'fees1.5': 36124.3, 'stress': 27899.3, 'plus1tick': 28641.2}

### By year (OOS)
```
      oos_net  oos_trades
2013  -1012.7          25
2014  -2829.4          37
2015   1411.6          39
2016   -738.4          39
2017   -109.7          16
2018  -5502.7          20
2019  -1163.1          14
2020   4868.8          18
2021   3003.9          13
2022  15806.7          29
2023   1714.3          19
2024    385.2          31
2025  21031.7          29
```

## Variant chosen per fold
```
 fold                   test      variant  train_net_p5
    0 2013-06-04..2014-05-30  min_abs_bp0       -2925.1
    1 2014-06-03..2015-05-29  min_abs_bp0       -2332.1
    2 2015-06-02..2016-05-31  min_abs_bp0       -4225.0
    3 2016-06-02..2017-05-31  min_abs_bp0      -12775.1
    4 2017-06-02..2018-05-31 min_abs_bp50      -11318.1
    5 2018-06-04..2019-05-31 min_abs_bp50      -18874.0
    6 2019-06-04..2020-05-29 min_abs_bp50      -16394.5
    7 2020-06-02..2021-05-31 min_abs_bp50      -21713.9
    8 2021-06-02..2022-05-31 min_abs_bp50      -12128.5
    9 2022-06-02..2023-05-31 min_abs_bp50       -2571.9
   10 2023-06-02..2024-05-31 min_abs_bp50        2684.0
   11 2024-06-04..2025-05-30  min_abs_bp0       -3815.7
   12 2025-06-03..2025-09-30  min_abs_bp0        8913.6
```

## Family: PBO = 0.645, K = 1

```
                  net  trades  avg_ticks
min_abs_bp0   29622.9     613      4.227
min_abs_bp50  30011.7     233     10.665
```

