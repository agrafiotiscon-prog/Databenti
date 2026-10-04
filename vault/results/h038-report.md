---
type: result
date: 2026-10-04
tags: [R9, H-038, gates]
---
# H-038 return seasonality: gate verdict **not promising**

Return seasonality - hold each futures market in the direction of its average return in the same calendar month over the previous years. 3980 dates 2010-06-07..2025-09-30; 13 folds (3 y / 1 y). DSR N = 233. Capital $1,000,000. engine sizing with seasonal sign signal, 1 tick + fees.

## Coverage (before P&L, D-042)
```
market  share_signal_5y  share_signal_10y
    ES            0.676             0.349
    NQ            0.676             0.349
   RTY            0.396             0.000
    YM            0.676             0.349
    ZT            0.676             0.349
    ZF            0.676             0.349
    ZN            0.676             0.349
    ZB            0.676             0.349
    CL            0.675             0.348
    NG            0.675             0.348
    RB            0.675             0.348
    HO            0.675             0.348
    GC            0.675             0.349
    SI            0.675             0.349
    HG            0.675             0.349
    6E            0.676             0.349
    6J            0.676             0.349
    6B            0.676             0.349
    6A            0.676             0.349
    6C            0.676             0.349
    6S            0.676             0.349
    ZC            0.674             0.348
    ZS            0.674             0.348
    ZW            0.674             0.348
    LE            0.675             0.348
    HE            0.675             0.348
```

OOS (walk-forward): {'ann_return_pct': -7.25, 'ann_vol_pct': 13.11, 'sharpe': -0.553, 'max_dd_pct': -95.4, 't_daily': -1.968}
OOS contract trades: 2741

## Gates
```
                                                          requirement result                                                   evidence
gate                                                                                                                                   
G1                                                  >= 200 OOS trades   PASS                                            oos_trades=2741
G2                                OOS net > 0 at 1.5x fees and 250 ms   FAIL                         oos_net_stress=-1016106.1099999996
G3                      DSR >= 0.95 (raw N) and OOS mean-trade t >= 2   FAIL                dsr_raw=0.0033871389555268916, oos_t=-1.968
G4                                                        PBO <= 0.10   FAIL                                     pbo=0.9795648795648796
G5                                                 +-20% plateau test   FAIL                                         plateau_pass=False
G6                                 not concentrated (red flags clear)   FAIL                                          concentrated=True
G7                       positive in >= 60% of OOS years (>= 2 years)   FAIL       years_positive_share=0.23076923076923078, n_years=13
G8                           tier-B fill check does not flip the sign   FAIL                                     tier_b_same_sign=False
G9                 MC 5th pct net > 0 and P(loss) <= 10% at 1.5x fees   FAIL            mc_net_p5=-1755630.6110000003, mc_p_loss=0.9645
G10   cluster medoid; >= 70% of its cluster profitable; not an island   FAIL  is_medoid=True, cluster_share_profitable=0.0, island=True
G11                        DSR >= 0.95 with cluster-based effective K   FAIL                                 dsr_k=0.024093140195077578
G12   beats a placebo / random-timing benchmark (one-sided p <= 0.05)   FAIL                               placebo_p=0.9666666666666667
```

Placebo: real OOS net -918,006 vs placebo median 47,414 (95th pct 895,792); p = 0.967

Net by scenario (OOS): {'base': -918006, 'fees1.5': -927453, 'stress': -1016106, 'plus1tick': -1006660}

### By year (OOS)
```
       oos_net  return_pct
2013       0.0        0.00
2014       0.0        0.00
2015 -366230.0      -36.62
2016   39435.0        3.94
2017       0.0        0.00
2018       0.0        0.00
2019       0.0        0.00
2020   64667.0        6.47
2021   41318.0        4.13
2022  -51700.0       -5.17
2023 -325849.0      -32.58
2024 -163754.0      -16.38
2025 -155894.0      -15.59
```

## Variant chosen per fold
```
 fold                   test    variant  train_net_p5
    0 2013-06-04..2014-05-30  5|commods             0
    1 2014-06-03..2015-05-29  5|commods             0
    2 2015-06-02..2016-05-31  5|commods             0
    3 2016-06-02..2017-05-31 10|commods             0
    4 2017-06-02..2018-05-31 10|commods             0
    5 2018-06-04..2019-05-31 10|commods             0
    6 2019-06-04..2020-05-29 10|commods             0
    7 2020-06-02..2021-05-31 10|commods             0
    8 2021-06-02..2022-05-31 10|commods       -350134
    9 2022-06-02..2023-05-31 10|commods       -366702
   10 2023-06-02..2024-05-31 10|commods       -686590
   11 2024-06-04..2025-05-30      5|all       -275446
   12 2025-06-03..2025-09-30      5|all       -390974
```

## Family (full period): PBO = 0.980, K = 2
```
            ann_return_pct  ann_vol_pct  sharpe  max_dd_pct  t_daily  net_full  trades
5|commods            -5.89        13.50  -0.436      -95.83   -1.733 -929639.0  4196.0
10|commods           -3.01        10.17  -0.296      -64.06   -1.178 -476123.0  2006.0
5|all                -4.26        14.27  -0.299     -103.57   -1.187 -673486.0  6585.0
10|all               -3.03        10.91  -0.277      -85.40   -1.102 -477990.0  3507.0
```

