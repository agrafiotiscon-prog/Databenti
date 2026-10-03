---
type: journal
date: 2026-10-03
tags: [journal]
---
# s6-routine-r3-2-limit-stop

## 2026-10-03 04:19 UTC
Routine R3.2 (04:15 UTC firing): engine now supports limit orders (trade_through default, queue_l1), stop orders and cancels with latency (an order can fill while its cancel is in flight; same-instant ties go to the fill). Position limit now uses the worst case of active orders, so brackets fit. Real TBBO check logged in trials.jsonl (engine-sanity). Next: R3.3 metrics.
