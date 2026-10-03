---
type: result
date: 2026-10-03
tags: [phase-5, H-020, gates]
---
# H-020 evaluation (D-023/D-026): gate verdict **insufficient data**

Volatility-managed exposure - long ES only while trailing realised volatility is below its 1-year median. 3943 dates 2010-06-07..2025-09-30; 13 folds (3 y / 1 y). DSR N = 166. Costs: 1 tick adverse per side + fees (stress 2 ticks + fees x1.5).

## Gates
```
                                                          requirement result                                                    evidence
gate                                                                                                                                    
G1                                                  >= 200 OOS trades   FAIL                                               oos_trades=79
G2                                OOS net > 0 at 1.5x fees and 250 ms   PASS                            oos_net_stress=180053.0649999999
G3                      DSR >= 0.95 (raw N) and OOS mean-trade t >= 2   FAIL        dsr_raw=0.5636525294229828, oos_t=3.8916802864658133
G4                                                        PBO <= 0.10   PASS                                    pbo=0.000777000777000777
G5                                                 +-20% plateau test   PASS                                           plateau_pass=True
G6                                 not concentrated (red flags clear)   PASS                                          concentrated=False
G7                       positive in >= 60% of OOS years (>= 2 years)   PASS         years_positive_share=0.6923076923076923, n_years=13
G8                           tier-B fill check does not flip the sign   PASS                                       tier_b_same_sign=True
G9                 MC 5th pct net > 0 and P(loss) <= 10% at 1.5x fees   PASS                 mc_net_p5=128639.17422765362, mc_p_loss=0.0
G10   cluster medoid; >= 70% of its cluster profitable; not an island   PASS  is_medoid=True, cluster_share_profitable=1.0, island=False
G11                        DSR >= 0.95 with cluster-based effective K   PASS                                    dsr_k=0.9999997632221154
G12   beats a placebo / random-timing benchmark (one-sided p <= 0.05)   FAIL                                             placebo_p=0.118
```

## Out-of-sample
```
{
 "trades": 79,
 "flag_few_trades": true,
 "net_pnl": 182206.21,
 "win_rate": 0.7215,
 "avg_trade": 2306.4077,
 "median_trade": 1495.49,
 "avg_ticks": 184.8734,
 "fees": 356.29,
 "profit_factor": 3.7644,
 "t_stat": 3.8917
}
```
Net by scenario: {'base': 182206.2, 'fees1.5': 182028.1, 'stress': 180053.1, 'plus1tick': 180231.2}

### By year (OOS)
```
      oos_net  oos_trades
2013  11135.4           6
2014  -1164.6           6
2015  -4438.5           3
2016   9035.4           6
2017  21238.9           8
2018   2565.0           5
2019  14876.4           8
2020  -2669.1           7
2021  45480.9           7
2022  -2867.0           1
2023  46746.9           9
2024  23392.4          10
2025  18874.0           3
```

## Variant chosen per fold
```
 fold                   test        variant  train_net_p5
    0 2013-06-04..2014-05-30 vol_lookback63       -1150.2
    1 2014-06-03..2015-05-29 vol_lookback63        -927.7
    2 2015-06-02..2016-05-31 vol_lookback63       -5011.5
    3 2016-06-02..2017-05-31 vol_lookback63      -13353.1
    4 2017-06-02..2018-05-31 vol_lookback63       -4484.3
    5 2018-06-04..2019-05-31 vol_lookback63        9860.6
    6 2019-06-04..2020-05-29 vol_lookback63        8489.3
    7 2020-06-02..2021-05-31 vol_lookback63        7627.4
    8 2021-06-02..2022-05-31 vol_lookback63       -6120.3
    9 2022-06-02..2023-05-31 vol_lookback63       13063.3
   10 2023-06-02..2024-05-31 vol_lookback63       -1316.4
   11 2024-06-04..2025-05-30 vol_lookback63       35465.2
   12 2025-06-03..2025-09-30 vol_lookback63       12422.8
```

## Family: PBO = 0.001, K = 1

```
                     net  trades  avg_ticks
vol_lookback21  106284.2     131     65.267
vol_lookback63  193064.6      91    170.088
```

