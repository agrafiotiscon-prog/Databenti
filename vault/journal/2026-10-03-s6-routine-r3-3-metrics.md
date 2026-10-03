---
type: journal
date: 2026-10-03
tags: [journal]
---
# s6-routine-r3-3-metrics

## 2026-10-03 05:17 UTC
Routine R3.3 (05:15 UTC firing): backtest/metrics.py implements the single-run metrics from vault/04-backtesting/metrics.md (daily series by CME trading date with zero days; Sharpe, Lo-adjusted Sharpe, PSR; drawdown; concentration flags; breakdowns; signed markouts; exposure). Tests are hand-computed with negative controls (Lo on iid data). End-to-end report on the real null baseline works (markout +100 ms = -0.61 ticks: half spread on market fills). Next: R3.4 hftbacktest adapter.
