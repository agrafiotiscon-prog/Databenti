---
type: result
date: 2026-10-05
tags: [R15, H-046, cftc, hedging-pressure, confirmation]
---
# H-046 hedgers' liquidity provision (CFTC COT, tradable days 5-20): **DOES NOT CONFIRM**

Pre-registered (research/hypotheses/H-046.yaml, committed before the run): fixed rule from Kang, Rouwenhorst & Tang (2020 JF); CONFIRMS only if stress net > 0, daily t >= 2, alpha t >= 2 beyond a reversal benchmark and week-shuffle placebo p <= 0.05. $1M notional per market per weekly cohort, ~9 long / 9 short.

## Coverage (before P&L)
```
    weeks_with_signal  first_week   last_week  returns_ok  median_close
CL                781  2010-06-08  2025-09-02      0.9884        71.390
NG                781  2010-06-08  2025-09-02      0.9952         2.995
RB                781  2010-06-08  2025-09-02      1.0000         2.114
HO                781  2010-06-08  2025-09-02      0.9995         2.255
GC                781  2010-06-08  2025-09-02      0.9972      1524.500
SI                781  2010-06-08  2025-09-02      0.9970        21.520
HG                781  2010-06-08  2025-09-02      0.9997         3.308
PL                781  2010-06-08  2025-09-02      0.9997      1006.800
PA                781  2010-06-08  2025-09-02      1.0000       930.000
ZC                781  2010-06-08  2025-09-02      0.9982       434.000
ZS                781  2010-06-08  2025-09-02      0.9984      1077.250
ZW                781  2010-06-08  2025-09-02      0.9995       577.000
KE                602  2013-12-17  2025-09-02      1.0000       545.250
ZL                781  2010-06-08  2025-09-02      0.9974        41.930
ZM                781  2010-06-08  2025-09-02      0.9972       342.000
LE                781  2010-06-08  2025-09-02      0.9979       125.800
HE                781  2010-06-08  2025-09-02      0.9990        81.800
GF                781  2010-06-08  2025-09-02      0.9971       153.150
```

## Result
```
verdict: DOES NOT CONFIRM
stress_net_pos: False
t_daily_ge_2: False
t_alpha_vs_reversal_ge_2: False
placebo_p_le_0.05: False
weeks: 798
cohort_positions: 13700
net: -7321715
net_stress: -18077632
net_per_position_bp: -5.34
t_daily: -0.726
alpha_t_vs_reversal: 0.104
beta_on_reversal: 0.431
corr_with_reversal: 0.421
reversal_net: -19201000
placebo_p: 0.256
placebo_median: -12373123
t_2010_2012: -0.47
t_2013_2025: -0.6
years_positive: 6/16
long_leg: 7842493
short_leg: -15164208
```

## By sector ($)
```
                  net
energy     -9513636.0
grains     -1723700.0
livestock  -6915053.0
metals     10830674.0
```

## By year ($)
```
            net
2010 -1607157.0
2011   778448.0
2012  -776357.0
2013  -859740.0
2014  -313466.0
2015  1855702.0
2016  3559051.0
2017  2744733.0
2018 -5643017.0
2019   299701.0
2020 -5359540.0
2021  -952361.0
2022  2686158.0
2023 -2476775.0
2024  -421212.0
2025  -835882.0
```

