---
type: result
date: 2026-10-04
tags: [R7, H-026, gates, portfolio]
---
# H-026 futures portfolio: gate verdict **not promising**

Commodity basis-momentum - trade the 12 commodity futures by the momentum of front minus second-contract returns. 26 markets, 3980 dates 2010-06-07..2025-09-30; 13 folds (3 y / 1 y). DSR N = 187. Capital $1M, integer contracts, 15% vol target, next-day-close execution, 1 tick + fees per contract side (stress 2 ticks + fees x1.5). Coverage: [futures-daily-check](futures-daily-check.md).

## User target (D-048): Sharpe >= 1.0 net (~15%/yr at 15% vol)
OOS (walk-forward) at $1M: {'ann_return_pct': np.float64(3.14), 'ann_vol_pct': np.float64(15.77), 'sharpe': 0.199, 'max_dd_pct': -50.1, 't_daily': 0.708}
OOS at $100k (integer contracts, same choices; realism check): {'ann_return_pct': np.float64(4.91), 'ann_vol_pct': np.float64(12.85), 'sharpe': 0.382, 'max_dd_pct': -26.69, 't_daily': 1.359}

## Gates
```
                                                          requirement result                                                     evidence
gate                                                                                                                                     
G1                                                  >= 200 OOS trades   PASS                                              oos_trades=6425
G2                                OOS net > 0 at 1.5x fees and 250 ms   PASS                             oos_net_stress=66935.12249999889
G3                      DSR >= 0.95 (raw N) and OOS mean-trade t >= 2   FAIL                       dsr_raw=0.362068543881893, oos_t=0.708
G4                                                        PBO <= 0.10   FAIL                                       pbo=0.5341880341880342
G5                                                 +-20% plateau test   FAIL                                           plateau_pass=False
G6                                 not concentrated (red flags clear)   FAIL                                            concentrated=True
G7                       positive in >= 60% of OOS years (>= 2 years)   PASS          years_positive_share=0.6153846153846154, n_years=13
G8                           tier-B fill check does not flip the sign   PASS                                        tier_b_same_sign=True
G9                 MC 5th pct net > 0 and P(loss) <= 10% at 1.5x fees   FAIL               mc_net_p5=-560957.8705000007, mc_p_loss=0.2555
G10   cluster medoid; >= 70% of its cluster profitable; not an island   FAIL  is_medoid=False, cluster_share_profitable=1.0, island=False
G11                        DSR >= 0.95 with cluster-based effective K   FAIL                                     dsr_k=0.7432342803819831
G12   beats a placebo / random-timing benchmark (one-sided p <= 0.05)   FAIL                                placebo_p=0.13333333333333333
```

Placebo: real OOS net 397,642 vs shifted-signal median -168,500 (95th pct 618,649); p = 0.133

Net by scenario (OOS): {'base': 397642, 'fees1.5': 368499, 'stress': 66935, 'plus1tick': 96078}; OOS contract trades 6425

### By year (OOS)
```
       oos_net  return_pct
2013   75606.0        7.56
2014 -134182.0      -13.42
2015 -227216.0      -22.72
2016  248277.0       24.83
2017  192838.0       19.28
2018 -198640.0      -19.86
2019   28588.0        2.86
2020  305754.0       30.58
2021  118149.0       11.81
2022  -68863.0       -6.89
2023    6610.0        0.66
2024  100972.0       10.10
2025  -50252.0       -5.03
```

### By sector (OOS net, $)
```
                net
sector             
energy    -394771.0
equity          0.0
fx              0.0
rates           0.0
metals     223610.0
grains     258282.0
livestock  310520.0
```

### By market (OOS net, $)
```
           net
root          
CL   -265509.0
RB   -184963.0
SI    -27013.0
HO     -9865.0
6E         0.0
6J         0.0
6C         0.0
6A         0.0
ES         0.0
6S         0.0
NQ         0.0
ZF         0.0
ZB         0.0
YM         0.0
RTY        0.0
6B         0.0
ZT         0.0
ZN         0.0
ZC      6182.0
NG     65565.0
GC     93065.0
LE     96820.0
ZS    125101.0
ZW    127000.0
HG    157557.0
HE    213700.0
```

## Variant chosen per fold
```
 fold                   test variant  train_net_p5
    0 2013-06-04..2014-05-30 tsbm126       -242506
    1 2014-06-03..2015-05-29 tsbm126       -143624
    2 2015-06-02..2016-05-31 xsbm126       -466621
    3 2016-06-02..2017-05-31 xsbm126       -474955
    4 2017-06-02..2018-05-31 xsbm126       -229363
    5 2018-06-04..2019-05-31 xsbm126       -189576
    6 2019-06-04..2020-05-29 tsbm252       -171538
    7 2020-06-02..2021-05-31 tsbm252        -99227
    8 2021-06-02..2022-05-31 tsbm252        499655
    9 2022-06-02..2023-05-31 tsbm126         40672
   10 2023-06-02..2024-05-31 tsbm126        356899
   11 2024-06-04..2025-05-30 tsbm126       -229429
   12 2025-06-03..2025-09-30 tsbm252         73577
```

## Family (full period): PBO = 0.534, K = 2
```
         ann_return_pct  ann_vol_pct  sharpe  max_dd_pct  t_daily  net_full
tsbm126            2.69        15.55   0.173      -65.89    0.687  424935.0
tsbm252            5.63        15.59   0.361      -70.80    1.435  889251.0
xsbm126            4.66        15.21   0.306      -50.14    1.216  735332.0
xsbm252            1.97        15.12   0.131      -65.63    0.519  311886.0
```


## Reading (2026-10-04)
Not promising, but the best of R8: 4/12 gates (G1, G2, G7, G8). OOS +3.1%/yr on $1M (Sharpe 0.20, max DD −50%),
8/13 years positive, positive at stress costs, **all four variants profitable over the full period** (cluster
share 1.0). Fails significance (OOS daily t 0.71, DSR 0.36), PBO 0.53 (the fold choice flips between variants),
MC P(loss) 0.26, and **G12 placebo p = 0.13** - shifted signals do almost as well, so timing is not proven.
By sector: livestock +$311k, grains +$258k, metals +$224k, energy −$395k. Coverage: near/far returns known on
90-97% of commodity days; CL's negative-price days in April 2020 give NaN (log of a negative return) and are skipped.
No lookahead found: near/far ordering uses the contract calendar only; the instruments are those of day t-1.
Not re-tested without energy (post-hoc). A weak, possibly real premium; it would need independent (forward or
longer pre-2010) data to say more.
