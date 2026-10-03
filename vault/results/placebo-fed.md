---
type: result
date: 2026-10-03
tags: [placebo, H-007, H-012]
---
# Placebo tests for the Fed-calendar co-leaders (diagnostic; no selection)

## H-007 (24 h pre-FOMC), OOS 2013-06-01..2025-09-30
- real FOMC days: 98 trades, mean net $323.8/trade
- random non-FOMC days (2924 available, 20,000 draws of 98): mean of means $50.1, 95th pct $346.3
- **one-sided p = 0.0630** (share of random draws with a mean at least as high)

## H-012 (FOMC-cycle even weeks) with the calendar shifted by k trading days
- real calendar (k = 0): net $75,423 over the OOS period
- shifted calendars k = 1..30: median $116,657, max $224,830
- **22 of 30 shifted calendars do at least as well as the real one** (permutation p ≈ 0.742)

```
0      75423.0
1      82682.0
2     130929.0
3     162622.0
4     224830.0
5     130327.0
6     132165.0
7      44262.0
8      31631.0
9      42361.0
10     76390.0
11    137631.0
12    178107.0
13    147810.0
14    154134.0
15    113129.0
16     81782.0
17     41946.0
18     78839.0
19    106987.0
20    156823.0
21    181944.0
22    157812.0
23    132788.0
24    120185.0
25     40342.0
26     34690.0
27     50459.0
28     52720.0
29     97226.0
30    124292.0
```
