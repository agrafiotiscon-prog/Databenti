---
type: memory
updated: 2026-10-02
tags: [memory, state]
---
# MEMORY: always-loaded project state (keep it short; details live in linked notes)

## The user
- Wants an **honest** order-flow research and backtesting system for CME index futures using
  Databento. The goal is a real edge after **realistic fees, commissions and slippage**, not a
  pretty backtest.
- Wants an **automated, continuously-improving research routine** that logs everything it tries.
- Wants everything **researched before building**, and has authorised overriding their own
  brief when the research is stronger. Wants this vault to be Claude's persistent memory.
- Works in phases: stop after each phase and wait for their OK.
- Shares outside material (e.g. video transcripts) → it goes into `vault/inbox/`.
- Full brief: [project-brief](project-brief.md).

## Decisions made by the user (session 4) → [decisions](decisions.md) D-012..D-015
- Instrument **ES**. Billing **pay-as-you-go** ($125 credit, $5 guard). Holdout = **last 12
  months** (frozen at the first multi-month tier-A pull, `config/splits.toml`; until then a
  provisional lock from today − 12 months is enforced by `data/holdout.py`). Broker **not chosen**
  → IBKR fees as the default profile (`config/costs.toml`).

## Current state (2026-10-03, session 6)
- Phases 0–2 done. **Phase 2 features validated on the first real day** (2024-03-05, ES), incl.
  a visual check ([day-check](../results/day-check-2024-03-05-rth.md)).
- **Real data** (key works; `DATABENTO_API_KEY` is an environment variable). Spent **$118.92**
  in total; earlier ($10.02 before `cache/download_log.csv` existed + $0.04 logged there; `spend_log.csv`
  also logs dry runs, so never sum it). Cached
  locally (not in git): 2024-03-05 trades/tbbo/mbo/status, trades for the 2024-03 roll window
  (c.0 + c.1), ES daily bars 2019–2025-09.
- Findings → [results](../results/README.md): roll crossover = **Monday of expiry week**
  (D-016, rule changed 8 → 4 days); MBO needed a **book warm-up** from the 00:00 UTC snapshot
  (fixed); MBO fill accounting is **exact** (1.0) once hidden iceberg reserve and
  modify-into-market aggressor fills (any F away from the resting price, 1.27%) are recorded; side-N share ≈ 0.002% (negligible); native
  iceberg refill = same-order `M` in the fill's event (mostly 1-lot clips).
  Calibration (D-018): synthetic icebergs ≈ chance → experimental; spoof label is descriptive only.
- **Hourly research routine** active (D-017, `trig_01SxDd7cr6pA7egPMDYvJNAH`, :15 UTC): it
  follows `research/ROUTINE.md` and works through `research/QUEUE.md`. Budget per D-019
  (cap $120 total); keeps a strategy only if it passes G1–G11.

## Next step
- Phases 3–5 done. **H-001 evaluated once (D-020) → NOT PROMISING, closed (D-021)**: 70/72
  variants lose after costs, median −1.25 ticks/trade → [h001-report](../results/h001-report.md).
- **H-002** (intraday momentum + delta filter, 1 year): inconclusive, t = 0.08. **H-003** (same
  signal, 15 y of hourly bars): **not promising**, 2,095 OOS trades, t = 0.21, 6/13 years > 0
  (D-024). **H-004** (follow multi-level sweeps): **not promising**, OOS t = −5.5, 0/16 > 0 (D-025).
  Total hypothesis trials: 108. Reports: `vault/results/h00{1,2,3,4}-report.md`.
- Data cached: 238 RTH trade days 2024-11..2025-09; ES hourly bars 2010-06..2025-09 (both ranks).
  Holdout frozen at 2025-10-03. Next: R6.3 (needs cached data or the user's OK to spend).
- **Budget (D-019):** whole $125 credit approved; hard cap $120 in code; **spent $118.92** →
  only $1.08 left. No more data purchases without the user. One year cannot pass G7.

## Open questions
- Recheck detector calibration (D-018) on more MBO days (needs the user's OK for MBO)
- CME fees after 2026-10-01 (SER #9799) → [costs](../02-market-structure/costs-fees-slippage.md)
- Roll rule for NQ/MES/MNQ not measured (ES only)

## Key numbers
- ES: tick 0.25 = $12.50. Fees about $2.26/side, $4.51 per round turn. Market-in/market-out ≈
  **1.36 ticks ≈ $17** before slippage.
- Latency 100 ms (stress 250/500). Fees ×1.5 and ×2 stress. Gates G1–G11 (≥ 200 trades,
  DSR ≥ 0.95, PBO ≤ 0.10, plateau, MC 5th percentile > 0, cluster medoid).

## Where things are
- [decisions](decisions.md) · [journal/](../journal/) · [inbox/](../inbox/) · [results/](../results/README.md) · [roadmap](../06-roadmap.md)
- Code: `data/` (Phase 1) · `features/` (Phase 2) · `backtest/` (Phase 3) · `scripts/` · `config/` · `tools/vault.py`
- Routine: `research/ROUTINE.md` (rules) · `research/QUEUE.md` (work) · `research/CHANGELOG.md`
