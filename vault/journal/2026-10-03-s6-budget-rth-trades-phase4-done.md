---
type: journal
date: 2026-10-03
tags: [journal]
---
# s6-budget-rth-trades-phase4-done

## 2026-10-03 09:27 UTC
User approved spending the whole $125 credit (D-019, cap $120 in code). Priced options: one year of tbbo $232, trades full-day $139, trades RTH-window ~$110 -> buying RTH trades 2024-11..2025-09 plus ~8 TBBO calibration days. Built Downloader.fetch_rth (RTH-window requests, cumulative cap) and backtest.engine.l1_from_trades (bid/ask rebuilt from aggressor prints: 81% exact vs TBBO, else +-1 tick, mean bias +0.017 ticks). Stage-1 download (Jul-Sep 2025) started; it freezes holdout_start. R4.4 done: research/clusters.py + research/gates.py. Phase 4 complete; next Phase 5 (H-001).
