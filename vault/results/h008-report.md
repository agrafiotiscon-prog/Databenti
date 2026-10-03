---
type: result
date: 2026-10-03
tags: [phase-5, H-008, gates]
---
# H-008 evaluation (D-020 protocol): gate verdict **insufficient data**

Fade extreme 5-minute order-flow imbalance (price-pressure reversal). Data: 238 RTH days 2024-11-01..2025-09-30 (quotes rebuilt from trades). 8 variants; 5 walk-forward folds (6 m / 1 m, 1-day embargo). DSR uses N = 126 (all hypothesis trials so far).

## Gates
```
                                                          requirement result                                                   evidence
gate                                                                                                                                   
G1                                                  >= 200 OOS trades   FAIL                                             oos_trades=124
G2                                OOS net > 0 at 1.5x fees and 250 ms   PASS                           oos_net_stress=598.6399999999999
G3                      DSR >= 0.95 (raw N) and OOS mean-trade t >= 2   FAIL     dsr_raw=0.18366142912718442, oos_t=0.18330621524126145
G4                                                        PBO <= 0.10   FAIL                                    pbo=0.38571428571428573
G5                                                 +-20% plateau test   FAIL                                         plateau_pass=False
G6                                 not concentrated (red flags clear)   FAIL                                          concentrated=True
G7                       positive in >= 60% of OOS years (>= 2 years)   FAIL                        years_positive_share=1.0, n_years=1
G8                           tier-B fill check does not flip the sign   FAIL                             not measured: tier_b_same_sign
G9                 MC 5th pct net > 0 and P(loss) <= 10% at 1.5x fees   FAIL              mc_net_p5=-1636.959253787519, mc_p_loss=0.299
G10   cluster medoid; >= 70% of its cluster profitable; not an island   FAIL  is_medoid=True, cluster_share_profitable=0.0, island=True
G11                        DSR >= 0.95 with cluster-based effective K   FAIL                                  dsr_k=0.47882927911620077
```

## Out-of-sample (concatenated test months)
```
{
 "trades": 124,
 "flag_few_trades": true,
 "net_pnl": 653.26,
 "win_rate": 0.1774,
 "avg_trade": 5.2682,
 "median_trade": -104.51,
 "avg_ticks": 0.7823,
 "fees": 559.24,
 "profit_factor": 1.0613,
 "t_stat": 0.1833
}
```
Net PnL by cost scenario: {'base': 653.26, 'fees1.5': 373.64, 'fees1.5_lat250': 598.64, 'fees2_lat500': -4177.5}

### Per month
```
              size      sum
trading_date               
2025-05         28  2536.22
2025-06         25   274.75
2025-07         30 -1110.30
2025-08         21 -1494.71
2025-09         20   447.30
```

## Variant chosen per fold
```
 fold  test_from    test_to                     variant  train_net_p5
    0 2025-05-02 2025-05-30 z3.0_hold_min30_stop_ticks8     -10176.82
    1 2025-06-03 2025-06-30 z3.0_hold_min30_stop_ticks8      -7118.85
    2 2025-07-02 2025-07-31 z3.0_hold_min30_stop_ticks8      -7719.83
    3 2025-08-04 2025-08-29 z3.0_hold_min30_stop_ticks8      -9279.40
    4 2025-09-02 2025-09-30 z3.0_hold_min30_stop_ticks8     -11116.96
```

## Family: PBO = 0.38571428571428573, clusters K = 3, variants net > 0: 0/8

Full-period results of all variants (in-sample for selection; not evidence of an edge):

```
                                   net  trades  avg_ticks
z2.0_hold_min30_stop_ticks8   -2189.13     563       0.05
z2.0_hold_min30_stop_ticks16  -4090.69     519      -0.27
z2.0_hold_min15_stop_ticks8   -4414.77     577      -0.25
z3.0_hold_min30_stop_ticks8   -4837.16     266      -1.09
z3.0_hold_min15_stop_ticks8   -5746.18     268      -1.35
z3.0_hold_min30_stop_ticks16  -8920.54     254      -2.45
z3.0_hold_min15_stop_ticks16 -10613.58     258      -2.93
z2.0_hold_min15_stop_ticks16 -10806.92     542      -1.23
```


## Interpretation (added by hand, session 6)
See [leaderboard](leaderboard.md): no reliable edge after costs; closed.
