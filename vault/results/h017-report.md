---
type: result
date: 2026-10-03
tags: [phase-5, H-017, gates]
---
# H-017 evaluation (D-023/D-026): gate verdict **insufficient data**

Option-expiration week (long from the Friday before OPEX week to the Thursday before expiration). 3943 dates 2010-06-07..2025-09-30; 13 folds (3 y / 1 y). DSR N = 158. Costs: 1 tick adverse per side + fees (stress 2 ticks + fees x1.5).

## Gates
```
                                                          requirement result                                                     evidence
gate                                                                                                                                     
G1                                                  >= 200 OOS trades   FAIL                                                oos_trades=86
G2                                OOS net > 0 at 1.5x fees and 250 ms   PASS                            oos_net_stress=23968.210000000006
G3                      DSR >= 0.95 (raw N) and OOS mean-trade t >= 2   FAIL          dsr_raw=0.7550777474293044, oos_t=0.831773536631076
G4                                                        PBO <= 0.10   FAIL                                       pbo=0.8822066822066822
G5                                                 +-20% plateau test   PASS                                            plateau_pass=True
G6                                 not concentrated (red flags clear)   FAIL                                            concentrated=True
G7                       positive in >= 60% of OOS years (>= 2 years)   PASS          years_positive_share=0.6153846153846154, n_years=13
G8                           tier-B fill check does not flip the sign   PASS                                        tier_b_same_sign=True
G9                 MC 5th pct net > 0 and P(loss) <= 10% at 1.5x fees   PASS                 mc_net_p5=6141.945439987104, mc_p_loss=0.017
G10   cluster medoid; >= 70% of its cluster profitable; not an island   FAIL  is_medoid=False, cluster_share_profitable=1.0, island=False
G11                        DSR >= 0.95 with cluster-based effective K   FAIL                                     dsr_k=0.7834386937280107
G12   beats a placebo / random-timing benchmark (one-sided p <= 0.05)   FAIL                                             placebo_p=0.4308
```

## Out-of-sample
```
{
 "trades": 86,
 "flag_few_trades": true,
 "net_pnl": 26312.14,
 "win_rate": 0.6744,
 "avg_trade": 305.9551,
 "median_trade": 670.49,
 "avg_ticks": 24.8372,
 "fees": 387.86,
 "profit_factor": 1.3296,
 "t_stat": 0.8318
}
```
Net by scenario: {'base': 26312.1, 'fees1.5': 26118.2, 'stress': 23968.2, 'plus1tick': 24162.1}

### By year (OOS)
```
      oos_net  oos_trades
2013   1436.5           3
2014   5749.0           3
2015   6207.0           4
2016   4613.9           8
2017   2862.9          11
2018  -1379.1          12
2019   8508.4          12
2020  -6387.1          11
2021  -4861.1           8
2022 -11230.5           4
2023  18907.0           4
2024  -1705.5           4
2025   3591.0           2
```

## Variant chosen per fold
```
 fold                   test         variant  train_net_p5
    0 2013-06-04..2014-05-30 monthsquarterly       -1777.2
    1 2014-06-03..2015-05-29 monthsquarterly       -2294.5
    2 2015-06-02..2016-05-31 monthsquarterly        3356.8
    3 2016-06-02..2017-05-31       monthsall        7753.8
    4 2017-06-02..2018-05-31       monthsall        6662.0
    5 2018-06-04..2019-05-31       monthsall       10843.1
    6 2019-06-04..2020-05-29       monthsall       -7255.5
    7 2020-06-02..2021-05-31       monthsall      -39466.9
    8 2021-06-02..2022-05-31 monthsquarterly      -38702.7
    9 2022-06-02..2023-05-31 monthsquarterly      -28175.2
   10 2023-06-02..2024-05-31 monthsquarterly      -37130.5
   11 2024-06-04..2025-05-30 monthsquarterly      -24409.8
   12 2025-06-03..2025-09-30 monthsquarterly      -35901.1
```

## Family: PBO = 0.882, K = 1

```
                     net  trades  avg_ticks
monthsall        27175.7     180     12.439
monthsquarterly  20966.9      60     28.317
```

