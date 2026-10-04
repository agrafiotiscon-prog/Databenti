---
type: result
date: 2026-10-04
tags: [R9, H-033, month-end, confirmation]
---
# H-033 month-end test on TN/UB (short 3 days after month-end): **DOES NOT CONFIRM**

Pre-registered (research/hypotheses/H-033.yaml, committed before the run): CONFIRMS only if stress net > 0, per-window t >= 2, drift-neutral t >= 2 and random-window placebo p <= 0.05. $250k notional per market.

## Coverage (before P&L)
```
market      first       last  days  month_ends  windows  returns_ok  median_close
    TN 2016-01-11 2025-09-30  2526         117      116         1.0       132.516
    UB 2010-06-07 2025-09-30  3972         184      183         1.0       157.750
```

## Result
```
verdict: DOES NOT CONFIRM
stress_net_pos: False
t_window_ge_2: False
t_drift_neutral_ge_2: False
placebo_p_le_0.05: False
windows: 299
net: 13769
net_stress: -20675
t_window: 0.21
t_drift_neutral: 0.678
placebo_p: 0.111
placebo_median: -48753
years_positive: 8/16
```

## Per market
```
        windows       net  mean_bp  win_rate
market                                      
TN          116 -25178.07     6.04      0.48
UB          183  38946.64   -12.57      0.56
```

## By year (pooled $)
```
          net
year         
2010  35106.0
2011 -19207.0
2012  19673.0
2013  15043.0
2014   6356.0
2015  28383.0
2016 -11235.0
2017 -19838.0
2018   9993.0
2019 -19096.0
2020  19029.0
2021   7360.0
2022 -13524.0
2023  -2396.0
2024 -31672.0
2025 -10207.0
```

## Roll months (Feb/May/Aug/Nov) vs others: mean window return, bp
```
                   size   mean
market roll_month             
TN     False         77   4.06
       True          39   9.95
UB     False        122 -10.81
       True          61 -16.10
```

## Reading (2026-10-04)
Does not confirm: the post-month-end short is flat on TN/UB (t 0.21; TN loses, UB gains; 8/16 years), negative at stress
costs. The month-end rise (H-030/H-032) does not reliably reverse in the following days, so the only month-end sleeve is
the long into month-end.
