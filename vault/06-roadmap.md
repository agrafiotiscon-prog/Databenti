---
type: topic
tags: [planning]
updated: 2026-10-02
---
# Roadmap, revised after research

## What changed vs the original brief, and why

| # | Original brief | Changed to | Why (evidence) |
|---|---|---|---|
| 1 | Use `ES.c.0` | Roll-date rule: `ES.c.0` before the roll Thursday, `ES.c.1` from roll Thursday to expiry; one contract per session | `c` rolls only at expiry, so the data would sit in a dying contract for about a week per quarter ([rolls](01-databento/symbology-and-rolls.md)) |
| 2 | Limit fills via MBO queue model everywhere | **Two tiers.** L1 data over years with pessimistic `trade_through` fills, and MBO over recent months with an exact FIFO queue to *calibrate* | MBO is the most expensive schema, and the $199 plan includes only 1 month of it; years are needed for 200+ trades and per-year stats ([data plan](01-databento/pricing-and-data-plan.md)) |
| 3 | Build our own tick backtester including the MBO queue | Own **small L1 engine** + **hftbacktest** (`L3FIFOQueueModel` + latency) for MBO | A purpose-built, Databento-compatible L3 FIFO engine exists, so writing our own adds bug risk for no gain ([engines](04-backtesting/engines-compared.md)) |
| 4 | Slippage as a configurable constant | **Latency model** (default 100 ms; stress 250/500 ms) + book at arrival + empirical slippage measurement | Slippage is correlated with signals that fire in fast markets ([costs](02-market-structure/costs-fees-slippage.md)) |
| 5 | Fixed RTH/ETH calendar | Calendar **plus** the `status` schema for holidays, early closes and halts | Real schedules vary (e.g. 12:15 CT close on Christmas Eve) |
| 6 | Sharpe, profit factor, drawdown… | Plus **DSR, PBO (CSCV), t ≥ 3 hurdle, cost and latency stress, markouts, concentration** | Selection bias and multiple testing ([methodology](05-anti-overfitting/methodology.md)) |
| 7 | MBO counts of adds and cancels | Exclude `F_SNAPSHOT`; separate fill-removals from true cancels; sample after `F_LAST` | Databento MBO semantics ([MBO](01-databento/mbo-book-building.md)) |
| 8 | Loader sorted by timestamp | **File order preserved** | FIFO priority is carried by message order |
| 9 | "Improve until profitable" | Gated research loop with trial budgets and an append-only log | Unconstrained search manufactures false positives |

## Revised phases

**Phase 1: data layer** ✅, then patched after research:
- `data/contracts.py`: ES/NQ expiry and roll calendar → contract rank per trading date
- `Downloader.fetch_sessions` picks the contract per session automatically
- new schemas: `tbbo`, `mbp-1`, `bbo-1s`, `status`, `statistics`
- `data/flags.py`: flag constants and snapshot/F_LAST helpers
- loader keeps file order

**Phase 1b: first real data** (needs your API key, about $0–5):
1. Dry-run costs for 3 RTH days of `trades, tbbo, mbp-1, mbp-10, mbo, ohlcv-1m, status`.
2. Download what is under $5.
3. Verification scripts on real data:
   - roll rule vs `ES.v.0` resolve
   - side-`N` share by time of day
   - snapshot detection at 00:00 UTC
   - **fill-removal reconciliation** (F sizes = C/M reductions)
   - native-iceberg sightings
   - `F_MAYBE_BAD_BOOK` occurrences

**Phase 2: features** (✅ code complete on synthetic data, session 4; awaiting real-data validation) exactly as in [feature definitions](03-order-flow/feature-definitions.md),
plus `features/book.py` (MBO book) and the Plotly day viewer. Each feature gets hand-made unit
tests, truncation tests and perturbation tests.

**Phase 3: backtester.**
- Own L1 engine: market, stop and limit orders with `trade_through` / `queue_l1`, latency, and
  fees from `config/costs.yaml`.
- Outputs from [metrics](04-backtesting/metrics.md).
- hftbacktest adapter for the tier-B `l3_fifo` calibration.

**Phase 4: research framework**: splits with a locked holdout, walk-forward, CPCV, DSR, PBO,
the sensitivity heatmaps, the trial log, red flags and the gate report.

**Phase 5: one hypothesis-driven strategy** (absorption at a profile level + delta divergence →
fade; fixed stop and target). Run it through all gates, give an honest verdict, then switch on
the [research loop](05-anti-overfitting/research-loop.md) as a scheduled routine.

## Decisions needed from you (✅ answered in session 4: ES, pay-as-you-go, 12-month holdout, IBKR default; see decisions D-012..D-015)
1. **Instrument:** ES (fees 0.36 tick per round turn; about $22–24k margin) vs MES (fees about
   1 tick per round turn; about 1/10 the margin). Research on ES is cheaper in cost terms; MES is
   cheaper in capital.
2. **Data budget:** usage-based (pay per GB; $125 free credits) vs the Standard plan ($199/mo,
   1 year L1 + 1 month L2/L3 included).
3. **Holdout:** OK to reserve the most recent 12 months?
4. **Broker:** so `config/costs.yaml` matches your real fees.
