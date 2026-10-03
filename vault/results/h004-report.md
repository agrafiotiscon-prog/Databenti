---
type: result
date: 2026-10-03
tags: [phase-5, H-004, gates]
---
# H-004 evaluation (D-020 protocol): gate verdict **insufficient data**

Follow large multi-level aggressive sweeps (order-splitting continuation). Data: 238 RTH days 2024-11-01..2025-09-30 (quotes rebuilt from trades). 16 variants; 5 walk-forward folds (6 m / 1 m, 1-day embargo). DSR uses N = 108 (all hypothesis trials so far).

## Gates
```
                                                          requirement result                                                    evidence
gate                                                                                                                                    
G1                                                  >= 200 OOS trades   PASS                                              oos_trades=202
G2                                OOS net > 0 at 1.5x fees and 250 ms   FAIL                           oos_net_stress=-6716.529999999999
G3                      DSR >= 0.95 (raw N) and OOS mean-trade t >= 2   FAIL                       dsr_raw=0.0, oos_t=-5.474372644479226
G4                                                        PBO <= 0.10   PASS                                                     pbo=0.0
G5                                                 +-20% plateau test   FAIL                                          plateau_pass=False
G6                                 not concentrated (red flags clear)   FAIL                                           concentrated=True
G7                       positive in >= 60% of OOS years (>= 2 years)   FAIL                         years_positive_share=0.0, n_years=1
G8                           tier-B fill check does not flip the sign   FAIL                              not measured: tier_b_same_sign
G9                 MC 5th pct net > 0 and P(loss) <= 10% at 1.5x fees   FAIL                mc_net_p5=-6335.2809296166215, mc_p_loss=1.0
G10   cluster medoid; >= 70% of its cluster profitable; not an island   FAIL  is_medoid=False, cluster_share_profitable=0.0, island=True
G11                        DSR >= 0.95 with cluster-based effective K   FAIL                                 dsr_k=7.771561172376096e-16
```

## Out-of-sample (concatenated test months)
```
{
 "trades": 202,
 "flag_few_trades": false,
 "net_pnl": -6123.52,
 "win_rate": 0.2822,
 "avg_trade": -30.3145,
 "median_trade": -79.51,
 "avg_ticks": -2.0644,
 "fees": 911.02,
 "profit_factor": 0.4689,
 "t_stat": -5.4744
}
```
Net PnL by cost scenario: {'base': -6123.52, 'fees1.5': -6579.03, 'fees1.5_lat250': -6716.53, 'fees2_lat500': -5822.04}

### Per month
```
              size      sum
trading_date               
2025-05         36 -1112.36
2025-06         29 -1255.79
2025-07         47 -1149.47
2025-08         33  -523.83
2025-09         57 -2082.07
```

## Variant chosen per fold
```
 fold  test_from    test_to                                           variant  train_net_p5
    0 2025-05-02 2025-05-30 min_size200_min_levels3_stop_ticks6_target_ticks8     -16418.69
    1 2025-06-03 2025-06-30 min_size200_min_levels3_stop_ticks6_target_ticks8     -16065.67
    2 2025-07-02 2025-07-31 min_size200_min_levels3_stop_ticks6_target_ticks8     -15070.19
    3 2025-08-04 2025-08-29 min_size200_min_levels3_stop_ticks6_target_ticks8     -14193.66
    4 2025-09-02 2025-09-30 min_size200_min_levels3_stop_ticks6_target_ticks8     -12921.59
```

## Family: PBO = 0.0, clusters K = 2, variants net > 0: 0/16

Full-period results of all variants (in-sample for selection; not evidence of an edge):

```
                                                           net  trades  avg_ticks
min_size200_min_levels3_stop_ticks12_target_ticks16  -15374.54     654      -1.52
min_size200_min_levels3_stop_ticks12_target_ticks8   -17145.28     678      -1.66
min_size200_min_levels3_stop_ticks6_target_ticks8    -18045.92     692      -1.73
min_size200_min_levels3_stop_ticks6_target_ticks16   -18147.73     673      -1.80
min_size200_min_levels2_stop_ticks12_target_ticks16  -30893.82    1232      -1.65
min_size200_min_levels2_stop_ticks6_target_ticks16   -32919.96    1296      -1.67
min_size200_min_levels2_stop_ticks12_target_ticks8   -32999.47    1297      -1.67
min_size200_min_levels2_stop_ticks6_target_ticks8    -34235.02    1352      -1.66
min_size100_min_levels3_stop_ticks12_target_ticks16 -204486.66   10216      -1.24
min_size100_min_levels3_stop_ticks6_target_ticks16  -244315.95   12595      -1.19
min_size100_min_levels2_stop_ticks12_target_ticks16 -252917.09   12659      -1.24
min_size100_min_levels3_stop_ticks12_target_ticks8  -253968.41   12141      -1.31
min_size100_min_levels3_stop_ticks6_target_ticks8   -273706.87   14037      -1.20
min_size100_min_levels2_stop_ticks6_target_ticks16  -302792.76   16326      -1.12
min_size100_min_levels2_stop_ticks12_target_ticks8  -326523.12   15662      -1.31
min_size100_min_levels2_stop_ticks6_target_ticks8   -368771.32   18982      -1.19
```


## Interpretation (added by hand, session 6; generated sections above unchanged)
- **Not promising, clearly negative.** OOS 202 trades, −$6,124, −2.06 ticks/trade after costs,
  **t = −5.5**; 0 of 16 variants positive over the year; MC P(loss) = 1.0.
- With ≈ 1.36 ticks of round-trip cost, the signal is ≈ −0.7 ticks **gross**: by the time a
  100 ms order arrives after a sweep, price has started to revert (the sweep's impact is partly
  temporary). Order-splitting continuation, if present, is not capturable at retail latency.
- **Observation, not evidence:** the mirror trade (fade sweeps) would gross ≈ +0.7 ticks, still
  below market-order costs (≈ −0.7 net). Any passive-entry fade variant was suggested by THIS
  result, so it must not be tested on the same 238 days (contaminated).
