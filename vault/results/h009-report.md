---
type: result
date: 2026-10-03
tags: [phase-5, H-009, gates]
---
# H-009 evaluation (D-023/D-026): gate verdict **not promising**

Overnight drift - hold ES from the cash close to the next morning. 3943 dates 2010-06-07..2025-09-30; 13 folds (3 y / 1 y). DSR N = 130. Costs: 1 tick adverse per side + fees (stress 2 ticks + fees x1.5).

## Gates
```
                                                          requirement result                                                     evidence
gate                                                                                                                                     
G1                                                  >= 200 OOS trades   PASS                                              oos_trades=2552
G2                                OOS net > 0 at 1.5x fees and 250 ms   FAIL                           oos_net_stress=-1076.7800000000025
G3                      DSR >= 0.95 (raw N) and OOS mean-trade t >= 2   FAIL         dsr_raw=0.6811720015776178, oos_t=1.0457923689481194
G4                                                        PBO <= 0.10   FAIL                                       pbo=0.6326340326340326
G5                                                 +-20% plateau test   PASS                                            plateau_pass=True
G6                                 not concentrated (red flags clear)   FAIL                                            concentrated=True
G7                       positive in >= 60% of OOS years (>= 2 years)   PASS          years_positive_share=0.6923076923076923, n_years=13
G8                           tier-B fill check does not flip the sign   PASS                                        tier_b_same_sign=True
G9                 MC 5th pct net > 0 and P(loss) <= 10% at 1.5x fees   PASS                  mc_net_p5=20305.6395550582, mc_p_loss=0.007
G10   cluster medoid; >= 70% of its cluster profitable; not an island   FAIL  is_medoid=False, cluster_share_profitable=1.0, island=False
G11                        DSR >= 0.95 with cluster-based effective K   FAIL                                     dsr_k=0.8195707651958988
```

## Out-of-sample
```
{
 "trades": 2552,
 "flag_few_trades": false,
 "net_pnl": 68477.98,
 "win_rate": 0.5333,
 "avg_trade": 26.8331,
 "median_trade": 45.49,
 "avg_ticks": 2.5074,
 "fees": 11509.52,
 "profit_factor": 1.0714,
 "t_stat": 1.0458
}
```
Net by scenario: {'base': 68478.0, 'fees1.5': 62723.2, 'stress': -1076.8, 'plus1tick': 4678.0}

### By year (OOS)
```
      oos_net  oos_trades
2013    998.4         114
2014   4538.6         191
2015  -4594.0         201
2016 -10135.0         199
2017   2486.5         197
2018   1045.6         195
2019  21593.2         226
2020  -5105.7         223
2021  22543.5         201
2022  -8605.5         198
2023   3899.0         197
2024  35793.2         226
2025   4020.2         184
```

## Variant chosen per fold
```
 fold                   test                         variant  train_net_p5
    0 2013-06-04..2014-05-30  exit_at08:00_skip_weekendsTrue      -19634.0
    1 2014-06-03..2015-05-29  exit_at09:00_skip_weekendsTrue      -11847.1
    2 2015-06-02..2016-05-31  exit_at09:00_skip_weekendsTrue       -8576.9
    3 2016-06-02..2017-05-31  exit_at09:00_skip_weekendsTrue      -23553.9
    4 2017-06-02..2018-05-31  exit_at08:00_skip_weekendsTrue      -29903.3
    5 2018-06-04..2019-05-31  exit_at08:00_skip_weekendsTrue      -20490.0
    6 2019-06-04..2020-05-29 exit_at09:00_skip_weekendsFalse      -12619.9
    7 2020-06-02..2021-05-31  exit_at08:00_skip_weekendsTrue      -16620.8
    8 2021-06-02..2022-05-31  exit_at09:00_skip_weekendsTrue        4274.7
    9 2022-06-02..2023-05-31  exit_at09:00_skip_weekendsTrue       27744.8
   10 2023-06-02..2024-05-31  exit_at09:00_skip_weekendsTrue       -7789.7
   11 2024-06-04..2025-05-30 exit_at09:00_skip_weekendsFalse      -21966.6
   12 2025-06-03..2025-09-30 exit_at09:00_skip_weekendsFalse      -43574.5
```

## Family: PBO = 0.633, K = 2

```
                                      net  trades  avg_ticks
exit_at08:00_skip_weekendsFalse   69170.4    3812      1.812
exit_at08:00_skip_weekendsTrue    56175.7    3032      1.843
exit_at09:00_skip_weekendsFalse  106456.8    3815      2.593
exit_at09:00_skip_weekendsTrue    87138.2    3032      2.660
```


## Interpretation (added by hand, session 6)
Not promoted; see [leaderboard](leaderboard.md).
