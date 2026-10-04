---
type: result
date: 2026-10-04
tags: [phase-5, H-028, gates]
---
# H-028 evaluation (D-020 protocol): gate verdict **insufficient data**

Trade-flow imbalance continuation - follow strong 5/15-min aggressor imbalance in ES RTH for 15/30 min. Data: 238 RTH days 2024-11-01..2025-09-30 (quotes rebuilt from trades). 8 variants; 5 walk-forward folds (6 m / 1 m, 1-day embargo). DSR uses N = 196 (all hypothesis trials so far).

## Gates
```
                                                          requirement result                                                    evidence
gate                                                                                                                                    
G1                                                  >= 200 OOS trades   FAIL                                              oos_trades=171
G2                                OOS net > 0 at 1.5x fees and 250 ms   PASS                           oos_net_stress=1855.6850000000013
G3                      DSR >= 0.95 (raw N) and OOS mean-trade t >= 2   FAIL       dsr_raw=0.13916347582249866, oos_t=0.6483494795780368
G4                                                        PBO <= 0.10   FAIL                                     pbo=0.34285714285714286
G5                                                 +-20% plateau test   FAIL                                          plateau_pass=False
G6                                 not concentrated (red flags clear)   FAIL                                           concentrated=True
G7                       positive in >= 60% of OOS years (>= 2 years)   FAIL                         years_positive_share=1.0, n_years=1
G8                           tier-B fill check does not flip the sign   FAIL                              not measured: tier_b_same_sign
G9                 MC 5th pct net > 0 and P(loss) <= 10% at 1.5x fees   FAIL              mc_net_p5=-198.48940274755526, mc_p_loss=0.066
G10   cluster medoid; >= 70% of its cluster profitable; not an island   FAIL  is_medoid=False, cluster_share_profitable=0.0, island=True
G11                        DSR >= 0.95 with cluster-based effective K   FAIL                                    dsr_k=0.6845372763648431
G12   beats a placebo / random-timing benchmark (one-sided p <= 0.05)   FAIL                                     not measured: placebo_p
```

## Out-of-sample (concatenated test months)
```
{
 "trades": 171,
 "flag_few_trades": true,
 "net_pnl": 2566.29,
 "win_rate": 0.5088,
 "avg_trade": 15.0075,
 "median_trade": 20.49,
 "avg_ticks": 1.5614,
 "fees": 771.21,
 "profit_factor": 1.14,
 "t_stat": 0.6483
}
```
Net PnL by cost scenario: {'base': 2566.29, 'fees1.5': 2180.69, 'fees1.5_lat250': 1855.69, 'fees2_lat500': 1507.58}

### Per month
```
              size      sum
trading_date               
2025-05         24   266.76
2025-06         43    93.57
2025-07         38 -1158.88
2025-08         34   271.66
2025-09         32  3093.18
```

## Variant chosen per fold
```
 fold  test_from    test_to                  variant  train_net_p5
    0 2025-05-02 2025-05-30 window15_levelq90_hold15     -16816.88
    1 2025-06-03 2025-06-30 window15_levelq90_hold15     -16430.85
    2 2025-07-02 2025-07-31 window15_levelq90_hold15     -12119.72
    3 2025-08-04 2025-08-29 window15_levelq90_hold30      -8977.43
    4 2025-09-02 2025-09-30 window15_levelq90_hold30      -7563.63
```

## Family: PBO = 0.34285714285714286, clusters K = 2, variants net > 0: 0/8

Full-period results of all variants (in-sample for selection; not evidence of an edge):

```
                               net  trades  avg_ticks
window15_levelq90_hold30  -4780.31     331      -0.79
window15_levelq90_hold15  -9167.81     331      -1.85
window15_levelq75_hold30 -14560.37     637      -1.47
window5_levelq90_hold30  -17501.16     416      -3.00
window5_levelq90_hold15  -19713.66     416      -3.43
window5_levelq75_hold30  -23449.26     726      -2.22
window15_levelq75_hold15 -25485.37     637      -2.84
window5_levelq75_hold15  -35836.76     726      -3.59
```


## Reading (2026-10-04)
Verdict "insufficient data" (one year cannot pass G7), but the substance is negative: **0 of 8 variants are net
positive over the full 238 days**. The walk-forward OOS +$2,566 over 171 trades (+1.56 ticks/trade gross of
selection luck, t 0.65) comes from the fold-by-fold choice landing on good months, not from a stable rule
(PBO 0.34, island, not a medoid). Strong 5/15-min aggressor imbalance does not continue enough over 15-30 min
to pay an ES round trip. Not worth buying more tick data for this idea.
