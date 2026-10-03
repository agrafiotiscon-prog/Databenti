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
  months** (frozen at the first multi-month pull, `config/splits.toml`). Broker **not chosen**
  → IBKR fees as the default profile (`config/costs.toml`).

## Current state (2026-10-02, session 5)
- Phases 0–1 done. **Phase 2 features: validated on the first real day** (2024-03-05, ES).
- **Real data** (key works; `DATABENTO_API_KEY` is an environment variable). Spent **$10.06** so
  far ($10.02 before `cache/download_log.csv` existed + $0.04 logged there; `spend_log.csv`
  also logs dry runs, so never sum it). Cached
  locally (not in git): 2024-03-05 trades/tbbo/mbo/status, trades for the 2024-03 roll window
  (c.0 + c.1), ES daily bars 2019–2025-09.
- Findings → [results](../results/README.md): roll crossover = **Monday of expiry week**
  (D-016, rule changed 8 → 4 days); MBO needed a **book warm-up** from the 00:00 UTC snapshot
  (fixed); MBO fill accounting is **exact** (1.0) once hidden iceberg reserve and
  modify-into-market aggressor fills are recorded; side-N share ≈ 0.002% (negligible); native
  iceberg refill = same-order `M` in the fill's event (mostly 1-lot clips).
  Calibration (D-018): synthetic icebergs ≈ chance → experimental; spoof label is descriptive only.
- **Hourly research routine** active (D-017, `trig_01SxDd7cr6pA7egPMDYvJNAH`, :15 UTC): it
  follows `research/ROUTINE.md` and works through `research/QUEUE.md`. Budget ≤ $1/firing,
  ≤ $3/day, ≤ $25 total; keeps a strategy only if it passes G1–G11.

## Next step
- The routine continues with `research/QUEUE.md`: R2.4 (visual check), then Phase 3 (L1 backtester), Phase 4 (framework), Phase 5 (H-001).
- **Needs the user:** a data budget for real backtests. One year of ES trades ≈ $140 on
  pay-as-you-go (more than the ~$115 left); Standard plan $199/mo includes 1 year of L1.

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
- Code: `data/` (Phase 1) · `features/` (Phase 2) · `scripts/` · `config/` · `tools/vault.py`
- Routine: `research/ROUTINE.md` (rules) · `research/QUEUE.md` (work) · `research/CHANGELOG.md`
