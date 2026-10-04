---
type: result
date: 2026-10-04
tags: [R9, H-029, gates]
---
# H-029 commodity index roll front-running: gate verdict **not promising**

Front-running the commodity index roll - short near / long next contract around the GSCI roll (5th-9th business day). 3976 dates 2010-06-07..2025-09-30; 13 folds (3 y / 1 y). DSR N = 204. Capital $1,000,000. calendar spread short near / long far, instruments fixed at entry, 4 contract sides x (1 tick + fees).

## Coverage (before P&L, D-042)
```
market  roll_months_in_data  events_used
    CL                  184          183
    HO                  184          183
    RB                  184          183
    NG                  184          183
    GC                   76           76
    SI                   77           76
    HG                   77           76
    ZC                   77           76
    ZW                   77           76
    ZS                   76           75
    LE                   92           92
    HE                  108          107
```

OOS (walk-forward): {'ann_return_pct': -0.72, 'ann_vol_pct': 1.36, 'sharpe': -0.528, 'max_dd_pct': -12.22, 't_daily': -1.878}
OOS contract trades: 1123

## Gates
```
                                                          requirement result                                                   evidence
gate                                                                                                                                   
G1                                                  >= 200 OOS trades   PASS                                            oos_trades=1123
G2                                OOS net > 0 at 1.5x fees and 250 ms   FAIL                         oos_net_stress=-181984.95500000002
G3                      DSR >= 0.95 (raw N) and OOS mean-trade t >= 2   FAIL                dsr_raw=4.135981557240598e-10, oos_t=-1.878
G4                                                        PBO <= 0.10   FAIL                                    pbo=0.18104118104118105
G5                                                 +-20% plateau test   FAIL                                         plateau_pass=False
G6                                 not concentrated (red flags clear)   FAIL                                          concentrated=True
G7                       positive in >= 60% of OOS years (>= 2 years)   FAIL       years_positive_share=0.15384615384615385, n_years=13
G8                           tier-B fill check does not flip the sign   FAIL                                     tier_b_same_sign=False
G9                 MC 5th pct net > 0 and P(loss) <= 10% at 1.5x fees   FAIL              mc_net_p5=-166326.92525000006, mc_p_loss=0.99
G10   cluster medoid; >= 70% of its cluster profitable; not an island   FAIL  is_medoid=True, cluster_share_profitable=0.0, island=True
G11                        DSR >= 0.95 with cluster-based effective K   FAIL                                dsr_k=0.0014065070698716653
G12   beats a placebo / random-timing benchmark (one-sided p <= 0.05)   FAIL                              placebo_p=0.07333333333333333
```

Placebo: real OOS net -90,703 vs placebo median -118,373 (95th pct -87,071); p = 0.073

Net by scenario (OOS): {'base': -90703, 'fees1.5': -99739, 'stress': -181985, 'plus1tick': -172949}

### By year (OOS)
```
      oos_net  return_pct
2013   4701.0        0.47
2014  -9018.0       -0.90
2015  -2382.0       -0.24
2016 -11150.0       -1.11
2017  -9931.0       -0.99
2018 -18026.0       -1.80
2019  -9215.0       -0.92
2020  -3924.0       -0.39
2021    339.0        0.03
2022 -20831.0       -2.08
2023  -7440.0       -0.74
2024  -2960.0       -0.30
2025   -866.0       -0.09
```

## Variant chosen per fold
```
 fold                   test variant  train_net_p5
    0 2013-06-04..2014-05-30     5|5        -34354
    1 2014-06-03..2015-05-29     1|5        -31705
    2 2015-06-02..2016-05-31     1|5        -28593
    3 2016-06-02..2017-05-31     1|5        -27425
    4 2017-06-02..2018-05-31     1|5        -39873
    5 2018-06-04..2019-05-31     1|5        -40521
    6 2019-06-04..2020-05-29     1|5        -53859
    7 2020-06-02..2021-05-31     1|9        -44804
    8 2021-06-02..2022-05-31     1|9        -22486
    9 2022-06-02..2023-05-31     5|9         -3392
   10 2023-06-02..2024-05-31     5|5        -38717
   11 2024-06-04..2025-05-30     5|5        -58595
   12 2025-06-03..2025-09-30     1|5        -67908
```

## Family (full period): PBO = 0.181, K = 2
```
     ann_return_pct  ann_vol_pct  sharpe  max_dd_pct  t_daily  net_full  trades
1|5           -0.75         0.59  -1.274      -11.94   -5.060 -117784.0  1396.0
1|9           -0.95         1.40  -0.679      -15.90   -2.695 -150241.0  1396.0
5|5           -0.37         1.78  -0.208      -14.40   -0.825  -58201.0  1386.0
5|9           -0.64         2.41  -0.267      -17.95   -1.062 -101729.0  1386.0
```


## Reading (2026-10-04)
Not promising (1/12). Front-running the GSCI roll with a near/far calendar spread lost in 11/13 OOS years and in
all 4 variants full-period (t −0.8 to −5.1). Consistent with Bessembinder et al. (2016): the roll's price impact
is now small and temporary, and four contract sides of costs per trade overwhelm it. Placebo p 0.07 only says the
roll window loses slightly less than random windows.
