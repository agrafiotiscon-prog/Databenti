---
type: result
date: 2026-10-03
tags: [phase-5, H-016, gates]
---
# H-016 evaluation (D-023/D-026): gate verdict **insufficient data**

Pre-holiday effect (long into the last trading day before an exchange holiday). 3943 dates 2010-06-07..2025-09-30; 13 folds (3 y / 1 y). DSR N = 156. Costs: 1 tick adverse per side + fees (stress 2 ticks + fees x1.5).

## Gates
```
                                                          requirement result                                                   evidence
gate                                                                                                                                   
G1                                                  >= 200 OOS trades   FAIL                                              oos_trades=31
G2                                OOS net > 0 at 1.5x fees and 250 ms   FAIL                                   oos_net_stress=-3209.715
G3                      DSR >= 0.95 (raw N) and OOS mean-trade t >= 2   FAIL     dsr_raw=0.03302288288144284, oos_t=-0.4469243747598812
G4                                                        PBO <= 0.10   FAIL                                    pbo=0.45998445998445997
G5                                                 +-20% plateau test   FAIL                                         plateau_pass=False
G6                                 not concentrated (red flags clear)   FAIL                                          concentrated=True
G7                       positive in >= 60% of OOS years (>= 2 years)   FAIL       years_positive_share=0.46153846153846156, n_years=13
G8                           tier-B fill check does not flip the sign   FAIL                                     tier_b_same_sign=False
G9                 MC 5th pct net > 0 and P(loss) <= 10% at 1.5x fees   FAIL              mc_net_p5=-4859.058051605017, mc_p_loss=0.887
G10   cluster medoid; >= 70% of its cluster profitable; not an island   FAIL  is_medoid=True, cluster_share_profitable=0.5, island=True
G11                        DSR >= 0.95 with cluster-based effective K   FAIL                                  dsr_k=0.32167984511479897
G12   beats a placebo / random-timing benchmark (one-sided p <= 0.05)   FAIL                                           placebo_p=0.5419
```

## Out-of-sample
```
{
 "trades": 31,
 "flag_few_trades": true,
 "net_pnl": -2364.81,
 "win_rate": 0.4516,
 "avg_trade": -76.2842,
 "median_trade": -29.51,
 "avg_ticks": -5.7419,
 "fees": 139.81,
 "profit_factor": 0.7979,
 "t_stat": -0.4469
}
```
Net by scenario: {'base': -2364.8, 'fees1.5': -2434.7, 'stress': -3209.7, 'plus1tick': -3139.8}

### By year (OOS)
```
      oos_net  oos_trades
2013    174.0           3
2014   -652.1           6
2015   -554.5           1
2016    349.0           3
2017  -1376.0           3
2018   1791.0           2
2019    591.0           2
2020   2978.5           2
2021   1408.0           1
2022  -2338.5           3
2023  -1309.0           2
2024  -2234.0           2
2025  -1192.0           1
```

## Variant chosen per fold
```
 fold                   test   variant  train_net_p5
    0 2013-06-04..2014-05-30 windowc2c        -123.4
    1 2014-06-03..2015-05-29 windowrth        -133.5
    2 2015-06-02..2016-05-31 windowrth       -1071.1
    3 2016-06-02..2017-05-31 windowrth       -2514.2
    4 2017-06-02..2018-05-31 windowrth       -3729.5
    5 2018-06-04..2019-05-31 windowrth       -3063.3
    6 2019-06-04..2020-05-29 windowc2c       -2274.9
    7 2020-06-02..2021-05-31 windowc2c         458.3
    8 2021-06-02..2022-05-31 windowc2c        1344.6
    9 2022-06-02..2023-05-31 windowc2c       -4459.8
   10 2023-06-02..2024-05-31 windowrth       -3987.6
   11 2024-06-04..2025-05-30 windowrth       -6329.6
   12 2025-06-03..2025-09-30 windowc2c       -3906.8
```

## Family: PBO = 0.460, K = 1

```
              net  trades  avg_ticks
windowc2c  2419.6      40      5.200
windowrth -1709.9      41     -2.976
```

