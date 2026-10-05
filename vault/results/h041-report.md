---
type: result
date: 2026-10-05
tags: [R12, H-041, trend, confirmation]
---
# H-041 trend252 on 12 never-used markets: **DOES NOT CONFIRM**

Pre-registered (research/hypotheses/H-041.yaml, committed before the data was downloaded): CONFIRMS only if stress net > 0, Sharpe >= 0.25 and circular-shift placebo p <= 0.05. Rule unchanged; $1M; P&L from 2011-06.

## Coverage and quoted units (before P&L)
```
market      first       last  days  returns_ok  median_close  notional_per_contract  max_abs_ret
    TN 2016-01-11 2025-09-30  2526      0.9996     132.51562                 132516        0.026
    UB 2010-06-07 2025-09-30  3972      0.9997     157.75000                 157750        0.069
    6N 2010-06-07 2025-09-30  3968      0.9995       0.69395                  69395        0.041
    6M 2010-06-07 2025-09-30  3966      0.9995       0.05410                  27050        0.080
    KE 2013-12-16 2025-09-30  2965      0.9997     545.25000                  27262        0.076
    ZL 2010-06-07 2025-09-30  3861      0.9972      41.93000                  25158        0.089
    ZM 2010-06-07 2025-09-30  3861      0.9969     342.00000                  34200        0.079
    GF 2010-06-07 2025-09-30  3853      0.9969     153.15000                  76575        0.059
    PL 2010-06-07 2025-09-30  3972      0.9995    1006.80000                  50340        0.127
    PA 2010-06-07 2025-09-30  3972      0.9997     930.00000                  93000        0.205
   EMD 2010-06-07 2025-09-30  3965      0.9997    1779.30000                 177930        0.117
   NKD 2010-06-07 2025-09-30  3968      0.9844   20670.00000                 103350        0.102
```

## Result
```
verdict: DOES NOT CONFIRM
stress_net_pos: True
sharpe_ge_0.25: False
placebo_p_le_0.05: False
ann_return_pct: 2.98
ann_vol_pct: 15.8
sharpe: 0.189
max_dd_pct: -49.1
net: 440895
net_stress: 183536
placebo_p: 0.2667
placebo_median: 9035
years_positive: 10/15
corr_with_orig26: 0.613
```

## By year (% of $1M)
```
      return_pct
2011      -22.18
2012       -7.82
2013       24.11
2014       18.86
2015       20.59
2016      -17.06
2017        9.32
2018      -25.38
2019       15.19
2020       16.47
2021       -7.69
2022       14.13
2023        1.47
2024        0.42
2025        3.67
```

## By market (net $)
```
           net
root          
ZM   -217535.0
PL    -60876.0
EMD   -52383.0
TN    -37780.0
UB     25907.0
6M     37895.0
6N     59506.0
KE     85966.0
GF    103344.0
ZL    109338.0
PA    151913.0
NKD   235599.0
```

## Descriptive: 26 original + 12 new markets as two equal-capital trend books (simple sum, not re-optimised)
Sum of both books: {'ann_return_pct': np.float64(7.68), 'ann_vol_pct': np.float64(28.34), 'sharpe': np.float64(0.271), 'max_dd_pct': np.float64(-79.9), 'net': 1134611}; correlation of daily P&L 0.613.


## Reading (2026-10-05)
Does not confirm by the pre-registered rule (Sharpe 0.19 < 0.25, placebo p 0.27), but the direction is right: +3.0%/yr at
15.8% vol, positive at stress costs, 10/15 years, 8/12 markets positive (NKD, PA, ZL, GF, KE strong; ZM −$218k). So the
trend rule is weakly positive out of sample, much like in the 26 markets (0.41 in hindsight), not a strong premium.
The new book correlates 0.61 with the 26-market trend book: extra markets add mostly the same factor, little
diversification (the simple sum of both books has Sharpe 0.27). Not added; the book keeps the 26-market trend sleeve.
