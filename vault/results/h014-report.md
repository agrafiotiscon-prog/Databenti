---
type: result
date: 2026-10-03
tags: [phase-5, H-014, gates]
---
# H-014 evaluation (D-023/D-026): gate verdict **not promising**

Time-series momentum on ES (long/short on the sign of the past N-day return). 3943 dates 2010-06-07..2025-09-30; 13 folds (3 y / 1 y). DSR N = 148. Costs: 1 tick adverse per side + fees (stress 2 ticks + fees x1.5).

## Gates
```
                                                          requirement result                                                     evidence
gate                                                                                                                                     
G1                                                  >= 200 OOS trades   PASS                                               oos_trades=361
G2                                OOS net > 0 at 1.5x fees and 250 ms   PASS                            oos_net_stress=37857.835000000036
G3                      DSR >= 0.95 (raw N) and OOS mean-trade t >= 2   FAIL         dsr_raw=0.4207607077443317, oos_t=0.5128773046536194
G4                                                        PBO <= 0.10   FAIL                                       pbo=0.7274281274281275
G5                                                 +-20% plateau test   PASS                                            plateau_pass=True
G6                                 not concentrated (red flags clear)   FAIL                                            concentrated=True
G7                       positive in >= 60% of OOS years (>= 2 years)   FAIL         years_positive_share=0.38461538461538464, n_years=13
G8                           tier-B fill check does not flip the sign   PASS                                        tier_b_same_sign=True
G9                 MC 5th pct net > 0 and P(loss) <= 10% at 1.5x fees   FAIL                mc_net_p5=-9444.709280218302, mc_p_loss=0.083
G10   cluster medoid; >= 70% of its cluster profitable; not an island   FAIL  is_medoid=False, cluster_share_profitable=1.0, island=False
G11                        DSR >= 0.95 with cluster-based effective K   FAIL                                     dsr_k=0.6613782654655074
G12   beats a placebo / random-timing benchmark (one-sided p <= 0.05)   FAIL                                      not measured: placebo_p
```

## Out-of-sample
```
{
 "trades": 361,
 "flag_few_trades": false,
 "net_pnl": 47696.89,
 "win_rate": 0.554,
 "avg_trade": 132.1243,
 "median_trade": 332.99,
 "avg_ticks": 10.9307,
 "fees": 1628.11,
 "profit_factor": 1.0855,
 "t_stat": 0.5129
}
```
Net by scenario: {'base': 47696.9, 'fees1.5': 46882.8, 'stress': 37857.8, 'plus1tick': 38671.9}

### By year (OOS)
```
      oos_net  oos_trades
2013   7833.4          12
2014  10468.8          18
2015 -10060.3          30
2016  -1489.8          31
2017  23900.8          22
2018 -14306.8          32
2019  -2929.8          26
2020 -25949.9          36
2021  -2025.9          39
2022 -26461.3          33
2023  51155.7          32
2024  64645.2          26
2025 -27083.2          24
```

## Variant chosen per fold
```
 fold                   test     variant  train_net_p5
    0 2013-06-04..2014-05-30 lookback120       -2570.2
    1 2014-06-03..2015-05-29 lookback120       -4163.0
    2 2015-06-02..2016-05-31 lookback250       16739.7
    3 2016-06-02..2017-05-31 lookback120      -11860.6
    4 2017-06-02..2018-05-31 lookback120       -5515.3
    5 2018-06-04..2019-05-31 lookback120        8943.7
    6 2019-06-04..2020-05-29  lookback60      -15890.0
    7 2020-06-02..2021-05-31  lookback20      -50567.0
    8 2021-06-02..2022-05-31  lookback60      -59047.8
    9 2022-06-02..2023-05-31  lookback60      -70912.7
   10 2023-06-02..2024-05-31 lookback250      -45557.5
   11 2024-06-04..2025-05-30 lookback120      -23147.1
   12 2025-06-03..2025-09-30 lookback250        7409.6
```

## Family: PBO = 0.727, K = 2

```
                  net  trades  avg_ticks
lookback20   114188.6     640     14.634
lookback60   115871.5     447     21.098
lookback120   83663.4     410     16.685
lookback250  139424.9     413     27.368
```


## Interpretation (added by hand, session 6)
Not promising: t = 0.51, 5/13 OOS years positive, unstable lookback selection; G12 (placebo) not measured -> FAIL. See [leaderboard](leaderboard.md).
