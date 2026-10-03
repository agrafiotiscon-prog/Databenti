---
type: result
date: 2026-10-03
tags: [phase-5, H-015, gates]
---
# H-015 evaluation (D-023/D-026): gate verdict **insufficient data**

Macro-announcement-day premium (jobs report and CPI days). 3943 dates 2010-06-07..2025-09-30; 13 folds (3 y / 1 y). DSR N = 154. Costs: 1 tick adverse per side + fees (stress 2 ticks + fees x1.5).

## Gates
```
                                                          requirement result                                                    evidence
gate                                                                                                                                    
G1                                                  >= 200 OOS trades   FAIL                                              oos_trades=165
G2                                OOS net > 0 at 1.5x fees and 250 ms   FAIL                                   oos_net_stress=-10553.725
G3                      DSR >= 0.95 (raw N) and OOS mean-trade t >= 2   FAIL     dsr_raw=0.18418207647950868, oos_t=-0.28457566142217167
G4                                                        PBO <= 0.10   FAIL                                      pbo=0.8912975912975913
G5                                                 +-20% plateau test   FAIL                                          plateau_pass=False
G6                                 not concentrated (red flags clear)   FAIL                                           concentrated=True
G7                       positive in >= 60% of OOS years (>= 2 years)   FAIL         years_positive_share=0.5384615384615384, n_years=13
G8                           tier-B fill check does not flip the sign   FAIL                                      tier_b_same_sign=False
G9                 MC 5th pct net > 0 and P(loss) <= 10% at 1.5x fees   FAIL              mc_net_p5=-16537.212834561215, mc_p_loss=0.809
G10   cluster medoid; >= 70% of its cluster profitable; not an island   FAIL  is_medoid=False, cluster_share_profitable=0.5, island=True
G11                        DSR >= 0.95 with cluster-based effective K   FAIL                                   dsr_k=0.33505237403731863
G12   beats a placebo / random-timing benchmark (one-sided p <= 0.05)   FAIL                                            placebo_p=0.5259
```

## Out-of-sample
```
{
 "trades": 165,
 "flag_few_trades": true,
 "net_pnl": -6056.65,
 "win_rate": 0.5455,
 "avg_trade": -36.707,
 "median_trade": 107.99,
 "avg_ticks": -2.5758,
 "fees": 744.15,
 "profit_factor": 0.9354,
 "t_stat": -0.2846
}
```
Net by scenario: {'base': -6056.7, 'fees1.5': -6428.7, 'stress': -10553.7, 'plus1tick': -10181.7}

### By year (OOS)
```
      oos_net  oos_trades
2013   2068.4           7
2014    187.9          11
2015   3068.8          18
2016  -3014.2          17
2017    925.4          11
2018  -1566.6          12
2019  11231.3          18
2020 -13022.2          16
2021   5637.9          11
2022  -5304.1          12
2023   6850.4          11
2024   -379.1          12
2025 -12740.6           9
```

## Variant chosen per fold
```
 fold                   test                         variant  train_net_p5
    0 2013-06-04..2014-05-30 eventsempsit_windowpost_release       -7766.9
    1 2014-06-03..2015-05-29          eventsempsit_windowc2c       -7707.3
    2 2015-06-02..2016-05-31            eventsboth_windowc2c       -3111.1
    3 2016-06-02..2017-05-31    eventscpi_windowpost_release       -3033.4
    4 2017-06-02..2018-05-31    eventscpi_windowpost_release        -158.8
    5 2018-06-04..2019-05-31    eventscpi_windowpost_release         791.5
    6 2019-06-04..2020-05-29            eventsboth_windowc2c       -3504.9
    7 2020-06-02..2021-05-31 eventsempsit_windowpost_release       -6992.7
    8 2021-06-02..2022-05-31          eventsempsit_windowc2c        -171.3
    9 2022-06-02..2023-05-31 eventsempsit_windowpost_release       -2160.1
   10 2023-06-02..2024-05-31 eventsempsit_windowpost_release      -11142.2
   11 2024-06-04..2025-05-30 eventsempsit_windowpost_release      -11288.7
   12 2025-06-03..2025-09-30    eventscpi_windowpost_release      -16130.6
```

## Family: PBO = 0.891, K = 2

```
                                     net  trades  avg_ticks
eventsboth_windowc2c             10173.9     355      2.654
eventsboth_windowpost_release    -7444.1     359     -1.298
eventsempsit_windowc2c            3644.8     173      2.046
eventsempsit_windowpost_release  -3035.8     177     -1.011
eventscpi_windowc2c               6529.2     182      3.231
eventscpi_windowpost_release     -4408.3     182     -1.577
```


## Interpretation (added by hand, session 6)
Not promising: OOS t = -0.28; jobs/CPI days earn no more than random days (placebo p = 0.53). See [leaderboard](leaderboard.md).
