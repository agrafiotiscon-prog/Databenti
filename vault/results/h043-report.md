---
type: result
date: 2026-10-05
tags: [R13, H-043, rates, mid-month]
---
# H-043 mid-month coupon reinvestment (long T-1..T+1 around the 15th): **DOES NOT CONFIRM**

Pre-registered (research/hypotheses/H-043.yaml, committed before the run): CONFIRMS only if stress net > 0, per-window t >= 2, drift-neutral t >= 2 and placebo p <= 0.05. $250k notional per market, 6 Treasury futures.

## Coverage (before P&L)
```
market      first       last  months  windows  anchor_day_mean
    ZT 2010-06-07 2025-09-30     184      184            15.43
    ZF 2010-06-07 2025-09-30     184      184            15.43
    ZN 2010-06-07 2025-09-30     184      184            15.43
    ZB 2010-06-07 2025-09-30     184      184            15.43
    TN 2016-01-11 2025-09-30     117      117            15.44
    UB 2010-06-07 2025-09-30     184      184            15.43
```

## Result
```
verdict: DOES NOT CONFIRM
stress_net_pos: False
t_window_ge_2: False
t_drift_neutral_ge_2: False
placebo_p_le_0.05: False
windows: 1037
net: -118318
net_stress: -191484
t_window: -1.711
t_drift_neutral: -1.252
placebo_p: 0.077
placebo_median: -206240
years_positive: 5/16
```

## Per market
```
        windows       net  mean_bp  win_rate
market                                      
TN          117 -40024.09    -9.52      0.44
UB          184  -5072.39    -0.26      0.52
ZB          184 -26306.27    -2.63      0.49
ZF          184 -14269.05    -1.63      0.50
ZN          184 -24003.43    -2.20      0.48
ZT          184  -8642.34    -1.30      0.42
```

## By year (pooled $)
```
          net
year         
2010  -7456.0
2011  67950.0
2012 -42063.0
2013  36154.0
2014  23497.0
2015    -83.0
2016 -27474.0
2017  48356.0
2018  -2423.0
2019  18839.0
2020 -32871.0
2021 -30024.0
2022 -82332.0
2023 -70595.0
2024 -14713.0
2025  -3079.0
```

## Reading (2026-10-05)
Does not confirm: no mid-month reinvestment effect. Every market's mean 3-day return around the 15th is slightly negative
(−0.3 to −9.5 bp), pooled t −1.71, drift-neutral t −1.25, 5/16 years positive. The month-end effect (H-030) is specific
to the month-end index rebalance, not a generic coupon-reinvestment flow.
