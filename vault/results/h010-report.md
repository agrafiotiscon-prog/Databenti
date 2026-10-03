---
type: result
date: 2026-10-03
tags: [phase-5, H-010, gates]
---
# H-010 evaluation (D-023/D-026): gate verdict **not promising**

Daily reversal - fade the previous RTH move the next day. 3943 dates 2010-06-07..2025-09-30; 13 folds (3 y / 1 y). DSR N = 134. Costs: 1 tick adverse per side + fees (stress 2 ticks + fees x1.5).

## Gates
```
                                                          requirement result                                                     evidence
gate                                                                                                                                     
G1                                                  >= 200 OOS trades   PASS                                              oos_trades=1074
G2                                OOS net > 0 at 1.5x fees and 250 ms   PASS                             oos_net_stress=53684.39000000001
G3                      DSR >= 0.95 (raw N) and OOS mean-trade t >= 2   FAIL         dsr_raw=0.4710560558905329, oos_t=1.3802653138956684
G4                                                        PBO <= 0.10   FAIL                                      pbo=0.20621600621600622
G5                                                 +-20% plateau test   PASS                                            plateau_pass=True
G6                                 not concentrated (red flags clear)   FAIL                                            concentrated=True
G7                       positive in >= 60% of OOS years (>= 2 years)   FAIL          years_positive_share=0.5384615384615384, n_years=13
G8                           tier-B fill check does not flip the sign   PASS                                        tier_b_same_sign=True
G9                 MC 5th pct net > 0 and P(loss) <= 10% at 1.5x fees   PASS                 mc_net_p5=35774.65840963535, mc_p_loss=0.001
G10   cluster medoid; >= 70% of its cluster profitable; not an island   FAIL  is_medoid=False, cluster_share_profitable=1.0, island=False
G11                        DSR >= 0.95 with cluster-based effective K   FAIL                                     dsr_k=0.8508757771553366
```

## Out-of-sample
```
{
 "trades": 1074,
 "flag_few_trades": false,
 "net_pnl": 82956.26,
 "win_rate": 0.4935,
 "avg_trade": 77.2405,
 "median_trade": -17.01,
 "avg_ticks": 6.54,
 "fees": 4843.74,
 "profit_factor": 1.1425,
 "t_stat": 1.3803
}
```
Net by scenario: {'base': 82956.3, 'fees1.5': 80534.4, 'stress': 53684.4, 'plus1tick': 56106.3}

### By year (OOS)
```
      oos_net  oos_trades
2013   2109.2          34
2014    336.4          64
2015  -2649.3          83
2016  -1302.8          81
2017    580.3          21
2018 -26111.4          94
2019  -9415.1          56
2020  75371.3         120
2021   9695.8          73
2022  28599.9         158
2023 -21334.0          99
2024  -5892.1          62
2025  32968.2         129
```

## Variant chosen per fold
```
 fold                   test                    variant  train_net_p5
    0 2013-06-04..2014-05-30 min_abs_bp50_entry_at09:00       -7874.5
    1 2014-06-03..2015-05-29 min_abs_bp50_entry_at09:00       -4918.7
    2 2015-06-02..2016-05-31 min_abs_bp50_entry_at09:00       -4117.6
    3 2016-06-02..2017-05-31 min_abs_bp50_entry_at09:00      -13737.1
    4 2017-06-02..2018-05-31 min_abs_bp50_entry_at10:00      -17918.3
    5 2018-06-04..2019-05-31 min_abs_bp50_entry_at10:00      -37064.2
    6 2019-06-04..2020-05-29 min_abs_bp50_entry_at09:00      -50786.6
    7 2020-06-02..2021-05-31 min_abs_bp50_entry_at09:00      -28802.6
    8 2021-06-02..2022-05-31 min_abs_bp50_entry_at09:00       17541.0
    9 2022-06-02..2023-05-31 min_abs_bp50_entry_at09:00       28289.7
   10 2023-06-02..2024-05-31 min_abs_bp50_entry_at09:00       -2274.2
   11 2024-06-04..2025-05-30 min_abs_bp50_entry_at09:00      -44665.8
   12 2025-06-03..2025-09-30  min_abs_bp0_entry_at10:00        5415.3
```

## Family: PBO = 0.206, K = 2

```
                                 net  trades  avg_ticks
min_abs_bp0_entry_at09:00    61679.7    3627      1.721
min_abs_bp50_entry_at09:00  118229.0    1299      7.642
min_abs_bp0_entry_at10:00    43979.7    3627      1.331
min_abs_bp50_entry_at10:00   82491.5    1299      5.441
```


## Interpretation (added by hand, session 6)
Not promoted; see [leaderboard](leaderboard.md).
