# Research queue (the routine takes the first open item; see ROUTINE.md)

Ordered. Split big items before starting them. Tick `[x]` when done and note the commit.

## Phase 2 leftovers: real-data validation (cached 2024-03-05 data, $0)
- [x] R2.1 (session 5: ratio 1.0 RTH, 0.9999994 full; see mbo-fill-reconciliation-2024-03-05) Re-run `scripts/verify_data.py --date 2024-03-05` (RTH and full) with the new fill
      accounting; confirm `fill_accounted_ratio` ≈ 1.0 and write
      `vault/results/mbo-fill-reconciliation-2024-03-05.md` (diagnosis already done in session 5:
      0.48% hidden iceberg reserve, 0.12% orders modified into the market).
- [x] R2.2 (s6: same-order M in the fill's event; see mbo-iceberg-refills-2024-03-05) (removed: 1,544 → 1,540 RTH, 1,850 → 1,843 full) Describe
      how native refills really look in Databento MBO (answers an open question in MEMORY).
- [x] R2.3 (s6, D-018: synthetic dt=1ms + clips>=2, experimental; spoof descriptive) Calibrate on the real distribution: spoof `min_size` (default 50) and synthetic-iceberg
      `dt` (5 ms; 44,893 synthetic icebergs in one RTH looks far too many). Record the choice and
      the evidence; parameters are fixed BEFORE any strategy uses them.
- [x] R2.4 (s6: found fully-filled modify-into-market pattern; see day-check-2024-03-05-rth) `scripts/plot_day.py --date 2024-03-05 --mbo` visual sanity check; save a screenshot
      or summary to `vault/results/`.

## Phase 3: backtester (vault/04-backtesting/)
- [x] R3.1 (s6: backtest/engine.py + costs.py; null baseline in trials.jsonl) L1 event engine skeleton: replay trades/tbbo in file order, strategy callback sees
      only data with `ts_recv + latency <= now`; market orders fill at the book seen at
      arrival (+ latency); fees from `config/costs.toml`. Tests: no-lookahead (negative
      control), fee arithmetic, one-contract position limits.
- [x] R3.2 (s6: limit/stop/cancel, trade_through + queue_l1; fill-mode check in trials.jsonl) Limit and stop orders with `trade_through` (pessimistic) and `queue_l1` fill modes.
- [x] R3.3 (s6: backtest/metrics.py; DSR/PBO/MC/stress belong to Phase 4) Metrics from `vault/04-backtesting/metrics.md` (per-trade, daily PnL, markouts,
      concentration) + per-year/month tables.
- [x] R3.4 (s6: backtest/hft_adapter.py; book = ours on 3,600/3,600 samples) hftbacktest adapter for tier-B `l3_fifo` calibration (MBO; only on cached days).

- [ ] R3.5 Tier-B calibration run: same strategy under trade_through / queue_l1 / hftbacktest l3_fifo
      on the cached MBO day; report fill-rate and PnL differences (needs a limit-order strategy;
      do it with H-001 in Phase 5 if nothing earlier fits).

## Phase 4: research framework (vault/05-anti-overfitting/)
- [ ] R4.1 Holdout lock in the loader (`config/splits.toml`), walk-forward splitter with embargo.
- [ ] R4.2 Append-only trial log `research/trials.jsonl` + hypothesis registry
      `research/hypotheses/*.yaml` (mechanism, space, budget written first).
- [ ] R4.3 DSR, PBO (CSCV), plateau test, Monte Carlo (block bootstrap + execution MC).
- [ ] R4.4 Cluster analysis of trials (effective K, medoids) and the G1–G11 gate report.

## Phase 5: first hypothesis
- [ ] R5.1 Registry entry H-001: absorption at a profile level + delta divergence → fade; fixed
      stop/target; declared space and budget.
- [ ] R5.2 Price the L1 data it needs (trades/tbbo, RTH). Within the routine budget, use what is
      affordable; a meaningful test needs years (see "Needs the user").
- [ ] R5.3 Run, gate, verdict (promising / not promising / insufficient data).

## Later: new hypotheses (one at a time, mechanism first; see vault/03-order-flow/evidence-review.md)

## Needs the user
- **Data budget for real backtests.** ES trades cost about $0.55 per full UTC day (tbbo ≈ $0.92):
  one year of trades ≈ $140, more than the remaining pay-as-you-go credit (~$112 after
  session 5). G1 needs ≥ 200 OOS trades and G7 needs several years. Options: Standard plan
  ($199/mo, 1 year of L1 included), a larger pay-as-you-go budget, or accept "insufficient data"
  verdicts. The routine stays within $25 until you decide.
