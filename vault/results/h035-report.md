---
type: result
date: 2026-10-04
tags: [R9, H-035, gates]
---
# H-035 month-end rebalancing pressure (equities): gate verdict **not promising**

Month-end rebalancing pressure in equity index futures - trade AGAINST the month's stock-vs-bond outperformance over the last days of the month. 3974 dates 2010-06-07..2025-09-30; 13 folds (3 y / 1 y). DSR N = 218. Capital $1,000,000. outright, side = -sign(ES-ZN MTD), 1 tick + fees per side.

## Coverage (before P&L, D-042)
```
 es_month_ends  events_k3  short_share   zn_first    zn_last
           184        183        0.656 2010-06-07 2025-09-30
```

OOS (walk-forward): {'ann_return_pct': 2.5, 'ann_vol_pct': 7.11, 'sharpe': 0.351, 'max_dd_pct': -14.95, 't_daily': 1.249}
OOS contract trades: 400

## Gates
```
                                                          requirement result                                                    evidence
gate                                                                                                                                    
G1                                                  >= 200 OOS trades   PASS                                              oos_trades=400
G2                                OOS net > 0 at 1.5x fees and 250 ms   PASS                            oos_net_stress=295170.5699999997
G3                      DSR >= 0.95 (raw N) and OOS mean-trade t >= 2   FAIL                     dsr_raw=0.5746852118490479, oos_t=1.249
G4                                                        PBO <= 0.10   FAIL                                      pbo=0.6546231546231546
G5                                                 +-20% plateau test   PASS                                           plateau_pass=True
G6                                 not concentrated (red flags clear)   FAIL                                           concentrated=True
G7                       positive in >= 60% of OOS years (>= 2 years)   FAIL         years_positive_share=0.5384615384615384, n_years=13
G8                           tier-B fill check does not flip the sign   PASS                                       tier_b_same_sign=True
G9                 MC 5th pct net > 0 and P(loss) <= 10% at 1.5x fees   FAIL              mc_net_p5=-79474.60500000007, mc_p_loss=0.0935
G10   cluster medoid; >= 70% of its cluster profitable; not an island   PASS  is_medoid=True, cluster_share_profitable=1.0, island=False
G11                        DSR >= 0.95 with cluster-based effective K   FAIL                                    dsr_k=0.8485726162392146
G12   beats a placebo / random-timing benchmark (one-sided p <= 0.05)   PASS                               placebo_p=0.04666666666666667
```

Placebo: real OOS net 315,850 vs placebo median -14,874 (95th pct 306,647); p = 0.047

Net by scenario (OOS): {'base': 315850, 'fees1.5': 313456, 'stress': 295171, 'plus1tick': 297565}

### By year (OOS)
```
       oos_net  return_pct
2013  -38195.0       -3.82
2014   26086.0        2.61
2015  -14862.0       -1.49
2016   58634.0        5.86
2017   -2441.0       -0.24
2018  151669.0       15.17
2019  -25038.0       -2.50
2020  113574.0       11.36
2021  -21696.0       -2.17
2022   13857.0        1.39
2023   12264.0        1.23
2024   53960.0        5.40
2025  -11964.0       -1.20
```

## Variant chosen per fold
```
 fold                   test variant  train_net_p5
    0 2013-06-04..2014-05-30    5|es         75380
    1 2014-06-03..2015-05-29   5|eq4         -6151
    2 2015-06-02..2016-05-31   3|eq4        -70731
    3 2016-06-02..2017-05-31   3|eq4        -52688
    4 2017-06-02..2018-05-31    3|es          8863
    5 2018-06-04..2019-05-31   5|eq4        -37623
    6 2019-06-04..2020-05-29   5|eq4         -6333
    7 2020-06-02..2021-05-31    5|es        -19491
    8 2021-06-02..2022-05-31   5|eq4         17447
    9 2022-06-02..2023-05-31   5|eq4        -85445
   10 2023-06-02..2024-05-31   3|eq4        -82297
   11 2024-06-04..2025-05-30    3|es       -153019
   12 2025-06-03..2025-09-30    3|es       -122731
```

## Family (full period): PBO = 0.655, K = 2
```
       ann_return_pct  ann_vol_pct  sharpe  max_dd_pct  t_daily  net_full  trades
3|es             1.95         6.01   0.324      -17.87    1.287  306836.0   183.0
3|eq4            1.72         5.80   0.297      -17.17    1.180  271829.0   648.0
5|es             3.88         7.67   0.506      -14.28    2.010  612318.0   183.0
5|eq4            3.52         7.30   0.482      -14.05    1.915  555424.0   648.0
```


## Reading (2026-10-04)
Not promoted (6/12: G1, G2, G5, G8, G10, G12), but the **second idea ever to pass the placebo** (p 0.047): trading against
the month's stock-vs-bond outperformance over the last days beats the same rule on random dates. All 4 variants are positive
full-period; the 5-day window is strongest (5|es t 2.0, +3.9%/yr at 7.7% vol). Fails significance (OOS t 1.25, DSR), PBO 0.65
(the fold choice flips between k=3 and k=5), concentration (2018 +15%, 2020 +11%) and G7 (7/13 years). It is the equity side
of the same month-end rebalancing flow as H-030 (stocks sold, bonds bought when stocks outperformed - 66% of months are
shorts). No unseen equity market can confirm it (all US index futures co-move), so the rule 5|es is added to forward paper
tracking as a **watch sleeve** (not part of the book) - D-065.
