---
type: result
date: 2026-10-03
tags: [phase-5, H-019, gates]
---
# H-019 evaluation (D-023/D-026): gate verdict **insufficient data**

Month-end rebalancing - fade the month-to-date ES move over the last 4 trading days of the month. 3943 dates 2010-06-07..2025-09-30; 13 folds (3 y / 1 y). DSR N = 164. Costs: 1 tick adverse per side + fees (stress 2 ticks + fees x1.5).

## Gates
```
                                                          requirement result                                                     evidence
gate                                                                                                                                     
G1                                                  >= 200 OOS trades   FAIL                                                oos_trades=86
G2                                OOS net > 0 at 1.5x fees and 250 ms   FAIL                           oos_net_stress=-12644.289999999997
G3                      DSR >= 0.95 (raw N) and OOS mean-trade t >= 2   FAIL        dsr_raw=0.176504264875876, oos_t=-0.33932976961219086
G4                                                        PBO <= 0.10   FAIL                                       pbo=0.6032634032634032
G5                                                 +-20% plateau test   PASS                                            plateau_pass=True
G6                                 not concentrated (red flags clear)   FAIL                                            concentrated=True
G7                       positive in >= 60% of OOS years (>= 2 years)   FAIL         years_positive_share=0.46153846153846156, n_years=13
G8                           tier-B fill check does not flip the sign   FAIL                                       tier_b_same_sign=False
G9                 MC 5th pct net > 0 and P(loss) <= 10% at 1.5x fees   FAIL                mc_net_p5=-24332.577374413962, mc_p_loss=0.82
G10   cluster medoid; >= 70% of its cluster profitable; not an island   FAIL  is_medoid=False, cluster_share_profitable=1.0, island=False
G11                        DSR >= 0.95 with cluster-based effective K   FAIL                                     dsr_k=0.3663867766384672
G12   beats a placebo / random-timing benchmark (one-sided p <= 0.05)   FAIL                                             placebo_p=0.4106
```

## Out-of-sample
```
{
 "trades": 86,
 "flag_few_trades": true,
 "net_pnl": -10300.36,
 "win_rate": 0.5,
 "avg_trade": -119.7716,
 "median_trade": 26.74,
 "avg_ticks": -9.2209,
 "fees": 387.86,
 "profit_factor": 0.9017,
 "t_stat": -0.3393
}
```
Net by scenario: {'base': -10300.4, 'fees1.5': -10494.3, 'stress': -12644.3, 'plus1tick': -12450.4}

### By year (OOS)
```
      oos_net  oos_trades
2013   1865.0           5
2014   -976.0           3
2015   7427.4           5
2016   5785.4           6
2017   1136.5           3
2018  11051.4           8
2019  -5253.1           9
2020   -552.1           6
2021   6288.9           8
2022 -10812.1          11
2023 -10028.1           9
2024  -1444.1           7
2025 -14789.6           6
```

## Variant chosen per fold
```
 fold                   test       variant  train_net_p5
    0 2013-06-04..2014-05-30 min_abs_bp200        1669.3
    1 2014-06-03..2015-05-29 min_abs_bp200        1753.7
    2 2015-06-02..2016-05-31 min_abs_bp200         371.8
    3 2016-06-02..2017-05-31 min_abs_bp200         575.4
    4 2017-06-02..2018-05-31 min_abs_bp200        2507.1
    5 2018-06-04..2019-05-31 min_abs_bp200        5548.0
    6 2019-06-04..2020-05-29 min_abs_bp200       -1503.4
    7 2020-06-02..2021-05-31 min_abs_bp200      -10387.3
    8 2021-06-02..2022-05-31 min_abs_bp200      -14607.8
    9 2022-06-02..2023-05-31 min_abs_bp200      -14670.6
   10 2023-06-02..2024-05-31 min_abs_bp200      -48868.7
   11 2024-06-04..2025-05-30 min_abs_bp200      -54950.3
   12 2025-06-03..2025-09-30 min_abs_bp200      -75139.5
```

## Family: PBO = 0.603, K = 1

```
                   net  trades  avg_ticks
min_abs_bp0    14224.7     183      6.579
min_abs_bp200     83.4     109      0.422
```

