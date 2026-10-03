---
type: result
date: 2026-10-03
tags: [phase-5, H-013, gates]
---
# H-013 evaluation (D-023/D-026): gate verdict **not promising**

Intraday periodicity - trade each RTH hour in the direction of its recent average. 3943 dates 2010-06-07..2025-09-30; 13 folds (3 y / 1 y). DSR N = 144. Costs: 1 tick adverse per side + fees (stress 2 ticks + fees x1.5).

## Gates
```
                                                          requirement result                                                    evidence
gate                                                                                                                                    
G1                                                  >= 200 OOS trades   PASS                                              oos_trades=637
G2                                OOS net > 0 at 1.5x fees and 250 ms   FAIL                           oos_net_stress=-53796.80499999999
G3                      DSR >= 0.95 (raw N) and OOS mean-trade t >= 2   FAIL                      dsr_raw=0.0, oos_t=-2.1370971086532213
G4                                                        PBO <= 0.10   PASS                                                     pbo=0.0
G5                                                 +-20% plateau test   FAIL                                          plateau_pass=False
G6                                 not concentrated (red flags clear)   FAIL                                           concentrated=True
G7                       positive in >= 60% of OOS years (>= 2 years)   FAIL        years_positive_share=0.15384615384615385, n_years=13
G8                           tier-B fill check does not flip the sign   FAIL                                      tier_b_same_sign=False
G9                 MC 5th pct net > 0 and P(loss) <= 10% at 1.5x fees   FAIL                 mc_net_p5=-41809.30709598186, mc_p_loss=1.0
G10   cluster medoid; >= 70% of its cluster profitable; not an island   FAIL  is_medoid=False, cluster_share_profitable=0.0, island=True
G11                        DSR >= 0.95 with cluster-based effective K   FAIL                                 dsr_k=0.0002104405452632574
```

## Out-of-sample
```
{
 "trades": 637,
 "flag_few_trades": false,
 "net_pnl": -36435.37,
 "win_rate": 0.4553,
 "avg_trade": -57.1984,
 "median_trade": -42.01,
 "avg_ticks": -4.2151,
 "fees": 2872.87,
 "profit_factor": 0.7726,
 "t_stat": -2.1371
}
```
Net by scenario: {'base': -36435.4, 'fees1.5': -37871.8, 'stress': -53796.8, 'plus1tick': -52360.4}

### By year (OOS)
```
      oos_net  oos_trades
2013  -1016.9        37.0
2014  -1572.2        16.0
2015  -1463.8        28.0
2016  -1993.1        65.0
2017      0.0         NaN
2018  -3008.1        60.0
2019  -2953.7        23.0
2020  -8448.3        80.0
2021  -2532.5        46.0
2022 -12347.6       163.0
2023   2720.0        51.0
2024    772.3        20.0
2025  -4591.5        48.0
```

## Variant chosen per fold
```
 fold                   test                variant  train_net_p5
    0 2013-06-04..2014-05-30 lookback40_min_abs_bp5       -9450.2
    1 2014-06-03..2015-05-29 lookback40_min_abs_bp5       -9829.0
    2 2015-06-02..2016-05-31 lookback40_min_abs_bp5       -5414.9
    3 2016-06-02..2017-05-31 lookback40_min_abs_bp5       -9393.3
    4 2017-06-02..2018-05-31 lookback40_min_abs_bp5       -8081.5
    5 2018-06-04..2019-05-31 lookback40_min_abs_bp5       -8037.1
    6 2019-06-04..2020-05-29 lookback40_min_abs_bp5       -9471.1
    7 2020-06-02..2021-05-31 lookback40_min_abs_bp5      -18797.0
    8 2021-06-02..2022-05-31 lookback40_min_abs_bp5      -24953.6
    9 2022-06-02..2023-05-31 lookback40_min_abs_bp5      -32956.8
   10 2023-06-02..2024-05-31 lookback40_min_abs_bp5      -39412.1
   11 2024-06-04..2025-05-30 lookback40_min_abs_bp5      -29363.2
   12 2025-06-03..2025-09-30 lookback40_min_abs_bp5      -24595.2
```

## Family: PBO = 0.000, K = 2

```
                             net  trades  avg_ticks
lookback10_min_abs_bp0 -539616.4   16492     -2.257
lookback10_min_abs_bp5 -284369.6    7363     -2.729
lookback40_min_abs_bp0 -165502.1    4909     -2.336
lookback40_min_abs_bp5  -38778.5     799     -3.522
```


## Interpretation (added by hand, session 6)
See [leaderboard](leaderboard.md).
