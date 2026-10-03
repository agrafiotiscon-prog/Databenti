---
type: result
date: 2026-10-03
tags: [phase-5, H-001, gates]
---
# H-001 evaluation (D-020): verdict **insufficient data**

Data: 238 RTH days 2024-11-01..2025-09-30, quotes rebuilt from trades (D-019). 72 variants, 5 walk-forward folds (6 m train / 1 m test, 1-day embargo).

## Gates
```
                                                          requirement result                                                    evidence
gate                                                                                                                                    
G1                                                  >= 200 OOS trades   FAIL                                               oos_trades=14
G2                                OOS net > 0 at 1.5x fees and 250 ms   FAIL                          oos_net_stress=-144.70999999999998
G3                      DSR >= 0.95 (raw N) and OOS mean-trade t >= 2   FAIL    dsr_raw=0.0008706706515871354, oos_t=-0.3663338143666064
G4                                                        PBO <= 0.10   FAIL                                     pbo=0.15714285714285714
G5                                                 +-20% plateau test   FAIL                                          plateau_pass=False
G6                                 not concentrated (red flags clear)   FAIL                                           concentrated=True
G7                       positive in >= 60% of OOS years (>= 2 years)   FAIL                         years_positive_share=0.0, n_years=1
G8                           tier-B fill check does not flip the sign   FAIL                              not measured: tier_b_same_sign
G9                 MC 5th pct net > 0 and P(loss) <= 10% at 1.5x fees   FAIL                mc_net_p5=-268.1181127444705, mc_p_loss=0.86
G10   cluster medoid; >= 70% of its cluster profitable; not an island   FAIL  is_medoid=False, cluster_share_profitable=0.0, island=True
G11                        DSR >= 0.95 with cluster-based effective K   FAIL                                  dsr_k=0.010337951108233656
```

## Out-of-sample (concatenated test months)
```
{
 "trades": 14,
 "flag_few_trades": true,
 "net_pnl": -113.14,
 "win_rate": 0.5,
 "avg_trade": -8.0814,
 "median_trade": -4.51,
 "avg_ticks": -0.2857,
 "fees": 63.14,
 "profit_factor": 0.8135,
 "t_stat": -0.3663
}
```
Net PnL by cost scenario: {'base': -113.14, 'fees1.5': -144.71, 'fees1.5_lat250': -144.71, 'fees2_lat500': -176.28}

### Per month
```
              size     sum
trading_date              
2025-05          1 -129.51
2025-08          3  211.47
2025-09         10 -195.10
```

## Variant chosen per fold
```
 fold  test_from    test_to                                                         variant  train_net_p5
    0 2025-05-02 2025-05-30 min_vol500_level_tol1_div_lookback10_stop_ticks10_target_ticks6       -517.65
    1 2025-06-03 2025-06-30 min_vol500_level_tol1_div_lookback20_stop_ticks10_target_ticks6       -713.18
    2 2025-07-02 2025-07-31  min_vol500_level_tol1_div_lookback20_stop_ticks6_target_ticks6       -245.30
    3 2025-08-04 2025-08-29  min_vol300_level_tol1_div_lookback20_stop_ticks6_target_ticks6       -177.06
    4 2025-09-02 2025-09-30  min_vol300_level_tol1_div_lookback20_stop_ticks6_target_ticks6       -177.06
```

## Family: PBO = 0.15714285714285714, clusters K = 18, DSR raw = 0.0008706706515871354, DSR K = 0.010337951108233656

Full-period results of all 72 variants (in-sample for selection; not evidence of an edge):

```
                                                                       net  trades  sharpe_ann
min_vol500_level_tol2_div_lookback10_stop_ticks10_target_ticks16    150.78      22        0.21
min_vol500_level_tol1_div_lookback10_stop_ticks10_target_ticks16     82.35      15        0.15
min_vol300_level_tol2_div_lookback10_stop_ticks10_target_ticks16     -3.06     106       -0.00
min_vol500_level_tol1_div_lookback10_stop_ticks10_target_ticks6    -142.65      15       -0.38
min_vol500_level_tol1_div_lookback10_stop_ticks6_target_ticks6     -142.65      15       -0.50
min_vol500_level_tol1_div_lookback10_stop_ticks10_target_ticks10   -292.65      15       -0.64
min_vol500_level_tol1_div_lookback10_stop_ticks6_target_ticks16    -367.65      15       -0.87
min_vol500_level_tol1_div_lookback20_stop_ticks10_target_ticks6    -424.61      11       -1.23
min_vol500_level_tol1_div_lookback20_stop_ticks6_target_ticks6     -424.61      11       -1.71
min_vol300_level_tol1_div_lookback10_stop_ticks10_target_ticks16   -448.69      69       -0.41
min_vol500_level_tol2_div_lookback10_stop_ticks10_target_ticks10   -449.22      22       -0.81
min_vol500_level_tol2_div_lookback10_stop_ticks10_target_ticks6    -449.22      22       -0.99
min_vol500_level_tol2_div_lookback10_stop_ticks6_target_ticks6     -549.22      22       -1.46
min_vol500_level_tol1_div_lookback10_stop_ticks6_target_ticks10    -592.65      15       -1.77
min_vol500_level_tol1_div_lookback20_stop_ticks10_target_ticks16   -599.61      11       -1.34
min_vol500_level_tol1_div_lookback20_stop_ticks6_target_ticks16    -599.61      11       -1.95
min_vol300_level_tol1_div_lookback20_stop_ticks6_target_ticks6     -605.01      51       -1.16
min_vol500_level_tol2_div_lookback10_stop_ticks6_target_ticks16    -649.22      22       -1.12
min_vol500_level_tol2_div_lookback20_stop_ticks6_target_ticks6     -672.16      16       -2.25
min_vol500_level_tol1_div_lookback20_stop_ticks6_target_ticks10    -674.61      11       -2.52
min_vol500_level_tol2_div_lookback20_stop_ticks6_target_ticks16    -722.16      16       -1.84
min_vol500_level_tol1_div_lookback20_stop_ticks10_target_ticks10   -749.61      11       -1.91
min_vol300_level_tol1_div_lookback10_stop_ticks10_target_ticks10   -786.19      69       -0.80
min_vol300_level_tol1_div_lookback20_stop_ticks6_target_ticks10    -855.01      51       -1.43
min_vol500_level_tol2_div_lookback20_stop_ticks10_target_ticks6    -872.16      16       -2.03
min_vol500_level_tol2_div_lookback20_stop_ticks6_target_ticks10    -872.16      16       -2.65
min_vol500_level_tol2_div_lookback20_stop_ticks10_target_ticks16   -922.16      16       -1.69
min_vol300_level_tol2_div_lookback20_stop_ticks10_target_ticks16   -930.26      76       -0.79
min_vol500_level_tol2_div_lookback10_stop_ticks6_target_ticks10    -949.22      22       -2.13
min_vol300_level_tol1_div_lookback20_stop_ticks6_target_ticks16   -1030.01      51       -1.45
min_vol300_level_tol1_div_lookback20_stop_ticks10_target_ticks16  -1063.00      50       -1.23
min_vol300_level_tol1_div_lookback20_stop_ticks10_target_ticks6   -1075.50      50       -1.69
min_vol500_level_tol2_div_lookback20_stop_ticks10_target_ticks10  -1147.16      16       -2.40
min_vol300_level_tol1_div_lookback10_stop_ticks6_target_ticks6    -1215.70      70       -1.99
min_vol300_level_tol2_div_lookback20_stop_ticks6_target_ticks16   -1247.27      77       -1.37
min_vol300_level_tol1_div_lookback10_stop_ticks10_target_ticks6   -1248.69      69       -1.62
min_vol300_level_tol1_div_lookback20_stop_ticks10_target_ticks10  -1300.50      50       -1.72
min_vol300_level_tol2_div_lookback20_stop_ticks6_target_ticks6    -1322.27      77       -1.99
min_vol300_level_tol2_div_lookback10_stop_ticks10_target_ticks10  -1328.06     106       -1.05
min_vol300_level_tol1_div_lookback10_stop_ticks6_target_ticks10   -1365.70      70       -1.88
min_vol300_level_tol1_div_lookback10_stop_ticks6_target_ticks16   -1440.70      70       -1.75
min_vol300_level_tol2_div_lookback20_stop_ticks6_target_ticks10   -1522.27      77       -2.04
min_vol300_level_tol2_div_lookback10_stop_ticks10_target_ticks6   -1840.56     106       -1.81
min_vol300_level_tol2_div_lookback20_stop_ticks10_target_ticks6   -1842.76      76       -2.12
min_vol300_level_tol2_div_lookback20_stop_ticks10_target_ticks10  -1917.76      76       -1.90
min_vol300_level_tol2_div_lookback10_stop_ticks6_target_ticks6    -2287.08     108       -2.90
min_vol300_level_tol2_div_lookback10_stop_ticks6_target_ticks16   -2612.08     108       -2.50
min_vol300_level_tol2_div_lookback10_stop_ticks6_target_ticks10   -2787.08     108       -2.95
min_vol150_level_tol1_div_lookback20_stop_ticks6_target_ticks16   -5342.03     353       -2.64
min_vol150_level_tol1_div_lookback20_stop_ticks10_target_ticks16  -6424.77     327       -2.56
min_vol150_level_tol1_div_lookback20_stop_ticks10_target_ticks10  -6732.37     337       -3.16
min_vol150_level_tol1_div_lookback20_stop_ticks6_target_ticks10   -7053.11     361       -4.10
min_vol150_level_tol1_div_lookback10_stop_ticks6_target_ticks16   -7170.59     509       -3.02
min_vol150_level_tol1_div_lookback20_stop_ticks6_target_ticks6    -7371.15     365       -5.38
min_vol150_level_tol1_div_lookback20_stop_ticks10_target_ticks6   -7534.43     343       -4.35
min_vol150_level_tol1_div_lookback10_stop_ticks10_target_ticks16  -7565.19     469       -2.45
min_vol150_level_tol2_div_lookback20_stop_ticks10_target_ticks16  -8702.69     469       -2.64
min_vol150_level_tol2_div_lookback10_stop_ticks10_target_ticks16  -9111.65     665       -2.37
min_vol150_level_tol2_div_lookback20_stop_ticks10_target_ticks10  -9293.92     492       -3.44
min_vol150_level_tol1_div_lookback10_stop_ticks10_target_ticks10  -9397.40     490       -3.55
min_vol150_level_tol1_div_lookback10_stop_ticks10_target_ticks6   -9666.08     508       -4.55
min_vol150_level_tol1_div_lookback10_stop_ticks6_target_ticks10   -9733.73     523       -4.63
min_vol150_level_tol1_div_lookback10_stop_ticks6_target_ticks6   -10908.34     534       -6.49
min_vol150_level_tol2_div_lookback20_stop_ticks10_target_ticks6  -10928.19     519       -5.15
min_vol150_level_tol2_div_lookback20_stop_ticks6_target_ticks16  -10972.26     526       -4.11
min_vol150_level_tol2_div_lookback10_stop_ticks10_target_ticks10 -11818.08     708       -3.61
min_vol150_level_tol2_div_lookback20_stop_ticks6_target_ticks10  -11839.91     541       -5.48
min_vol150_level_tol2_div_lookback20_stop_ticks6_target_ticks6   -12005.11     561       -6.89
min_vol150_level_tol2_div_lookback10_stop_ticks10_target_ticks6  -12537.01     751       -4.95
min_vol150_level_tol2_div_lookback10_stop_ticks6_target_ticks16  -12926.96     746       -4.44
min_vol150_level_tol2_div_lookback10_stop_ticks6_target_ticks10  -14404.27     777       -5.70
min_vol150_level_tol2_div_lookback10_stop_ticks6_target_ticks6   -15682.61     811       -7.80
```

Limitations: one year of data (G7 cannot pass); tier-B fill check (G8) not run; no market impact; quotes rebuilt from trades (81% exact).

## Interpretation (added by hand, session 6; the generated sections above are unchanged)
- **Substantive verdict: not promising.** The gate code says "insufficient data" because there
  are < 200 OOS trades, but the whole declared family loses after costs: **2 of 72 variants**
  are net positive over the full period ($150.8 and $82.4, both low-trade variants = noise),
  median variant **−$1,275**, median **−1.25 ticks/trade** after fees. A market round trip costs
  ≈ 1.4 ticks including fees, so the signal's gross edge is ≈ 0.
- Only 14 OOS trades: in every training window all variants lost, so selection on the bootstrap
  5th percentile picked the variant that traded least (it lost least). Expected behaviour of the
  rule, not a bug.
- PBO 0.16, DSR ≈ 0.001 (raw N = 72) and 0.01 (cluster K = 18): no evidence beyond what the
  search itself produces.
- Caveats that cannot rescue it: quotes rebuilt from trades (81% exact, unbiased on average);
  one year only; tier-B check not run. None of these explains a family-wide −1.25 ticks/trade.
- H-001 is **closed**. Its 72 trials stay in the log and count toward future deflation.
