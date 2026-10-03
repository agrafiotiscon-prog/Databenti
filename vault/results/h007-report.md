---
type: result
date: 2026-10-03
tags: [phase-5, H-007, gates]
---
# H-007 evaluation (D-023/D-026): gate verdict **insufficient data**

Pre-FOMC announcement drift (long into scheduled FOMC statements). 3943 dates 2010-06-07..2025-09-30; 13 folds (3 y / 1 y). DSR N = 118. Costs: 1 tick adverse per side + fees (stress 2 ticks + fees x1.5).

## Gates
```
                                                          requirement result                                                   evidence
gate                                                                                                                                   
G1                                                  >= 200 OOS trades   FAIL                                              oos_trades=98
G2                                OOS net > 0 at 1.5x fees and 250 ms   PASS                          oos_net_stress=18624.530000000002
G3                      DSR >= 0.95 (raw N) and OOS mean-trade t >= 2   FAIL   dsr_raw=0.00014398243054575266, oos_t=1.9470650624820616
G4                                                        PBO <= 0.10   PASS                                  pbo=0.0021756021756021756
G5                                                 +-20% plateau test   FAIL                                         plateau_pass=False
G6                                 not concentrated (red flags clear)   FAIL                                          concentrated=True
G7                       positive in >= 60% of OOS years (>= 2 years)   PASS        years_positive_share=0.6153846153846154, n_years=13
G8                           tier-B fill check does not flip the sign   PASS                                      tier_b_same_sign=True
G9                 MC 5th pct net > 0 and P(loss) <= 10% at 1.5x fees   PASS                mc_net_p5=11816.488944574266, mc_p_loss=0.0
G10   cluster medoid; >= 70% of its cluster profitable; not an island   FAIL  is_medoid=True, cluster_share_profitable=0.5, island=True
G11                        DSR >= 0.95 with cluster-based effective K   PASS                                   dsr_k=0.9830052838674881
```

## Out-of-sample
```
{
 "trades": 98,
 "flag_few_trades": true,
 "net_pnl": 21295.52,
 "win_rate": 0.5102,
 "avg_trade": 217.3012,
 "median_trade": 32.99,
 "avg_ticks": 17.7449,
 "fees": 441.98,
 "profit_factor": 1.9247,
 "t_stat": 1.9471
}
```
Net by scenario: {'base': 21295.5, 'fees1.5': 21074.5, 'stress': 18624.5, 'plus1tick': 18845.5}

### By year (OOS)
```
      oos_net  oos_trades
2013   -735.0           5
2014   -186.1           8
2015   -536.1           8
2016    738.9           8
2017    226.4           8
2018   2988.9           8
2019   -961.1           8
2020   5555.9           7
2021  -4898.6           8
2022   8276.4           8
2023   3426.4           8
2024   6351.4           8
2025   1047.9           6
```

## Variant chosen per fold
```
 fold                   test       variant  train_net_p5
    0 2013-06-04..2014-05-30 windowmorning       -1819.3
    1 2014-06-03..2015-05-29   windowlm24h       -1772.3
    2 2015-06-02..2016-05-31 windowmorning       -3734.0
    3 2016-06-02..2017-05-31   windowlm24h       -3022.5
    4 2017-06-02..2018-05-31   windowlm24h       -1494.3
    5 2018-06-04..2019-05-31   windowlm24h        1322.2
    6 2019-06-04..2020-05-29   windowlm24h        -566.9
    7 2020-06-02..2021-05-31   windowlm24h        -226.8
    8 2021-06-02..2022-05-31 windowmorning       -2341.3
    9 2022-06-02..2023-05-31   windowlm24h       -2824.7
   10 2023-06-02..2024-05-31   windowlm24h        2668.5
   11 2024-06-04..2025-05-30   windowlm24h        4995.4
   12 2025-06-03..2025-09-30   windowlm24h        5386.8
```

## Family: PBO = 0.002, K = 1

```
                   net  trades  avg_ticks
windowlm24h    32612.3     122     21.746
windowmorning  -2400.2     122     -1.213
```


## Interpretation (added by hand, session 6)
Best candidate so far but NOT promoted (6/11 gates). Details and next steps: [leaderboard](leaderboard.md).
