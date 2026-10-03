---
type: result
date: 2026-10-03
tags: [phase-3, R3.5, fills, calibration]
---
# Tier-B fill calibration on 2024-03-05 (R3.5, `scripts/calibrate_fills.py`)

77 passive 1-lot probes (every 5 min in RTH, alternating buy at bid / sell at ask, 60 s life, 100 ms latency). Markout = mid 60 s after the fill minus fill price, in our favour, ticks.

```
               probes  filled  fill_rate  maker_fills  median_wait_s  markout60_ticks_mean  markout60_ticks_median
trade_through    77.0    61.0      0.792         49.0            1.7                 -0.33                    -1.5
queue_l1         77.0    67.0      0.870         55.0            0.9                  0.33                    -0.5
hft_l3_fifo      77.0    52.0      0.675         52.0            1.6                  0.27                     0.0
```

Fill/no-fill agreement with the L3 FIFO reference: {'trade_through vs hft': 0.727, 'queue_l1 vs hft': 0.805}

## Interpretation [inferred; one day, 77 probes - small sample]
- **Passive (maker) fills:** trade_through 49, L3 FIFO reference 52, queue_l1 55. The engine's
  default `trade_through` is **close to the full-book reference and slightly conservative** (−6%);
  `queue_l1` is slightly optimistic (+6% fills, faster: median wait 0.9 s vs 1.6 s).
- The engine's extra fills (61 − 49 = 12 for trade_through) are **taker** fills: a plain limit
  order that became marketable during the 100 ms flight. hftbacktest used post-only (GTX) orders,
  which are rejected instead - an order-type difference, not a fill-model error.
- **Adverse selection:** trade_through fills have the worst 60 s markout (median −1.5 ticks): it
  fills only when price trades through us, i.e. exactly when we are wrong - pessimistic by design.
  L3 FIFO median 0.0 ticks, queue_l1 −0.5.
- Fill/no-fill agreement with L3 FIFO: 73% (trade_through), 81% (queue_l1).
- **Decision (D-047): keep `trade_through` as the default for limit-order strategies; never use
  `queue_l1` alone for a promotion decision** (G8 tier-B check stays). More MBO days would tighten
  this (needs the user's OK for MBO spend).
