---
type: result
date: 2026-10-03
tags: [phase-5, H-003, gates]
---
# H-003 evaluation (D-023): gate verdict **not promising**

Last-hour intraday momentum on 15 years of hourly bars. 3813 trading dates 2010-06-08..2025-09-30; 13 folds (3 y train / 1 y test). DSR N = 92. Costs: 1 tick adverse per side + fees (stress 2 ticks + fees x1.5).

## Gates
```
                                                          requirement result                                                   evidence
gate                                                                                                                                   
G1                                                  >= 200 OOS trades   PASS                                            oos_trades=2095
G2                                OOS net > 0 at 1.5x fees and 250 ms   FAIL                          oos_net_stress=-49922.67499999999
G3                      DSR >= 0.95 (raw N) and OOS mean-trade t >= 2   FAIL    dsr_raw=0.0019897044218712967, oos_t=0.2140322965838904
G4                                                        PBO <= 0.10   PASS                                   pbo=0.031313131313131314
G5                                                 +-20% plateau test   FAIL                                         plateau_pass=False
G6                                 not concentrated (red flags clear)   FAIL                                          concentrated=True
G7                       positive in >= 60% of OOS years (>= 2 years)   FAIL       years_positive_share=0.46153846153846156, n_years=13
G8                           tier-B fill check does not flip the sign   FAIL                                     tier_b_same_sign=False
G9                 MC 5th pct net > 0 and P(loss) <= 10% at 1.5x fees   FAIL              mc_net_p5=-15847.47592913866, mc_p_loss=0.345
G10   cluster medoid; >= 70% of its cluster profitable; not an island   FAIL  is_medoid=True, cluster_share_profitable=0.0, island=True
G11                        DSR >= 0.95 with cluster-based effective K   FAIL                                   dsr_k=0.3194409736909241
```

## Out-of-sample
```
{
 "trades": 2095,
 "flag_few_trades": false,
 "net_pnl": 7176.55,
 "win_rate": 0.4754,
 "avg_trade": 3.4256,
 "median_trade": -17.01,
 "avg_ticks": 0.6348,
 "fees": 9448.45,
 "profit_factor": 1.0157,
 "t_stat": 0.214
}
```
Net by scenario: {'base': 7176.5, 'fees1.5': 2452.3, 'stress': -49922.7, 'plus1tick': -45198.5}

### By year (OOS)
```
      oos_net  oos_trades
2013   1279.8          71
2014   1473.1         139
2015   1656.2         176
2016  -9389.6         164
2017  -4115.6         106
2018  -1950.1         158
2019  -3733.1         157
2020  14473.0         200
2021 -10044.5         154
2022  16985.9         211
2023  12154.8         168
2024 -10908.6         207
2025   -704.8         184
```

## Variant chosen per fold
```
 fold                   test                   variant  train_net_p5
    0 2013-06-04..2014-05-30 signalopen30_min_abs_bp25      -21738.1
    1 2014-06-03..2015-05-29    signalday_min_abs_bp25      -15272.3
    2 2015-06-02..2016-05-31    signalday_min_abs_bp25       -6052.2
    3 2016-06-02..2017-05-31    signalday_min_abs_bp25       -8014.7
    4 2017-06-02..2018-05-31    signalday_min_abs_bp25      -18077.3
    5 2018-06-04..2019-05-31 signalopen30_min_abs_bp25      -24189.4
    6 2019-06-04..2020-05-29    signalday_min_abs_bp25      -31682.8
    7 2020-06-02..2021-05-28    signalday_min_abs_bp25      -15697.5
    8 2021-06-02..2022-05-31    signalday_min_abs_bp25      -35066.7
    9 2022-06-02..2023-05-31    signalday_min_abs_bp25      -27003.9
   10 2023-06-02..2024-05-31    signalday_min_abs_bp25      -31807.0
   11 2024-06-04..2025-05-30     signalday_min_abs_bp0      -19308.5
   12 2025-06-03..2025-09-30     signalday_min_abs_bp0      -22108.4
```

## Family: PBO = 0.031, K = 2

```
                                net  trades  avg_ticks
signalopen30_min_abs_bp0  -109468.7    3768     -1.963
signalday_min_abs_bp0      -34581.8    3782     -0.371
signalopen30_min_abs_bp25  -89058.7    2222     -2.846
signalday_min_abs_bp25      -8950.4    2586      0.084
```


## Interpretation (added by hand, session 6; generated sections above unchanged)
- **Not promising.** 2,095 OOS trades over 13 walk-forward years (2013–2025): +$7,177 net with
  pessimistic costs (≈ 2.36 ticks per round trip), +0.63 ticks/trade, **t = 0.21**. Positive in
  only 6 of 13 years; harsh stress −$49.9k; DSR 0.002 (N = 92). PBO 0.03 means the variant choice
  is not overfit — there is simply no reliable signal after costs in 2013–2025.
- The published effect (Gao et al. 2018 sample to 2013; Baltussen et al. 2021) is not robust in
  ES at the cash close in the post-2013 period, consistent with post-publication decay.
- **Observation, not evidence:** the positive years (2020, 2022, 2023) were high-volatility
  years, which fits the gamma-hedging mechanism. It was noticed AFTER seeing yearly results on
  this data, so any "trade only in high volatility" variant tested on 2010–2025 is contaminated
  (data snooping). It could only be judged fairly on the frozen holdout (from 2025-10-03, user
  unlock) or on future data, pre-registered first.
