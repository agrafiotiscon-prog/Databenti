---
type: result
date: 2026-10-03
tags: [phase-5, H-005, gates]
---
# H-005 evaluation (D-023/D-026): gate verdict **insufficient data**

Turn-of-the-month effect in ES (hold over the month boundary). 3943 dates 2010-06-07..2025-09-30; 13 folds (3 y / 1 y). DSR N = 112. Costs: 1 tick adverse per side + fees (stress 2 ticks + fees x1.5).

## Gates
```
                                                          requirement result                                                   evidence
gate                                                                                                                                   
G1                                                  >= 200 OOS trades   FAIL                                             oos_trades=124
G2                                OOS net > 0 at 1.5x fees and 250 ms   FAIL                         oos_net_stress=-238.85999999999694
G3                      DSR >= 0.95 (raw N) and OOS mean-trade t >= 2   FAIL     dsr_raw=0.13882580157580338, oos_t=0.11575691248232343
G4                                                        PBO <= 0.10   FAIL                                     pbo=0.4081585081585082
G5                                                 +-20% plateau test   FAIL                                         plateau_pass=False
G6                                 not concentrated (red flags clear)   FAIL                                          concentrated=True
G7                       positive in >= 60% of OOS years (>= 2 years)   FAIL        years_positive_share=0.5384615384615384, n_years=13
G8                           tier-B fill check does not flip the sign   PASS                                      tier_b_same_sign=True
G9                 MC 5th pct net > 0 and P(loss) <= 10% at 1.5x fees   FAIL              mc_net_p5=-12355.62059993407, mc_p_loss=0.386
G10   cluster medoid; >= 70% of its cluster profitable; not an island   FAIL  is_medoid=True, cluster_share_profitable=0.5, island=True
G11                        DSR >= 0.95 with cluster-based effective K   FAIL                                    dsr_k=0.502446864264069
```

## Out-of-sample
```
{
 "trades": 124,
 "flag_few_trades": true,
 "net_pnl": 3140.76,
 "win_rate": 0.5403,
 "avg_trade": 25.3287,
 "median_trade": 176.74,
 "avg_ticks": 2.3871,
 "fees": 559.24,
 "profit_factor": 1.0317,
 "t_stat": 0.1158
}
```
Net by scenario: {'base': 3140.8, 'fees1.5': 2861.1, 'stress': -238.9, 'plus1tick': 40.8}

### By year (OOS)
```
      oos_net  oos_trades
2013  -1964.6           6
2014   -582.6          10
2015  -2057.6          10
2016    487.9          11
2017   3154.9          10
2018   -532.6          10
2019    284.4           9
2020    662.9          11
2021  11554.9          10
2022   2900.4          11
2023   2829.9          10
2024  -2828.1           9
2025 -10769.1           7
```

## Variant chosen per fold
```
 fold                   test            variant  train_net_p5
    0 2013-06-04..2014-05-30 entry_k2_exit_day3        6451.2
    1 2014-06-03..2015-05-29 entry_k1_exit_day3       -4689.0
    2 2015-06-02..2016-05-31 entry_k1_exit_day1       -6220.4
    3 2016-06-02..2017-05-31 entry_k1_exit_day1       -7442.2
    4 2017-06-02..2018-05-31 entry_k1_exit_day1       -5248.6
    5 2018-06-04..2019-05-31 entry_k1_exit_day1      -10536.3
    6 2019-06-04..2020-05-29 entry_k2_exit_day1        -120.4
    7 2020-06-02..2021-05-31 entry_k1_exit_day1      -18098.9
    8 2021-06-02..2022-05-31 entry_k1_exit_day3       10392.1
    9 2022-06-02..2023-05-31 entry_k1_exit_day3       10170.5
   10 2023-06-02..2024-05-31 entry_k1_exit_day1        5704.2
   11 2024-06-04..2025-05-30 entry_k1_exit_day1         328.8
   12 2025-06-03..2025-09-30 entry_k1_exit_day1      -16033.5
```

## Family: PBO = 0.408, K = 2

```
                        net  trades  avg_ticks
entry_k1_exit_day1  24383.3     170     11.835
entry_k1_exit_day3  33906.9     162     17.105
entry_k2_exit_day1   -198.7     166      0.265
entry_k2_exit_day3  12112.4     158      6.494
```


## Interpretation (added by hand, session 6)
See [leaderboard](leaderboard.md): no reliable edge after costs; closed.
