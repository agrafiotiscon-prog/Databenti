---
type: result
date: 2026-10-05
tags: [R15, H-044, fomc, confirmation]
---
# H-044 Treasury futures, long day-1..day+1 around FOMC: **CONFIRMS**

Pre-registered (research/hypotheses/H-044.yaml, committed before the run). Fixed rule from the paper, single evaluation, $250,000 notional per market, 2010-06..2025-09 (development data only).

## Coverage (before P&L)
```
market      first       last  fomc_in_range  fomc_traded  windows  returns_ok  median_close
    ZT 2010-06-07 2025-09-30            122          122      122         1.0     109.13281
    ZF 2010-06-07 2025-09-30            122          122      122         1.0     118.96875
    ZN 2010-06-07 2025-09-30            122          122      122         1.0     125.79688
    ZB 2010-06-07 2025-09-30            122          122      122         1.0     144.21875
    TN 2016-01-11 2025-09-30             77           77       77         1.0     132.51562
    UB 2010-06-07 2025-09-30            122          122      122         1.0     157.75000
```

## Result
```
verdict: CONFIRMS
stress_net_pos: True
t_window_ge_2: True
t_drift_neutral_ge_2: True
placebo_p_le_0.05: True
t_no_month_end_ge_2: True
windows: 687
net: 255677
net_stress: 207047
t_window: 3.63
t_drift_neutral: 4.624
t_no_month_end: 2.282
month_end_overlap_share: 0.37
placebo_p: 0.002
placebo_median: -43212
years_positive: 11/16
```

## Paper overlap vs post-sample
```
                         windows        net  mean_bp     t
period                                                    
<= 2017 (paper overlap)      321   84462.97    13.99  1.63
> 2017 (post-sample)         366  171213.96    22.86  3.60
```

## Per market
```
        windows       net  mean_bp  win_rate
market                                      
TN           77  39336.71    22.72      0.65
UB          122  84713.66    35.03      0.57
ZB          122  71252.65    29.00      0.61
ZF          122  19633.94     8.91      0.58
ZN          122  35774.56    15.22      0.60
ZT          122   4965.41     2.90      0.55
```

## By year (pooled $)
```
           net
year          
2010   21453.0
2011  118910.0
2012  -57956.0
2013  -22934.0
2014  -23715.0
2015    6470.0
2016   30358.0
2017   11878.0
2018   13572.0
2019   54563.0
2020   43313.0
2021  -31161.0
2022  -10708.0
2023   60634.0
2024   37041.0
2025    3960.0
```

