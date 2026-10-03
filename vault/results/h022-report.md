---
type: result
date: 2026-10-03
tags: [R7, H-022, gates, portfolio]
---
# H-022 diversified futures portfolio: gate verdict **not promising**

Diversified futures portfolio - time-series trend and carry across 26 CME markets, 15% vol target. 26 markets, 3980 dates 2010-06-07..2025-09-30; 13 folds (3 y / 1 y). DSR N = 174. Capital $1M, integer contracts, 15% vol target, next-day-close execution, 1 tick + fees per contract side (stress 2 ticks + fees x1.5). Coverage: [futures-daily-check](futures-daily-check.md).

## User target (D-048): Sharpe >= 1.0 net (~15%/yr at 15% vol)
OOS (walk-forward) at $1M: {'ann_return_pct': np.float64(-4.33), 'ann_vol_pct': np.float64(15.32), 'sharpe': -0.283, 'max_dd_pct': -70.51, 't_daily': -1.006}
OOS at $100k (integer contracts, same choices; realism check): {'ann_return_pct': np.float64(-2.04), 'ann_vol_pct': np.float64(5.81), 'sharpe': -0.351, 'max_dd_pct': -30.47, 't_daily': -1.25}

## Gates
```
                                                          requirement result                                                    evidence
gate                                                                                                                                    
G1                                                  >= 200 OOS trades   PASS                                             oos_trades=9690
G2                                OOS net > 0 at 1.5x fees and 250 ms   FAIL                            oos_net_stress=-847438.699999999
G3                      DSR >= 0.95 (raw N) and OOS mean-trade t >= 2   FAIL                 dsr_raw=0.0003019377715285376, oos_t=-1.006
G4                                                        PBO <= 0.10   FAIL                                      pbo=0.2174048174048174
G5                                                 +-20% plateau test   FAIL                                          plateau_pass=False
G6                                 not concentrated (red flags clear)   FAIL                                           concentrated=True
G7                       positive in >= 60% of OOS years (>= 2 years)   FAIL         years_positive_share=0.3076923076923077, n_years=13
G8                           tier-B fill check does not flip the sign   FAIL                                      tier_b_same_sign=False
G9                 MC 5th pct net > 0 and P(loss) <= 10% at 1.5x fees   FAIL               mc_net_p5=-1465125.011749997, mc_p_loss=0.878
G10   cluster medoid; >= 70% of its cluster profitable; not an island   PASS  is_medoid=True, cluster_share_profitable=1.0, island=False
G11                        DSR >= 0.95 with cluster-based effective K   FAIL                                   dsr_k=0.03626181242751153
G12   beats a placebo / random-timing benchmark (one-sided p <= 0.05)   FAIL                                              placebo_p=0.96
```

Placebo: real OOS net -548,434 vs shifted-signal median 443,926 (95th pct 1,407,690); p = 0.960

Net by scenario (OOS): {'base': -548434, 'fees1.5': -582428, 'stress': -847439, 'plus1tick': -813445}; OOS contract trades 9690

### By year (OOS)
```
       oos_net  return_pct
2013   10281.0        1.03
2014   90555.0        9.06
2015  -29467.0       -2.95
2016 -238852.0      -23.89
2017  -14019.0       -1.40
2018  -38936.0       -3.89
2019 -250271.0      -25.03
2020  189600.0       18.96
2021  -24449.0       -2.44
2022  208885.0       20.89
2023 -220721.0      -22.07
2024 -100373.0      -10.04
2025 -130666.0      -13.07
```

### By sector (OOS net, $)
```
                net
sector             
fx        -255421.0
livestock -163092.0
rates     -162708.0
energy     -90933.0
grains     -72134.0
equity      62521.0
metals     133334.0
```

### By market (OOS net, $)
```
           net
root          
6C   -127867.0
6S   -103431.0
RB    -99818.0
LE    -87594.0
6B    -86974.0
HE    -75498.0
ZC    -67004.0
RTY   -65102.0
ZS    -58815.0
ZN    -46498.0
ZB    -41357.0
ZT    -38065.0
ZF    -36789.0
CL    -18231.0
NG     -3384.0
6A      9911.0
6J     17263.0
HO     30500.0
NQ     33436.0
6E     35676.0
YM     39865.0
SI     40210.0
GC     41502.0
HG     51621.0
ZW     53684.0
ES     54322.0
```

## Variant chosen per fold
```
 fold                   test  variant  train_net_p5
    0 2013-06-04..2014-05-30    carry        -96761
    1 2014-06-03..2015-05-29    carry          4645
    2 2015-06-02..2016-05-31 trend252         44656
    3 2016-06-02..2017-05-31 trend252         80229
    4 2017-06-02..2018-05-31    combo       -276797
    5 2018-06-04..2019-05-31 trend126       -496058
    6 2019-06-04..2020-05-29 trend126       -363298
    7 2020-06-02..2021-05-31 trend252       -149159
    8 2021-06-02..2022-05-31 trend252       -151852
    9 2022-06-02..2023-05-31 trend126         20922
   10 2023-06-02..2024-05-31 trend126         33747
   11 2024-06-04..2025-05-30 trend252       -229176
   12 2025-06-03..2025-09-30 trend252       -408486
```

## Family (full period): PBO = 0.217, K = 2
```
          ann_return_pct  ann_vol_pct  sharpe  max_dd_pct  t_daily   net_full
trend126            0.41        15.80   0.026      -83.61    0.102    64237.0
trend252            6.73        16.52   0.407      -51.89    1.619  1062424.0
carry              -3.02        15.58  -0.194     -106.62   -0.771  -477713.0
combo               2.06        15.62   0.132      -56.15    0.523   324750.0
```


## Interpretation (added by hand, session 6)
- **Not promising.** Walk-forward OOS 2013-06..2025-09: **−4.3%/yr at 15.3% vol (Sharpe −0.28)**, max
  drawdown −70% of $1M (summed, not compounded); 4/13 years positive; placebo p 0.96. At $100k with
  integer contracts: −2.0%/yr (only ~6% vol - many markets round to zero contracts at that size).
- **Checked for bugs before believing it:** coverage 98.8-99.97% same-contract returns, all price levels
  match the contract specs ([futures-daily-check](futures-daily-check.md)); carry signs verified on known
  states (CL contango 2015/2020 short, backwardation 2022 long; ZN long 2015 / short with the inverted
  2023 curve; JPY short; ES long 2015 / short 2023). One extra tick per side costs ~2.2%/yr.
- **Full-period variants (in-sample, for context only - not selectable after the fact):** trend252
  Sharpe 0.41 (6.7%/yr, max DD −52%), combo 0.13, trend126 0.03, carry −0.19. Trend252's ~0.4 matches
  public trend indices after 2010 (D-048). Year-by-year selection between variants destroyed value:
  3-year training windows chose carry/trend126 at the wrong times.
- **Implication for the user's 15%/yr target:** the classic diversified trend/carry recipe, run honestly
  with costs and without hindsight, delivered Sharpe ≈ −0.3 (selected) to +0.4 (best variant in
  hindsight) over 2010-2025 - far below Sharpe 1.0.
