---
type: result
date: 2026-10-04
tags: [R7, H-024, gates, portfolio]
---
# H-024 futures portfolio: gate verdict **not promising**

Cross-sectional carry across 26 CME futures - long high-carry, short low-carry markets, 15% vol target. 26 markets, 3980 dates 2010-06-07..2025-09-30; 13 folds (3 y / 1 y). DSR N = 179. Capital $1M, integer contracts, 15% vol target, next-day-close execution, 1 tick + fees per contract side (stress 2 ticks + fees x1.5). Coverage: [futures-daily-check](futures-daily-check.md).

## User target (D-048): Sharpe >= 1.0 net (~15%/yr at 15% vol)
OOS (walk-forward) at $1M: {'ann_return_pct': np.float64(-1.5), 'ann_vol_pct': np.float64(15.32), 'sharpe': -0.098, 'max_dd_pct': -70.76, 't_daily': -0.349}
OOS at $100k (integer contracts, same choices; realism check): {'ann_return_pct': np.float64(-1.73), 'ann_vol_pct': np.float64(12.67), 'sharpe': -0.137, 'max_dd_pct': -71.3, 't_daily': -0.486}

## Gates
```
                                                          requirement result                                                    evidence
gate                                                                                                                                    
G1                                                  >= 200 OOS trades   PASS                                             oos_trades=7118
G2                                OOS net > 0 at 1.5x fees and 250 ms   FAIL                           oos_net_stress=-401226.0575000009
G3                      DSR >= 0.95 (raw N) and OOS mean-trade t >= 2   FAIL                 dsr_raw=7.637768634216613e-08, oos_t=-0.349
G4                                                        PBO <= 0.10   FAIL                                     pbo=0.17707847707847707
G5                                                 +-20% plateau test   FAIL                                          plateau_pass=False
G6                                 not concentrated (red flags clear)   FAIL                                           concentrated=True
G7                       positive in >= 60% of OOS years (>= 2 years)   FAIL        years_positive_share=0.46153846153846156, n_years=13
G8                           tier-B fill check does not flip the sign   FAIL                                      tier_b_same_sign=False
G9                 MC 5th pct net > 0 and P(loss) <= 10% at 1.5x fees   FAIL              mc_net_p5=-1128566.3962500033, mc_p_loss=0.678
G10   cluster medoid; >= 70% of its cluster profitable; not an island   FAIL  is_medoid=False, cluster_share_profitable=0.0, island=True
G11                        DSR >= 0.95 with cluster-based effective K   FAIL                                  dsr_k=0.028329899497299305
G12   beats a placebo / random-timing benchmark (one-sided p <= 0.05)   FAIL                                              placebo_p=0.57
```

Placebo: real OOS net -190,131 vs shifted-signal median -126,319 (95th pct 447,533); p = 0.570

Net by scenario (OOS): {'base': -190131, 'fees1.5': -211988, 'stress': -401226, 'plus1tick': -379368}; OOS contract trades 7118

### By year (OOS)
```
       oos_net  return_pct
2013  -55921.0       -5.59
2014  -41086.0       -4.11
2015  133814.0       13.38
2016  -48339.0       -4.83
2017  212568.0       21.26
2018 -353990.0      -35.40
2019   31425.0        3.14
2020   20756.0        2.08
2021 -119359.0      -11.94
2022   15650.0        1.56
2023  -36028.0       -3.60
2024  -87174.0       -8.72
2025  137553.0       13.76
```

### By sector (OOS net, $)
```
                net
sector             
energy    -322099.0
grains    -210685.0
livestock -118596.0
rates      -11048.0
metals      -9884.0
fx         237772.0
equity     244410.0
```

### By market (OOS net, $)
```
           net
root          
ZS   -264599.0
CL   -178132.0
RB   -163529.0
ZT   -130325.0
NQ   -130258.0
6C   -121745.0
GC   -111258.0
ZF   -105157.0
6A    -81454.0
HE    -71088.0
LE    -47508.0
ZC    -27168.0
HO    -21962.0
6B      3370.0
NG     41524.0
HG     50581.0
SI     50792.0
ZN     55048.0
RTY    67661.0
ZW     81082.0
6E     81485.0
6S     98702.0
ES    108473.0
ZB    169386.0
YM    198534.0
6J    257414.0
```

## Variant chosen per fold
```
 fold                   test           variant  train_net_p5
    0 2013-06-04..2014-05-30 xsc_global_smooth        246087
    1 2014-06-03..2015-05-29 xsc_global_smooth        119046
    2 2015-06-02..2016-05-31 xsc_global_smooth       -226635
    3 2016-06-02..2017-05-31 xsc_global_smooth       -448664
    4 2017-06-02..2018-05-31 xsc_global_smooth       -212280
    5 2018-06-04..2019-05-31 xsc_sector_smooth       -107445
    6 2019-06-04..2020-05-29 xsc_global_smooth       -377693
    7 2020-06-02..2021-05-31 xsc_global_smooth       -427607
    8 2021-06-02..2022-05-31 xsc_global_smooth       -414431
    9 2022-06-02..2023-05-31 xsc_global_smooth       -333290
   10 2023-06-02..2024-05-31 xsc_sector_smooth       -263610
   11 2024-06-04..2025-05-30 xsc_global_smooth       -390648
   12 2025-06-03..2025-09-30 xsc_sector_smooth       -500711
```

## Family (full period): PBO = 0.177, K = 2
```
                   ann_return_pct  ann_vol_pct  sharpe  max_dd_pct  t_daily   net_full
xsc_sector                 -13.57        15.29  -0.887     -252.75   -3.527 -2142636.0
xsc_global                  -1.84        15.27  -0.121      -91.49   -0.480  -291282.0
xsc_sector_smooth           -0.27        15.40  -0.018      -74.43   -0.070   -43047.0
xsc_global_smooth            4.64        15.35   0.302      -35.49    1.201   732622.0
```


## Reading (2026-10-04)
Not promising. Cross-sectional carry lost −1.5%/yr OOS (Sharpe −0.10, max DD −71% at $1M with the 2.5x scale cap),
6/13 years positive, 2018 alone −35%. Equity and FX carry made money (+$244k, +$238k); commodity carry lost
(energy −$322k, grains −$211k, livestock −$119k) - consistent with seasonality and contango shocks dominating
commodity curves post-2010. Placebo p 0.57: the ranking timing adds nothing. Carry was computed with each pair's own
expiry gap (fix made before any P&L, see the registry entry). Not re-tested on sub-universes (that would be
selection after seeing the result).
