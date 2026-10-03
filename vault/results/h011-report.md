---
type: result
date: 2026-10-03
tags: [phase-5, H-011, gates]
---
# H-011 evaluation (D-020 protocol): gate verdict **insufficient data**

Fade large deviations from the session VWAP, target VWAP. Data: 238 RTH days 2024-11-01..2025-09-30 (quotes rebuilt from trades). 4 variants; 5 walk-forward folds (6 m / 1 m, 1-day embargo). DSR uses N = 138 (all hypothesis trials so far).

## Gates
```
                                                          requirement result                                                    evidence
gate                                                                                                                                    
G1                                                  >= 200 OOS trades   PASS                                              oos_trades=256
G2                                OOS net > 0 at 1.5x fees and 250 ms   PASS                            oos_net_stress=4954.630000000006
G3                      DSR >= 0.95 (raw N) and OOS mean-trade t >= 2   FAIL        dsr_raw=0.1274656671199389, oos_t=0.6783867375015267
G4                                                        PBO <= 0.10   FAIL                                     pbo=0.11428571428571428
G5                                                 +-20% plateau test   FAIL                                          plateau_pass=False
G6                                 not concentrated (red flags clear)   FAIL                                           concentrated=True
G7                       positive in >= 60% of OOS years (>= 2 years)   FAIL                         years_positive_share=1.0, n_years=1
G8                           tier-B fill check does not flip the sign   FAIL                              not measured: tier_b_same_sign
G9                 MC 5th pct net > 0 and P(loss) <= 10% at 1.5x fees   PASS                 mc_net_p5=21.45821666344295, mc_p_loss=0.05
G10   cluster medoid; >= 70% of its cluster profitable; not an island   FAIL  is_medoid=False, cluster_share_profitable=0.0, island=True
G11                        DSR >= 0.95 with cluster-based effective K   FAIL                                    dsr_k=0.6441318291165217
```

## Out-of-sample (concatenated test months)
```
{
 "trades": 256,
 "flag_few_trades": false,
 "net_pnl": 4070.44,
 "win_rate": 0.3477,
 "avg_trade": 15.9002,
 "median_trade": -204.51,
 "avg_ticks": 1.6328,
 "fees": 1154.56,
 "profit_factor": 1.1356,
 "t_stat": 0.6784
}
```
Net PnL by cost scenario: {'base': 4070.44, 'fees1.5': 3493.16, 'fees1.5_lat250': 4954.63, 'fees2_lat500': 3863.82}

### Per month
```
              size      sum
trading_date               
2025-05         60  3204.40
2025-06         32  -794.32
2025-07         71   292.29
2025-08         42  2073.08
2025-09         51  -705.01
```

## Variant chosen per fold
```
 fold  test_from    test_to           variant  train_net_p5
    0 2025-05-02 2025-05-30 k3.0_stop_ticks16     -33788.83
    1 2025-06-03 2025-06-30 k3.0_stop_ticks16     -28785.68
    2 2025-07-02 2025-07-31 k3.0_stop_ticks16     -25032.43
    3 2025-08-04 2025-08-29 k3.0_stop_ticks16     -26831.83
    4 2025-09-02 2025-09-30 k3.0_stop_ticks16     -23721.08
```

## Family: PBO = 0.11428571428571428, clusters K = 2, variants net > 0: 0/4

Full-period results of all variants (in-sample for selection; not evidence of an edge):

```
                        net  trades  avg_ticks
k3.0_stop_ticks16 -14494.86     786      -1.11
k3.0_stop_ticks8  -21380.40    1290      -0.97
k2.0_stop_ticks16 -56244.18    2568      -1.39
k2.0_stop_ticks8  -82648.01    4351      -1.16
```


## Interpretation (added by hand, session 6)
Not promoted; see [leaderboard](leaderboard.md).
