# Research changelog (one line per routine unit; append-only)

- 2026-10-02 s5: routine set up (D-017). Queue seeded from the roadmap.
- 2026-10-03 R2.2: native refill = same-order M in the fill's event (100%); synthetic re-posts can't be told apart from new orders (156k/day). Result note written. $0.
- 2026-10-03 R2.3: calibrate_mbo.py; synthetic icebergs ≈ chance (experimental, dt=1ms, clips>=2), spoof label descriptive (45% base rate). D-018. $0.
- 2026-10-03 R2.4: day-chart check found orders modified into the market and fully filled (F away from resting price) misread as icebergs; fixed (aggressor 1.27% of fills, native icebergs 1,540→1,432); late size increases no longer count as refills. Phase 2 complete. $0.
- 2026-10-03 R3.1: L1 engine (market orders, latency, worse-of-book at arrival, fees, position limit) + 8 tests; null baseline on real TBBO: -2.95 ticks/trade gross, fees exact. $0.
