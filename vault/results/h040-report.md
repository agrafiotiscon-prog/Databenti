---
type: result
date: 2026-10-05
tags: [R11, H-040, H-037, confirmation]
---
# H-040 confirmation of H-037 on 6N/6M (never used before): **DOES NOT CONFIRM**

Pre-registered (research/hypotheses/H-040.yaml, committed before the data was downloaded): CONFIRMS only if stress net > 0, per-window t >= 2, drift-neutral t >= 2 and placebo p <= 0.05. Rule: over the last 5 days of the month, long the foreign currency after a US equity rise month-to-date, short after a fall; $250k notional per market.

## Coverage (before P&L)
```
market      first       last  days  events  returns_ok  median_close  contracts_at_median
    6N 2010-06-07 2025-09-30  3968     183      0.9997       0.69395                    4
    6M 2010-06-07 2025-09-30  3966     182      0.9997       0.05410                    9
```

## Result
```
verdict: DOES NOT CONFIRM
stress_net_pos: False
t_window_ge_2: False
t_drift_neutral_ge_2: False
placebo_p_le_0.05: False
windows: 365
net: -24534
net_stress: -51887
t_window: -0.362
t_drift_neutral: -0.071
placebo_p: 0.227
placebo_median: -80320
years_positive: 9/16
```

## Per market
```
        windows       net  win_rate  mean_excess_bp
market                                             
6M          182 -67685.26      0.46          -11.49
6N          183  43151.44      0.55           10.37
```

## By year (pooled $)
```
          net
year         
2010  19237.0
2011 -39150.0
2012   4139.0
2013 -15274.0
2014 -24517.0
2015   2804.0
2016  12871.0
2017  10096.0
2018 -10312.0
2019   4932.0
2020 -19664.0
2021   1521.0
2022  20462.0
2023  10986.0
2024  -1852.0
2025   -815.0
```

## Reading (2026-10-05)
Does not confirm: on currency futures never used before the H-037 rule loses (net −$25k, stress −$52k, t −0.36, drift-neutral
t −0.07, placebo p 0.23). NZD went the predicted way, MXN the opposite. H-037's near-pass on the six major currencies was not
a general month-end hedging effect; it is not added to the book or the watch list.
