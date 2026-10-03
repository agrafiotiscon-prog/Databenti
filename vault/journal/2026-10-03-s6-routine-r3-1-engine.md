---
type: journal
date: 2026-10-03
tags: [journal]
---
# s6-routine-r3-1-engine

## 2026-10-03 03:19 UTC
Routine R3.1 (03:15 UTC firing): Phase 3 started. backtest/engine.py (L1 event replay, market orders with latency, fills at the worse of the books around arrival, fees from config/costs.toml, position limit, end flatten) and backtest/costs.py. Found and fixed a unit bug while testing (pandas 2 index units vs Timestamp.value ns). Null-baseline run on real 2024-03-05 RTH TBBO behaves as expected (-2.95 ticks/trade gross, fees exact); logged to research/trials.jsonl as engine-sanity, not a strategy. Next: R3.2 limit/stop orders.
