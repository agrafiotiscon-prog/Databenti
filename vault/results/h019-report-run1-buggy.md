---
type: result
date: 2026-10-03
tags: [phase-5, H-019, gates]
---
# [SUPERSEDED: data bug, see D-041] H-019 evaluation (D-023/D-026): gate verdict **insufficient data**

Month-end rebalancing - fade the month-to-date ES move over the last 4 trading days of the month. 3943 dates 2010-06-07..2025-09-30; 13 folds (3 y / 1 y). DSR N = 162. Costs: 1 tick adverse per side + fees (stress 2 ticks + fees x1.5).

## Gates
```
                                                          requirement result                                                    evidence
gate                                                                                                                                    
G1                                                  >= 200 OOS trades   FAIL                                               oos_trades=30
G2                                OOS net > 0 at 1.5x fees and 250 ms   PASS                           oos_net_stress=31547.050000000003
G3                      DSR >= 0.95 (raw N) and OOS mean-trade t >= 2   FAIL        dsr_raw=0.5198708938934435, oos_t=1.4727915611961808
G4                                                        PBO <= 0.10   FAIL                                     pbo=0.18477078477078476
G5                                                 +-20% plateau test   FAIL                                          plateau_pass=False
G6                                 not concentrated (red flags clear)   FAIL                                           concentrated=True
G7                       positive in >= 60% of OOS years (>= 2 years)   PASS         years_positive_share=0.7692307692307693, n_years=13
G8                           tier-B fill check does not flip the sign   PASS                                       tier_b_same_sign=True
G9                 MC 5th pct net > 0 and P(loss) <= 10% at 1.5x fees   PASS                 mc_net_p5=14707.185140058178, mc_p_loss=0.0
G10   cluster medoid; >= 70% of its cluster profitable; not an island   PASS  is_medoid=True, cluster_share_profitable=1.0, island=False
G11                        DSR >= 0.95 with cluster-based effective K   PASS                                    dsr_k=0.9544056363943946
G12   beats a placebo / random-timing benchmark (one-sided p <= 0.05)   PASS                                            placebo_p=0.0287
```

## Out-of-sample
```
{
 "trades": 30,
 "flag_few_trades": true,
 "net_pnl": 32364.7,
 "win_rate": 0.5,
 "avg_trade": 1078.8233,
 "median_trade": 32.99,
 "avg_ticks": 86.6667,
 "fees": 135.3,
 "profit_factor": 2.2809,
 "t_stat": 1.4728
}
```
Net by scenario: {'base': 32364.7, 'fees1.5': 32297.1, 'stress': 31547.1, 'plus1tick': 31614.7}

### By year (OOS)
```
      oos_net  oos_trades
2013     95.5         1.0
2014   -976.0         3.0
2015   4678.5         2.0
2016      0.0         NaN
2017      0.0         NaN
2018    699.0         3.0
2019   1316.0         2.0
2020    657.0         4.0
2021   3461.5         3.0
2022  10969.5         4.0
2023   6536.5         3.0
2024   2349.0         3.0
2025   2578.5         2.0
```

## Variant chosen per fold
```
 fold                   test       variant  train_net_p5
    0 2013-06-04..2014-05-30 min_abs_bp200       -1500.8
    1 2014-06-03..2015-05-29 min_abs_bp200       -2395.4
    2 2015-06-02..2016-05-31 min_abs_bp200       -1654.2
    3 2016-06-02..2017-05-31 min_abs_bp200       -2384.8
    4 2017-06-02..2018-05-31 min_abs_bp200       -1314.6
    5 2018-06-04..2019-05-31 min_abs_bp200        -727.1
    6 2019-06-04..2020-05-29 min_abs_bp200       -2047.9
    7 2020-06-02..2021-05-31   min_abs_bp0      -10197.3
    8 2021-06-02..2022-05-31   min_abs_bp0      -10466.8
    9 2022-06-02..2023-05-31   min_abs_bp0      -20876.3
   10 2023-06-02..2024-05-31   min_abs_bp0      -10345.2
   11 2024-06-04..2025-05-30   min_abs_bp0      -12396.9
   12 2025-06-03..2025-09-30   min_abs_bp0        3717.2
```

## Family: PBO = 0.185, K = 1

```
                   net  trades  avg_ticks
min_abs_bp0    35925.9      58     49.914
min_abs_bp200  12438.7      33     30.515
```

