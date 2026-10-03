---
type: result
date: 2026-10-03
tags: [phase-5, H-002, gates]
---
# H-002 evaluation (D-020 protocol): gate verdict **insufficient data**

Intraday momentum into the cash close, with an optional order-flow confirmation filter. Data: 238 RTH days 2024-11-01..2025-09-30 (quotes rebuilt from trades). 16 variants; 5 walk-forward folds (6 m / 1 m, 1-day embargo). DSR uses N = 88 (all hypothesis trials so far).

## Gates
```
                                                          requirement result                                                   evidence
gate                                                                                                                                   
G1                                                  >= 200 OOS trades   FAIL                                              oos_trades=53
G2                                OOS net > 0 at 1.5x fees and 250 ms   PASS                          oos_net_stress=128.95500000000118
G3                      DSR >= 0.95 (raw N) and OOS mean-trade t >= 2   FAIL    dsr_raw=0.031688255328514825, oos_t=0.07775314730669491
G4                                                        PBO <= 0.10   FAIL                                                    pbo=0.2
G5                                                 +-20% plateau test   FAIL                                         plateau_pass=False
G6                                 not concentrated (red flags clear)   FAIL                                          concentrated=True
G7                       positive in >= 60% of OOS years (>= 2 years)   FAIL                        years_positive_share=1.0, n_years=1
G8                           tier-B fill check does not flip the sign   FAIL                             not measured: tier_b_same_sign
G9                 MC 5th pct net > 0 and P(loss) <= 10% at 1.5x fees   FAIL             mc_net_p5=-2116.9668781501605, mc_p_loss=0.426
G10   cluster medoid; >= 70% of its cluster profitable; not an island   FAIL  is_medoid=True, cluster_share_profitable=0.0, island=True
G11                        DSR >= 0.95 with cluster-based effective K   FAIL                                   dsr_k=0.1034695239427349
```

## Out-of-sample (concatenated test months)
```
{
 "trades": 53,
 "flag_few_trades": true,
 "net_pnl": 348.47,
 "win_rate": 0.434,
 "avg_trade": 6.5749,
 "median_trade": -154.51,
 "avg_ticks": 0.8868,
 "fees": 239.03,
 "profit_factor": 1.0329,
 "t_stat": 0.0778
}
```
Net PnL by cost scenario: {'base': 348.47, 'fees1.5': 228.96, 'fees1.5_lat250': 128.96, 'fees2_lat500': 59.44}

### Per month
```
              size      sum
trading_date               
2025-05         10 -2095.10
2025-06         10 -1232.60
2025-07         13   516.37
2025-08         10   517.40
2025-09         10  2642.40
```

## Variant chosen per fold
```
 fold  test_from    test_to                                                 variant  train_net_p5
    0 2025-05-02 2025-05-30  signalopen30_min_abs_bp10_stop_ticks0_delta_filterTrue       -984.32
    1 2025-06-03 2025-06-30    signalday_min_abs_bp10_stop_ticks12_delta_filterTrue      -5095.07
    2 2025-07-02 2025-07-31   signalopen30_min_abs_bp0_stop_ticks0_delta_filterTrue      -4139.45
    3 2025-08-04 2025-08-29   signalopen30_min_abs_bp0_stop_ticks0_delta_filterTrue      -2757.25
    4 2025-09-02 2025-09-30 signalopen30_min_abs_bp10_stop_ticks12_delta_filterTrue      -5298.28
```

## Family: PBO = 0.2, clusters K = 6, variants net > 0: 5/16

Full-period results of all variants (in-sample for selection; not evidence of an edge):

```
                                                               net  trades  avg_ticks
signalopen30_min_abs_bp10_stop_ticks0_delta_filterTrue     6276.06      94       5.70
signalopen30_min_abs_bp0_stop_ticks0_delta_filterTrue      4119.88     112       3.30
signalday_min_abs_bp0_stop_ticks0_delta_filterTrue         3293.85     115       2.65
signalopen30_min_abs_bp10_stop_ticks0_delta_filterFalse     835.75     175       0.74
signalday_min_abs_bp10_stop_ticks0_delta_filterTrue         300.03      97       0.61
signalopen30_min_abs_bp10_stop_ticks12_delta_filterTrue     -86.44      94       0.29
signalopen30_min_abs_bp0_stop_ticks0_delta_filterFalse    -1665.14     214      -0.26
signalopen30_min_abs_bp0_stop_ticks12_delta_filterTrue    -1730.12     112      -0.88
signalday_min_abs_bp0_stop_ticks12_delta_filterTrue       -2706.15     115      -1.52
signalday_min_abs_bp0_stop_ticks0_delta_filterFalse       -3077.64     214      -0.79
signalopen30_min_abs_bp10_stop_ticks12_delta_filterFalse  -3701.75     175      -1.33
signalopen30_min_abs_bp0_stop_ticks12_delta_filterFalse   -5240.14     214      -1.60
signalday_min_abs_bp10_stop_ticks12_delta_filterTrue      -5462.47      97      -4.14
signalday_min_abs_bp0_stop_ticks12_delta_filterFalse      -6002.64     214      -1.88
signalday_min_abs_bp10_stop_ticks0_delta_filterFalse      -9218.37     187      -3.58
signalday_min_abs_bp10_stop_ticks12_delta_filterFalse    -11643.37     187      -4.62
```


## Interpretation (added by hand, session 6; generated sections above unchanged)
- **Inconclusive, no detectable edge.** OOS 53 trades, +$348 (+0.89 ticks/trade net), t = 0.08:
  indistinguishable from zero. 5/16 variants positive over the full year; PBO 0.20; DSR 0.03
  (N = 88 hypothesis trials so far); MC P(loss) 0.43.
- **Underpowered by design:** per-trade standard deviation ≈ $600, so detecting a realistic
  +$20/trade edge at t = 2 needs ≈ 3,700 trades ≈ 15 years of once-a-day trades. One year of
  order-flow data cannot decide this hypothesis either way.
- The base signal needs only three prices per day, so it can be tested on many years of cheap
  1-minute bars (without the delta filter). That becomes a NEW pre-registered hypothesis (the
  H-002 trial budget is spent), with years kept strictly before the holdout.
