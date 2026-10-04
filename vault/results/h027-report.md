---
type: result
date: 2026-10-04
tags: [R8, H-027, FOMC, replication]
---
# H-027 pre-FOMC drift on NQ/RTY/YM daily bars: **DOES NOT REPLICATE**

Pre-registered: REPLICATES if pooled mean > 0, per-event t >= 2 and placebo p <= 0.05 (registry H-027).
Window: UTC-day close before the statement day -> statement-day close (includes the 14:00 ET reaction).

## Coverage (before P&L)
```
market      first       last  fomc_expected  fomc_found missing
    NQ 2010-06-08 2025-09-30            122         122       -
   RTY 2017-07-11 2025-09-30             65          65       -
    YM 2010-06-08 2025-09-30            122         122       -
```

## Result (pooled, $333k notional per market)

```
verdict: DOES NOT REPLICATE
events: 122
net: 143874
mean_per_event: 1179
t: 1.133
win_rate: 0.574
net_stress: 131141
placebo_p: 0.167
placebo_median: 36833
```

## Per market
```
     events      net   mean  win_rate     t
NQ    122.0  96044.0  787.0     0.582  1.83
RTY    65.0  24237.0  373.0     0.523  0.50
YM    122.0  23593.0  193.0     0.525  0.59
```

## By year (pooled)
```
      count      sum
2010      5  -5149.0
2011      8  11621.0
2012      8  18184.0
2013      8   -656.0
2014      8   5743.0
2015      8   6791.0
2016      8  -1660.0
2017      8   6472.0
2018      8 -37399.0
2019      8  -3011.0
2020      7  50047.0
2021      8  24299.0
2022      8  28871.0
2023      8  10726.0
2024      8   7319.0
2025      6  21676.0
```

## Reading (2026-10-04)
Does not replicate by the pre-registered rule. The direction is right (pooled +$144k over 122 events, 57% winners,
positive at stress costs, 11/16 years > 0) but the size is not distinguishable from ordinary equity drift: random
non-FOMC days earn a median $37k on the same sizing and the FOMC days beat them only with p = 0.17; t = 1.13.
NQ is strongest (t 1.83), YM and RTY are weak (t 0.59, 0.50). 2020 alone is +$50k. Combined with the ES holdout
loss (D-052) this lowers the prior for H-007: the pre-FOMC drift looks much weaker post-2010 than in Lucca-Moench's
1994-2011 sample, as later studies also report. Note the daily window includes ~6 h after the statement.
