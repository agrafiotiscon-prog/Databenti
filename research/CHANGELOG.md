# Research changelog (one line per routine unit; append-only)

- 2026-10-02 s5: routine set up (D-017). Queue seeded from the roadmap.
- 2026-10-03 R2.2: native refill = same-order M in the fill's event (100%); synthetic re-posts can't be told apart from new orders (156k/day). Result note written. $0.
- 2026-10-03 R2.3: calibrate_mbo.py; synthetic icebergs ≈ chance (experimental, dt=1ms, clips>=2), spoof label descriptive (45% base rate). D-018. $0.
- 2026-10-03 R2.4: day-chart check found orders modified into the market and fully filled (F away from resting price) misread as icebergs; fixed (aggressor 1.27% of fills, native icebergs 1,540→1,432); late size increases no longer count as refills. Phase 2 complete. $0.
- 2026-10-03 R3.1: L1 engine (market orders, latency, worse-of-book at arrival, fees, position limit) + 8 tests; null baseline on real TBBO: -2.95 ticks/trade gross, fees exact. $0.
- 2026-10-03 R3.2: limit/stop/cancel orders, trade_through + queue_l1 (optimistic refused), cancel-in-flight; 7 tests incl. negative controls; fill-mode check on real TBBO logged. $0.
- 2026-10-03 R3.3: backtest/metrics.py (trade stats, daily PnL with zero days, Sharpe/Lo/PSR, drawdown, concentration, breakdowns, markouts, exposure) + 7 hand-computed tests; scipy avoided. $0.
- 2026-10-03 R3.4: hftbacktest adapter (drops N, vectorised); hftbacktest book == our book on 3,600/3,600 real samples. Phase 3 code complete (R3.5 calibration run deferred). $0.
- 2026-10-03 R4.1: holdout lock (provisional until frozen at first multi-month tier-A pull; enforced in downloads + loads) and walk-forward splitter with embargo; 6 tests. $0.
- 2026-10-03 R4.2: hypothesis registry (YAML, validated) + hash-chained append-only trial log enforcing declared space and budget; 5 tests incl. tamper detection. $0.
- 2026-10-03 R4.3: research/stats.py (DSR, PBO-CSCV, plateau, stationary block bootstrap, execution MC, shuffle DD); 7 tests incl. best-of-200-noise negative control. $0.
- 2026-10-03 R4.4: trial clustering (effective K, medoids, islands) + G1-G11 gate report (missing evidence fails). Phase 4 complete. D-019 budget: buying ~1 year RTH trades; stage 1 (Jul-Sep 2025) running.
- 2026-10-03 R5.1: H-001 registered (fade absorption at developing VA boundary + delta divergence; 72-variant space, budget 72) before any result.
- 2026-10-03 Phase 5 prep: D-020 protocol fixed before results; strategies/h001.py; fast bracket simulator (engine-equivalent); scripts/run_h001.py (single evaluation, all-or-nothing trial logging); dry run on out-of-window days OK (no PnL viewed).
- 2026-10-03 R5.3: H-001 single evaluation: all gates fail; 70/72 variants lose after costs (median -1.25 ticks/trade); NOT PROMISING; closed (D-021). Total data spend $117.15.
- 2026-10-03 R6.1: H-002 registered (intraday momentum into the close, Gao et al. 2018 / Baltussen et al. 2021; optional cum-delta filter; 16 variants); protocol D-022 fixed before any result.
