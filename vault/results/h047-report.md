---
type: result
date: 2026-10-05
tags: [R15, H-047, fomc, confirmation]
---
# H-047 Treasury futures, long on employment/CPI release days: **DOES NOT CONFIRM**

Pre-registered (research/hypotheses/H-047.yaml, committed before the run). Fixed rule from the paper, single evaluation, $250,000 notional per market, 2010-06..2025-09 (development data only).

## Coverage (before P&L)
```
market      first       last  fomc_in_range  fomc_traded  windows  returns_ok  median_close
    ZT 2010-06-07 2025-09-30            367          364      364         1.0     109.13281
    ZF 2010-06-07 2025-09-30            367          364      364         1.0     118.96875
    ZN 2010-06-07 2025-09-30            367          364      364         1.0     125.79688
    ZB 2010-06-07 2025-09-30            367          364      364         1.0     144.21875
    TN 2016-01-11 2025-09-30            233          231      231         1.0     132.51562
    UB 2010-06-07 2025-09-30            367          364      364         1.0     157.75000
```

## Result
```
verdict: DOES NOT CONFIRM
stress_net_pos: False
t_window_ge_2: False
t_drift_neutral_ge_2: False
placebo_p_le_0.05: False
t_no_h030_h044_overlap_ge_2: False
windows: 2051
net: -220543
net_stress: -365545
t_window: -2.919
t_drift_neutral: -1.041
t_no_month_end: -3.098
month_end_overlap_share: 0.075
placebo_p: 0.669
placebo_median: -181704
years_positive: 5/16
```

## Paper overlap vs post-sample
```
         windows        net  mean_bp     t
period                                    
<= 2017      941  -37455.35     1.52 -0.73
> 2017      1110 -183087.75    -3.58 -3.29
```

## Per market
```
        windows       net  mean_bp  win_rate
market                                      
TN          231 -28021.12    -1.92      0.47
UB          364 -74590.98    -3.02      0.48
ZB          364 -54589.99    -1.06      0.48
ZF          364 -20752.03    -0.70      0.48
ZN          364 -31408.28    -0.51      0.48
ZT          364 -11180.70    -0.50      0.42
```

## By year (pooled $)
```
          net
year         
2010  -8231.0
2011  43729.0
2012 -39088.0
2013 -41177.0
2014  14863.0
2015 -23349.0
2016  -4616.0
2017  20413.0
2018 -24456.0
2019 -30823.0
2020  12220.0
2021   1295.0
2022 -36339.0
2023  -8988.0
2024 -50847.0
2025 -45151.0
```

## By release type
```
         windows        net  mean_bp     t
release                                   
cpi         1025  -14029.97     2.30 -0.29
empsit      1026 -206513.14    -4.78 -3.61
```


Note: 3 of 367 release days have no bar (2017-04-14 and 2020-04-10 = Good Friday; 2014-10-03 = a gap in the cached ZN/rates bars).
