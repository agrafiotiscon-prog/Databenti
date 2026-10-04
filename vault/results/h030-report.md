---
type: result
date: 2026-10-04
tags: [R9, H-030, gates]
---
# H-030 Treasury month-end: gate verdict **not promising**

Treasury futures around month-end - long into the last days of the month (index extension) or into the first days (cash-need reversal). 3973 dates 2010-06-07..2025-09-30; 13 folds (3 y / 1 y). DSR N = 208. Capital $1,000,000. long outright, enter/exit at closes, 1 tick + fees per side.

## Coverage (before P&L, D-042)
```
market      first       last  month_ends  pre5_windows  post5_windows
    ZT 2010-06-07 2025-09-30         184           184            183
    ZF 2010-06-07 2025-09-30         184           184            183
    ZN 2010-06-07 2025-09-30         184           184            183
    ZB 2010-06-07 2025-09-30         184           184            183
```

OOS (walk-forward): {'ann_return_pct': 1.37, 'ann_vol_pct': 2.21, 'sharpe': 0.62, 'max_dd_pct': -3.92, 't_daily': 2.205}
OOS contract trades: 472

## Gates
```
                                                          requirement result                                                    evidence
gate                                                                                                                                    
G1                                                  >= 200 OOS trades   PASS                                              oos_trades=472
G2                                OOS net > 0 at 1.5x fees and 250 ms   PASS                           oos_net_stress=130382.73999999954
G3                      DSR >= 0.95 (raw N) and OOS mean-trade t >= 2   FAIL                 dsr_raw=2.4250159274374905e-05, oos_t=2.205
G4                                                        PBO <= 0.10   PASS                                   pbo=0.0016317016317016317
G5                                                 +-20% plateau test   FAIL                                          plateau_pass=False
G6                                 not concentrated (red flags clear)   PASS                                          concentrated=False
G7                       positive in >= 60% of OOS years (>= 2 years)   PASS         years_positive_share=0.7692307692307693, n_years=13
G8                           tier-B fill check does not flip the sign   PASS                                       tier_b_same_sign=True
G9                 MC 5th pct net > 0 and P(loss) <= 10% at 1.5x fees   PASS               mc_net_p5=49779.625499998685, mc_p_loss=0.006
G10   cluster medoid; >= 70% of its cluster profitable; not an island   PASS  is_medoid=True, cluster_share_profitable=1.0, island=False
G11                        DSR >= 0.95 with cluster-based effective K   FAIL                                   dsr_k=0.35267255832394184
G12   beats a placebo / random-timing benchmark (one-sided p <= 0.05)   PASS                                               placebo_p=0.0
```

Placebo: real OOS net 173,130 vs placebo median -104,907 (95th pct -9,143); p = 0.000

Net by scenario (OOS): {'base': 173130, 'fees1.5': 170742, 'stress': 130383, 'plus1tick': 132771}

### By year (OOS)
```
      oos_net  return_pct
2013  -7503.0       -0.75
2014  31005.0        3.10
2015   9106.0        0.91
2016  51715.0        5.17
2017 -17629.0       -1.76
2018  28164.0        2.82
2019  20430.0        2.04
2020  25092.0        2.51
2021  -7691.0       -0.77
2022   6066.0        0.61
2023   1976.0        0.20
2024  12847.0        1.28
2025  19552.0        1.96
```

## Variant chosen per fold
```
 fold                   test        variant  train_net_p5
    0 2013-06-04..2014-05-30 pre|3|long_end         39574
    1 2014-06-03..2015-05-29      pre|5|all         -1643
    2 2015-06-02..2016-05-31 pre|5|long_end         22474
    3 2016-06-02..2017-05-31 pre|5|long_end         19434
    4 2017-06-02..2018-05-31 pre|5|long_end          8438
    5 2018-06-04..2019-05-31      pre|3|all        -18862
    6 2019-06-04..2020-05-29      pre|3|all         -7587
    7 2020-06-02..2021-05-31 pre|3|long_end         18599
    8 2021-06-02..2022-05-31      pre|5|all         10722
    9 2022-06-02..2023-05-31      pre|3|all        -17772
   10 2023-06-02..2024-05-31      pre|3|all        -35157
   11 2024-06-04..2025-05-30      pre|3|all        -13643
   12 2025-06-03..2025-09-30      pre|3|all         -6280
```

## Family (full period): PBO = 0.002, K = 4
```
                 ann_return_pct  ann_vol_pct  sharpe  max_dd_pct  t_daily  net_full  trades
pre|3|long_end             2.04         2.60   0.785       -3.54    3.117  321438.0   368.0
post|3|long_end           -0.78         3.17  -0.245      -22.73   -0.974 -122438.0   366.0
pre|3|all                  1.42         1.69   0.842       -1.97    3.342  223755.0   736.0
post|3|all                -0.53         2.05  -0.260      -14.15   -1.031  -83727.0   732.0
pre|5|long_end             2.44         3.32   0.737       -6.88    2.925  385136.0   368.0
post|5|long_end           -2.02         4.07  -0.496      -36.35   -1.971 -318469.0   366.0
pre|5|all                  1.63         2.14   0.761       -4.08    3.022  256847.0   736.0
post|5|all                -1.38         2.63  -0.527      -24.05   -2.091 -218227.0   732.0
```


## Reading and robustness (2026-10-04, descriptive; does not change the verdict)
**9/12 gates - the most of any hypothesis so far - but not promoted** (fails G3: DSR with N = 214 global trials;
G5: the plateau test compares the chosen variant with all others, which include the four *post* variants that
lose by construction; G11). Not re-defined after the fact.
- **The pre-month-end window is positive in every variant** (t 2.9-3.3 full period); the post window is negative
  in every variant: prices rise into month-end and give part of it back after - the shape a price-pressure
  (index duration extension) mechanism predicts.
- **Effect scales with duration** (pre-3-day mean per window): ZT +3.7 bp, ZF +12.0, ZN +16.0, ZB +27.2 vs an average
  3-day return of −0.2..+2.0 bp; per-window t 4.1-5.0 in each market; 14/16 years positive in each market.
- **Stable over time:** net per market is almost identical in 2010-17 and 2018-25 (e.g. ZB $54k / $55k).
- **Not a roll artefact:** it holds in non-roll months (Jan/Mar/Apr/...; ZN t 3.7) as well as in the quarterly
  roll months (ZN t 2.2).
- **Placebo caveat:** random long windows lost (median −$105k) because bonds fell in 2020-23, so p = 0.000 overstates
  the timing edge; but the real result is positive in absolute terms (OOS +$173k, t 2.2; stress +$130k).
- Small risk use: at $1M with 1x notional the book runs ~2-3% vol; scaled to 15% vol this would be ~10-12%/yr
  *before* accounting for selection (DSR) - an upper bound, not a forecast.
- Execution: ohlcv-1d closes are the last trade of the UTC day (evening ET Globex session), consistent for entry and
  exit; month-end dates are exchange-calendar facts (no lookahead).
**Status: strongest candidate so far; needs independent confirmation** - forward data (paper tracking) or a
pre-registered replication on Treasury futures not used here (UB ultra bond, TN ultra 10-year; ~$0.1 of data,
needs the user's OK).
