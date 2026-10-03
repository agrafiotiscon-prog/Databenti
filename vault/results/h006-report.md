---
type: result
date: 2026-10-03
tags: [phase-5, H-006, gates]
---
# H-006 evaluation (D-023/D-026): gate verdict **not promising**

Fade the overnight gap after the RTH open. 3943 dates 2010-06-07..2025-09-30; 13 folds (3 y / 1 y). DSR N = 116. Costs: 1 tick adverse per side + fees (stress 2 ticks + fees x1.5).

## Gates
```
                                                          requirement result                                                   evidence
gate                                                                                                                                   
G1                                                  >= 200 OOS trades   PASS                                            oos_trades=2043
G2                                OOS net > 0 at 1.5x fees and 250 ms   FAIL                          oos_net_stress=-34920.89499999999
G3                      DSR >= 0.95 (raw N) and OOS mean-trade t >= 2   FAIL       dsr_raw=0.4812694398938914, oos_t=0.5933993309221447
G4                                                        PBO <= 0.10   FAIL                                     pbo=0.6374514374514374
G5                                                 +-20% plateau test   FAIL                                         plateau_pass=False
G6                                 not concentrated (red flags clear)   FAIL                                          concentrated=True
G7                       positive in >= 60% of OOS years (>= 2 years)   FAIL       years_positive_share=0.38461538461538464, n_years=13
G8                           tier-B fill check does not flip the sign   FAIL                                     tier_b_same_sign=False
G9                 MC 5th pct net > 0 and P(loss) <= 10% at 1.5x fees   FAIL             mc_net_p5=-1931.7216212059268, mc_p_loss=0.073
G10   cluster medoid; >= 70% of its cluster profitable; not an island   FAIL  is_medoid=True, cluster_share_profitable=0.0, island=True
G11                        DSR >= 0.95 with cluster-based effective K   FAIL                                   dsr_k=0.7169653784557114
```

## Out-of-sample
```
{
 "trades": 2043,
 "flag_few_trades": false,
 "net_pnl": 20761.07,
 "win_rate": 0.4738,
 "avg_trade": 10.1621,
 "median_trade": -29.51,
 "avg_ticks": 1.1738,
 "fees": 9213.93,
 "profit_factor": 1.0409,
 "t_stat": 0.5934
}
```
Net by scenario: {'base': 20761.1, 'fees1.5': 16154.1, 'stress': -34920.9, 'plus1tick': -30313.9}

### By year (OOS)
```
      oos_net  oos_trades
2013   -214.7          67
2014   -824.2         119
2015  -2358.5         146
2016   -142.9         137
2017  -1940.3          81
2018  -3800.5         147
2019    560.8         175
2020   5013.3         216
2021 -28943.0         198
2022  14734.9         214
2023  -2437.0         205
2024  22456.6         187
2025  18656.5         151
```

## Variant chosen per fold
```
 fold                   test                   variant  train_net_p5
    0 2013-06-04..2014-05-30 min_gap_bp25_exit_at10:00      -24047.7
    1 2014-06-03..2015-05-29 min_gap_bp25_exit_at10:00      -18516.6
    2 2015-06-02..2016-05-31 min_gap_bp25_exit_at10:00      -11904.3
    3 2016-06-02..2017-05-31 min_gap_bp25_exit_at10:00      -11756.8
    4 2017-06-02..2018-05-31 min_gap_bp25_exit_at10:00      -15188.4
    5 2018-06-04..2019-05-31 min_gap_bp25_exit_at10:00      -17555.5
    6 2019-06-04..2020-05-29 min_gap_bp10_exit_at10:00      -20916.3
    7 2020-06-02..2021-05-31 min_gap_bp10_exit_at10:00      -10776.1
    8 2021-06-02..2022-05-31 min_gap_bp10_exit_at10:00      -39085.6
    9 2022-06-02..2023-05-31 min_gap_bp10_exit_at10:00      -50291.1
   10 2023-06-02..2024-05-31 min_gap_bp10_exit_at10:00      -59308.4
   11 2024-06-04..2025-05-30 min_gap_bp10_exit_at11:00      -25069.3
   12 2025-06-03..2025-09-30 min_gap_bp10_exit_at11:00       26797.8
```

## Family: PBO = 0.637, K = 2

```
                               net  trades  avg_ticks
min_gap_bp10_exit_at10:00  -4163.2    3024      0.251
min_gap_bp25_exit_at10:00 -16524.0    2145     -0.255
min_gap_bp10_exit_at11:00  -2550.7    3024      0.293
min_gap_bp25_exit_at11:00 -23299.0    2145     -0.508
```


## Interpretation (added by hand, session 6)
See [leaderboard](leaderboard.md): no reliable edge after costs; closed.
