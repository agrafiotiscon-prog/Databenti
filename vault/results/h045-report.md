---
type: result
date: 2026-10-05
tags: [R15, H-045, fomc, confirmation]
---
# H-045 FX futures, short USD on FOMC days: **CONFIRMS**

Pre-registered (research/hypotheses/H-045.yaml, committed before the run). Fixed rule from the paper, single evaluation, $125,000 notional per market, 2010-06..2025-09 (development data only).

## Coverage (before P&L)
```
market      first       last  fomc_in_range  fomc_traded  windows  returns_ok  median_close
    6E 2010-06-07 2025-09-30            122          122      122      0.9997       1.14587
    6J 2010-06-07 2025-09-30            122          122      122      0.9997       0.00911
    6B 2010-06-07 2025-09-30            122          122      122      0.9997       1.34955
    6A 2010-06-07 2025-09-30            122          122      122      0.9997       0.74560
    6C 2010-06-07 2025-09-30            122          122      122      1.0000       0.77563
    6S 2010-06-07 2025-09-30            122          122      122      0.9997       1.06720
    6N 2010-06-07 2025-09-30            122          122      122      0.9997       0.69395
    6M 2010-06-07 2025-09-30            122          122      122      0.9997       0.05410
```

## Result
```
verdict: CONFIRMS
stress_net_pos: True
t_window_ge_2: True
t_drift_neutral_ge_2: True
placebo_p_le_0.05: True
windows: 976
net: 110960
net_stress: 88457
t_window: 3.436
t_drift_neutral: 4.082
t_no_month_end: 4.376
month_end_overlap_share: 0.254
placebo_p: 0.0
placebo_median: -27274
years_positive: 12/16
```

## Paper overlap vs post-sample
```
                         windows        net  mean_bp     t
period                                                    
<= 2014 (paper overlap)      296  -18510.52    -4.71 -0.95
> 2014 (post-sample)         680  129470.28    16.30  5.09
```

## Per market
```
        windows       net  mean_bp  win_rate
market                                      
6A          122  11711.92     7.16      0.57
6B          122  17726.73    10.94      0.57
6C          122   6846.43     4.10      0.48
6E          122  13868.53     9.23      0.57
6J          122   2324.46     3.11      0.54
6M          122  27505.78    22.80      0.58
6N          122  11551.13     9.16      0.54
6S          122  19424.78    12.91      0.57
```

## By year (pooled $)
```
          net
year         
2010  15247.0
2011  -8609.0
2012  13211.0
2013  -4330.0
2014 -34029.0
2015   7627.0
2016  13913.0
2017  21138.0
2018   1492.0
2019  12013.0
2020  23740.0
2021   1177.0
2022  16358.0
2023  34746.0
2024  14881.0
2025 -17616.0
```

