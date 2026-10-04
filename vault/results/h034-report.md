---
type: result
date: 2026-10-04
tags: [R9, H-034, gates]
---
# H-034 turn of the month (equities): gate verdict **not promising**

Turn of the month in US equity index futures - long from the close before the last trading day to the 1st/3rd trading day of the new month. 3974 dates 2010-06-07..2025-09-30; 13 folds (3 y / 1 y). DSR N = 218. Capital $1,000,000. long outright T-1 close -> n-th day of new month, 1 tick + fees per side.

## Coverage (before P&L, D-042)
```
market      first       last  month_ends  windows_n3
    ES 2010-06-07 2025-09-30         184         183
    NQ 2010-06-07 2025-09-30         184         183
   RTY 2017-07-10 2025-09-30          99          98
    YM 2010-06-07 2025-09-30         184         183
```

OOS (walk-forward): {'ann_return_pct': -0.51, 'ann_vol_pct': 4.84, 'sharpe': -0.105, 'max_dd_pct': -15.03, 't_daily': -0.375}
OOS contract trades: 422

## Gates
```
                                                          requirement result                                                    evidence
gate                                                                                                                                    
G1                                                  >= 200 OOS trades   PASS                                              oos_trades=422
G2                                OOS net > 0 at 1.5x fees and 250 ms   FAIL                            oos_net_stress=-82769.7100000004
G3                      DSR >= 0.95 (raw N) and OOS mean-trade t >= 2   FAIL                   dsr_raw=0.25063136310570255, oos_t=-0.375
G4                                                        PBO <= 0.10   FAIL                                      pbo=0.8600621600621601
G5                                                 +-20% plateau test   PASS                                           plateau_pass=True
G6                                 not concentrated (red flags clear)   FAIL                                           concentrated=True
G7                       positive in >= 60% of OOS years (>= 2 years)   FAIL        years_positive_share=0.23076923076923078, n_years=13
G8                           tier-B fill check does not flip the sign   FAIL                                      tier_b_same_sign=False
G9                 MC 5th pct net > 0 and P(loss) <= 10% at 1.5x fees   FAIL              mc_net_p5=-361563.11200000043, mc_p_loss=0.652
G10   cluster medoid; >= 70% of its cluster profitable; not an island   PASS  is_medoid=True, cluster_share_profitable=1.0, island=False
G11                        DSR >= 0.95 with cluster-based effective K   FAIL                                    dsr_k=0.3353979026415874
G12   beats a placebo / random-timing benchmark (one-sided p <= 0.05)   FAIL                                placebo_p=0.8766666666666667
```

Placebo: real OOS net -64,463 vs placebo median 96,311 (95th pct 335,936); p = 0.877

Net by scenario (OOS): {'base': -64463, 'fees1.5': -66750, 'stress': -82770, 'plus1tick': -80483}

### By year (OOS)
```
      oos_net  return_pct
2013  -1383.0       -0.14
2014 -29603.0       -2.96
2015 -11087.0       -1.11
2016 -15759.0       -1.58
2017  29206.0        2.92
2018  22006.0        2.20
2019 -28812.0       -2.88
2020 -20507.0       -2.05
2021  -4856.0       -0.49
2022 -16901.0       -1.69
2023  60772.0        6.08
2024 -22787.0       -2.28
2025 -24750.0       -2.48
```

## Variant chosen per fold
```
 fold                   test variant  train_net_p5
    0 2013-06-04..2014-05-30   3|eq4         -4839
    1 2014-06-03..2015-05-29   1|eq4       -126091
    2 2015-06-02..2016-05-31   3|eq4        -97250
    3 2016-06-02..2017-05-31   1|eq4       -124822
    4 2017-06-02..2018-05-31   1|eq4       -119594
    5 2018-06-04..2019-05-31   1|eq4        -93867
    6 2019-06-04..2020-05-29   1|eq4        -24270
    7 2020-06-02..2021-05-31    1|es       -224762
    8 2021-06-02..2022-05-31    1|es       -138285
    9 2022-06-02..2023-05-31    3|es       -165512
   10 2023-06-02..2024-05-31   1|eq4        -41484
   11 2024-06-04..2025-05-30   1|eq4        -50753
   12 2025-06-03..2025-09-30    1|es        -17381
```

## Family (full period): PBO = 0.860, K = 2
```
       ann_return_pct  ann_vol_pct  sharpe  max_dd_pct  t_daily  net_full  trades
1|es             0.66         4.98   0.132      -13.61    0.523  103549.0   183.0
3|es             1.20         7.10   0.169      -18.62    0.673  189661.0   183.0
1|eq4            0.46         4.58   0.100      -15.39    0.398   72424.0   647.0
3|eq4            0.78         6.82   0.115      -20.43    0.457  123734.0   647.0
```


## Reading (2026-10-04)
Not promising (3/12). Every variant is mildly positive full-period (t 0.4-0.7) but random 4-day windows earn more
(placebo median +$96k vs real OOS −$64k, p 0.88): the turn-of-the-month effect is not distinguishable from equity drift
in 2010-2025 index futures. Closed.
