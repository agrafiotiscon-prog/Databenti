---
type: result
date: 2026-10-04
tags: [R9, H-032, H-030, confirmation]
---
# H-032 confirmation of H-030 on TN/UB (never used before): **CONFIRMS**

Pre-registered (research/hypotheses/H-032.yaml, committed before the data was downloaded): CONFIRMS only if stress net > 0, per-window t >= 2, drift-neutral t >= 2 and random-window placebo p <= 0.05. Rule: long 3 trading days into month-end, $250k notional per market.

## Coverage (before P&L)
```
market      first       last  days  month_ends  windows  returns_ok  median_close
    TN 2016-01-11 2025-09-30  2526         117      117         1.0       132.516
    UB 2010-06-07 2025-09-30  3972         184      184         1.0       157.750
```

## Result
```
verdict: CONFIRMS
stress_net_pos: True
t_window_ge_2: True
t_drift_neutral_ge_2: True
placebo_p_le_0.05: True
windows: 301
net: 208479
net_stress: 180109
t_window: 4.458
t_drift_neutral: 5.053
placebo_p: 0.0
placebo_median: -78081
years_positive: 15/16
```

## Per market
```
        windows        net  mean_bp  win_rate
market                                       
TN          117   55810.64    20.88      0.62
UB          184  152668.59    36.50      0.59
```

## By year (pooled $)
```
          net
year         
2010  25687.0
2011  15204.0
2012  19285.0
2013   2579.0
2014  15767.0
2015   5316.0
2016  16324.0
2017   7145.0
2018  20284.0
2019  20382.0
2020  25744.0
2021   3744.0
2022  -6346.0
2023   3752.0
2024  15962.0
2025  17650.0
```

## Roll months (Feb/May/Aug/Nov) vs others: mean window return, bp
```
                   size   mean
market roll_month             
TN     False         78  21.39
       True          39  19.85
UB     False        123  37.19
       True          61  35.10
```

## Reading (2026-10-04)
**H-030 is confirmed on contracts that played no part in finding it.** All four pre-registered criteria pass with
margin: stress net +$180k, per-window t 4.46, drift-neutral t 5.05 (so it is not the bond trend), placebo p 0.000,
15/16 years positive. The size again scales with duration (TN +21 bp, UB +37 bp per 3-day window, vs ZN +16, ZB +27 in
H-030) and is the same in roll and non-roll months. Caveat: TN/UB are highly correlated with ZN/ZB, so this rules out
a four-contract artefact, not a common cause in the Treasury market. TN's 2010-12 bars (a different, illiquid
product under the same root) were excluded per the registry ("from its 2016 listing").
