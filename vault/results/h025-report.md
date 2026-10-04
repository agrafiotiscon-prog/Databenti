---
type: result
date: 2026-10-04
tags: [R7, H-025, gates, portfolio]
---
# H-025 futures portfolio: gate verdict **not promising**

Cross-sectional momentum across 26 CME futures - long recent winners, short recent losers, 15% vol target. 26 markets, 3980 dates 2010-06-07..2025-09-30; 13 folds (3 y / 1 y). DSR N = 183. Capital $1M, integer contracts, 15% vol target, next-day-close execution, 1 tick + fees per contract side (stress 2 ticks + fees x1.5). Coverage: [futures-daily-check](futures-daily-check.md).

## User target (D-048): Sharpe >= 1.0 net (~15%/yr at 15% vol)
OOS (walk-forward) at $1M: {'ann_return_pct': np.float64(-1.33), 'ann_vol_pct': np.float64(14.95), 'sharpe': -0.089, 'max_dd_pct': -48.82, 't_daily': -0.316}
OOS at $100k (integer contracts, same choices; realism check): {'ann_return_pct': np.float64(-1.5), 'ann_vol_pct': np.float64(8.38), 'sharpe': -0.179, 'max_dd_pct': -29.27, 't_daily': -0.637}

## Gates
```
                                                          requirement result                                                    evidence
gate                                                                                                                                    
G1                                                  >= 200 OOS trades   PASS                                            oos_trades=10193
G2                                OOS net > 0 at 1.5x fees and 250 ms   FAIL                           oos_net_stress=-504331.4350000008
G3                      DSR >= 0.95 (raw N) and OOS mean-trade t >= 2   FAIL                  dsr_raw=0.005735615398182237, oos_t=-0.316
G4                                                        PBO <= 0.10   FAIL                                      pbo=0.4478632478632479
G5                                                 +-20% plateau test   FAIL                                          plateau_pass=False
G6                                 not concentrated (red flags clear)   FAIL                                           concentrated=True
G7                       positive in >= 60% of OOS years (>= 2 years)   FAIL        years_positive_share=0.46153846153846156, n_years=13
G8                           tier-B fill check does not flip the sign   FAIL                                      tier_b_same_sign=False
G9                 MC 5th pct net > 0 and P(loss) <= 10% at 1.5x fees   FAIL              mc_net_p5=-1046325.0273750012, mc_p_loss=0.669
G10   cluster medoid; >= 70% of its cluster profitable; not an island   FAIL  is_medoid=False, cluster_share_profitable=0.0, island=True
G11                        DSR >= 0.95 with cluster-based effective K   FAIL                                    dsr_k=0.1588779150635723
G12   beats a placebo / random-timing benchmark (one-sided p <= 0.05)   FAIL                                               placebo_p=0.4
```

Placebo: real OOS net -168,116 vs shifted-signal median -262,681 (95th pct 689,099); p = 0.400

Net by scenario (OOS): {'base': -168116, 'fees1.5': -203732, 'stress': -504331, 'plus1tick': -468716}; OOS contract trades 10193

### By year (OOS)
```
       oos_net  return_pct
2013  136549.0       13.65
2014  -77364.0       -7.74
2015  -31415.0       -3.14
2016 -116002.0      -11.60
2017  149844.0       14.98
2018 -134944.0      -13.49
2019 -121783.0      -12.18
2020   15473.0        1.55
2021    7907.0        0.79
2022  168823.0       16.88
2023  -39292.0       -3.93
2024   71988.0        7.20
2025 -197901.0      -19.79
```

### By sector (OOS net, $)
```
                net
sector             
livestock -159166.0
metals    -145937.0
grains    -139566.0
energy    -103925.0
fx          24090.0
rates      118256.0
equity     238130.0
```

### By market (OOS net, $)
```
           net
root          
6S   -124626.0
RB   -106648.0
HG   -106499.0
RTY   -96262.0
ZS    -91696.0
LE    -87607.0
6B    -76289.0
ZC    -72190.0
HE    -71559.0
ZT    -65874.0
SI    -64021.0
YM    -62111.0
6A    -55973.0
6C    -47467.0
NG    -18108.0
CL     -7451.0
ZW     24321.0
GC     24584.0
ZN     24698.0
HO     28282.0
ZF     46239.0
ES    107750.0
ZB    113194.0
6E    140110.0
6J    188336.0
NQ    288754.0
```

## Variant chosen per fold
```
 fold                   test       variant  train_net_p5
    0 2013-06-04..2014-05-30 xsm126_sector       -177883
    1 2014-06-03..2015-05-29 xsm252_sector       -214761
    2 2015-06-02..2016-05-31 xsm252_global        -12102
    3 2016-06-02..2017-05-31 xsm252_global        -35020
    4 2017-06-02..2018-05-31 xsm252_global       -326996
    5 2018-06-04..2019-05-31 xsm252_global       -438215
    6 2019-06-04..2020-05-29 xsm252_global       -488932
    7 2020-06-02..2021-05-31 xsm252_global       -447009
    8 2021-06-02..2022-05-31 xsm126_global       -461741
    9 2022-06-02..2023-05-31 xsm126_global         80812
   10 2023-06-02..2024-05-31 xsm126_global        343905
   11 2024-06-04..2025-05-30 xsm126_global        -97365
   12 2025-06-03..2025-09-30 xsm126_sector       -403892
```

## Family (full period): PBO = 0.448, K = 2
```
               ann_return_pct  ann_vol_pct  sharpe  max_dd_pct  t_daily  net_full
xsm126_sector           -1.95        15.44  -0.126     -107.23   -0.502 -308392.0
xsm252_sector           -4.97        15.29  -0.325     -112.43   -1.291 -784352.0
xsm126_global            3.13        15.89   0.197      -68.32    0.782  493955.0
xsm252_global            0.97        16.00   0.061      -71.68    0.242  153593.0
```


## Reading (2026-10-04)
Not promising. Cross-sectional momentum lost −1.3%/yr OOS (Sharpe −0.09, max DD −49%), 6/13 years positive,
PBO 0.45, placebo p 0.40. Equity (+$238k) and rates (+$118k) were the profitable sectors - as in H-024, the
equity gain most likely comes from the global ranking leaning long equities in a 2013-2025 bull market (equity
drift, cf. G12 findings for H-005/H-009/H-012), not from relative momentum. Commodities lost in all four sectors.
Together with H-024 (carry) this suggests relative-value premia are too thin in a 26-market, 2-6-names-per-sector
universe after costs. Not re-tested on sub-universes (post-hoc).
