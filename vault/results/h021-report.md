---
type: result
date: 2026-10-03
tags: [phase-5, H-021, gates]
---
# H-021 evaluation (D-023/D-026): gate verdict **insufficient data**

Buy ES after a sharp 3-day decline (liquidity provision to mechanical de-risking), fixed hold. 3943 dates 2010-06-07..2025-09-30; 13 folds (3 y / 1 y). DSR N = 170. Costs: 1 tick adverse per side + fees (stress 2 ticks + fees x1.5).

## Gates
```
                                                          requirement result                                                    evidence
gate                                                                                                                                    
G1                                                  >= 200 OOS trades   FAIL                                               oos_trades=94
G2                                OOS net > 0 at 1.5x fees and 250 ms   PASS                           oos_net_stress=11614.090000000011
G3                      DSR >= 0.95 (raw N) and OOS mean-trade t >= 2   FAIL      dsr_raw=0.042605752764508176, oos_t=0.2488552735326059
G4                                                        PBO <= 0.10   FAIL                                     pbo=0.30753690753690754
G5                                                 +-20% plateau test   FAIL                                          plateau_pass=False
G6                                 not concentrated (red flags clear)   FAIL                                           concentrated=True
G7                       positive in >= 60% of OOS years (>= 2 years)   PASS         years_positive_share=0.6923076923076923, n_years=13
G8                           tier-B fill check does not flip the sign   PASS                                       tier_b_same_sign=True
G9                 MC 5th pct net > 0 and P(loss) <= 10% at 1.5x fees   FAIL              mc_net_p5=-16982.103456452398, mc_p_loss=0.224
G10   cluster medoid; >= 70% of its cluster profitable; not an island   FAIL  is_medoid=False, cluster_share_profitable=0.5, island=True
G11                        DSR >= 0.95 with cluster-based effective K   FAIL                                    dsr_k=0.5855146966711906
G12   beats a placebo / random-timing benchmark (one-sided p <= 0.05)   FAIL                                            placebo_p=0.9872
```

## Out-of-sample
```
{
 "trades": 94,
 "flag_few_trades": true,
 "net_pnl": 14176.06,
 "win_rate": 0.5638,
 "avg_trade": 150.8091,
 "median_trade": 626.74,
 "avg_ticks": 12.4255,
 "fees": 423.94,
 "profit_factor": 1.0798,
 "t_stat": 0.2489
}
```
Net by scenario: {'base': 14176.1, 'fees1.5': 13964.1, 'stress': 11614.1, 'plus1tick': 11826.1}

### By year (OOS)
```
      oos_net  oos_trades
2013   1794.5           4
2014    733.4          12
2015   4930.9           7
2016   8368.4           7
2017   5640.0           5
2018 -14587.1          11
2019   2353.5           2
2020  -8152.1           6
2021  41851.4           8
2022 -17241.6          12
2023   3951.4           8
2024   6022.9           6
2025 -21489.6           6
```

## Variant chosen per fold
```
 fold                   test        variant  train_net_p5
    0 2013-06-04..2014-05-30 z_min1.5_hold3        1956.2
    1 2014-06-03..2015-05-29 z_min1.5_hold3        2683.0
    2 2015-06-02..2016-05-31 z_min1.5_hold5        5527.5
    3 2016-06-02..2017-05-31 z_min1.5_hold5       -5658.9
    4 2017-06-02..2018-05-31 z_min1.5_hold5        2195.8
    5 2018-06-04..2019-05-31 z_min1.5_hold5       -3175.2
    6 2019-06-04..2020-05-29 z_min2.0_hold5       -6791.8
    7 2020-06-02..2021-05-31 z_min2.0_hold5      -62355.5
    8 2021-06-02..2022-05-31 z_min2.0_hold5      -31129.3
    9 2022-06-02..2023-05-31 z_min1.5_hold5      -14343.9
   10 2023-06-02..2024-05-31 z_min1.5_hold5       10031.3
   11 2024-06-04..2025-05-30 z_min1.5_hold5      -22973.3
   12 2025-06-03..2025-09-30 z_min2.0_hold3      -49299.0
```

## Family: PBO = 0.308, K = 2

```
                    net  trades  avg_ticks
z_min1.5_hold3   6586.6     136      4.235
z_min2.0_hold3 -42120.2      71    -47.099
z_min1.5_hold5  56383.8     120     37.950
z_min2.0_hold5   2468.3      68      3.265
```

