---
type: result
date: 2026-10-04
tags: [R9, H-031, gates]
---
# H-031 Treasury auction cycle: gate verdict **not promising**

Treasury auction cycle - short the matching future before note/bond auctions, long after (Lou, Yan & Zhang 2013). 3973 dates 2010-06-07..2025-09-30; 13 folds (3 y / 1 y). DSR N = 200. Capital $1,000,000. outright short pre / long post auction, closes, 1 tick + fees per side, $250k per position.

## Coverage (before P&L, D-042)
```
market  auctions_in_range  on_trading_dates skipped
    ZT                184               184       -
    ZF                184               184       -
    ZN                369               369       -
    ZB                250               250       -
```

OOS (walk-forward): {'ann_return_pct': 0.24, 'ann_vol_pct': 1.73, 'sharpe': 0.14, 'max_dd_pct': -5.47, 't_daily': 0.497}
OOS contract trades: 807

## Gates
```
                                                          requirement result                                                    evidence
gate                                                                                                                                    
G1                                                  >= 200 OOS trades   PASS                                              oos_trades=807
G2                                OOS net > 0 at 1.5x fees and 250 ms   FAIL                          oos_net_stress=-24120.614999999198
G3                      DSR >= 0.95 (raw N) and OOS mean-trade t >= 2   FAIL                    dsr_raw=0.14027065014465756, oos_t=0.497
G4                                                        PBO <= 0.10   FAIL                                      pbo=0.6933177933177933
G5                                                 +-20% plateau test   FAIL                                          plateau_pass=False
G6                                 not concentrated (red flags clear)   FAIL                                           concentrated=True
G7                       positive in >= 60% of OOS years (>= 2 years)   PASS         years_positive_share=0.6153846153846154, n_years=13
G8                           tier-B fill check does not flip the sign   FAIL                                      tier_b_same_sign=False
G9                 MC 5th pct net > 0 and P(loss) <= 10% at 1.5x fees   FAIL               mc_net_p5=-63999.5196249997, mc_p_loss=0.3135
G10   cluster medoid; >= 70% of its cluster profitable; not an island   PASS  is_medoid=True, cluster_share_profitable=1.0, island=False
G11                        DSR >= 0.95 with cluster-based effective K   FAIL                                    dsr_k=0.5241191665188217
G12   beats a placebo / random-timing benchmark (one-sided p <= 0.05)   PASS                                               placebo_p=0.0
```

Placebo: real OOS net 30,591 vs placebo median -93,553 (95th pct -32,327); p = 0.000

Net by scenario (OOS): {'base': 30591, 'fees1.5': 27286, 'stress': -24121, 'plus1tick': -20815}

### By year (OOS)
```
      oos_net  return_pct
2013  -8641.0       -0.86
2014  12359.0        1.24
2015  -2342.0       -0.23
2016  -9922.0       -0.99
2017   6591.0        0.66
2018   2895.0        0.29
2019    746.0        0.07
2020   4318.0        0.43
2021 -11248.0       -1.12
2022  -3955.0       -0.40
2023  10545.0        1.05
2024  26475.0        2.65
2025   2772.0        0.28
```

## Variant chosen per fold
```
 fold                   test variant  train_net_p5
    0 2013-06-04..2014-05-30  post|3          4112
    1 2014-06-03..2015-05-29  post|3        -19055
    2 2015-06-02..2016-05-31  post|3        -31602
    3 2016-06-02..2017-05-31  post|3        -40051
    4 2017-06-02..2018-05-31  post|3        -42161
    5 2018-06-04..2019-05-31   pre|3        -37375
    6 2019-06-04..2020-05-29   pre|3        -12561
    7 2020-06-02..2021-05-31  post|3        -20460
    8 2021-06-02..2022-05-31  post|5         -5701
    9 2022-06-02..2023-05-31   pre|3          1584
   10 2023-06-02..2024-05-31   pre|3         48341
   11 2024-06-04..2025-05-30   pre|3         38418
   12 2025-06-03..2025-09-30   pre|3         25000
```

## Family (full period): PBO = 0.693, K = 2
```
        ann_return_pct  ann_vol_pct  sharpe  max_dd_pct  t_daily  net_full  trades
pre|3             0.39         1.62   0.238       -9.45    0.944   60773.0   985.0
post|3           -0.16         1.63  -0.097      -10.24   -0.384  -24888.0   987.0
pre|5             0.24         2.36   0.100       -9.90    0.399   37317.0   985.0
post|5           -0.20         2.30  -0.085      -14.28   -0.338  -30807.0   985.0
```


## Reading (2026-10-04)
Not promising (4/12). The pre-auction short is weakly positive (pre|3 full-period t 0.94) and the post-auction
long is negative - the Lou-Yan-Zhang pattern is at most faint after 2010, and does not survive stress costs.
**Caution on G12 (p 0.000):** random short windows lost heavily because Treasuries trended (median −$94k), so beating
the placebo here mostly reflects bond drift, not auction timing. PBO 0.69.
