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
- Works in phases, but (session 6) wants the research to **keep going without confirmation
  requests**: contact them only when sure, i.e. a candidate passes ALL gates G1–G11.
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
- **Real data** (key works; `DATABENTO_API_KEY` is an environment variable). Spent **≈ $121.2** (see Budget below)
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
  **H-005..H-008** evaluated; **leaderboard: [leaderboard](../results/leaderboard.md)** — best is
  **H-007 pre-FOMC drift** (6/11 gates, OOS 98 trades, t = 1.95), not promoted (D-027).
  **H-009..H-011**: overnight drift 5/11, daily reversal 5/11, VWAP fade 3/11 (D-029).
  H-012 FOMC-cycle even weeks scored 6/11 but was **demoted by a placebo test** (shifted calendars do
  as well → equity drift); H-007 placebo p = 0.063. **New gate G12** (placebo/random timing,
  D-032). H-013 intraday periodicity negative (D-031). G12 placebo: H-005, H-009 are drift. H-014 TSMOM
  not promising (t 0.51). **Only H-007 shows timing beyond drift (p 0.063).** H-015 macro days: 0/12, placebo p 0.53.
  H-016 pre-holiday 0/12; H-017 OPEX week 5/12 (placebo p 0.43); H-018 Monday reversal 5/12
  (placebo p 0.24 vs Tue-Fri) - all closed (D-039). H-019 month-end
  rebalancing: run 1 buggy (dropped 2/3 of months, looked good), fixed re-run 1/12 → closed (D-041/42).
  Lesson: check event coverage first. H-020 vol-managed long: 8/12 gates (most) but placebo p 0.118,
  79 trades → not promoted (D-044). H-021 buy-the-selloff 3/12, placebo p 0.99 (D-046).
  Total hypothesis trials: 174. R3.5 fill calibration (D-047): trade_through ≈ L3 FIFO (49 vs 52 maker
  fills), conservative; queue_l1 mildly optimistic.
- Data cached: 238 RTH trade days 2024-11..2025-09; ES hourly bars 2010-06..2025-09 (both ranks).
  Holdout frozen at 2025-10-03. Next: H-007 confirmation needs the user (holdout unlock /
  paper trading); coverage audit done (H-007 sample complete, 122/122); next R6.3 more ideas.
- **User target (D-048): ~15%/yr = Sharpe ≥ 1 at 15% vol** → [return-targets](../04-backtesting/return-targets.md).
  R7: 26 CME futures daily bars 2010-2025 cached (`data/universe.py`, `portfolio/`). H-022 trend+carry
  portfolio OOS −4.3%/yr (Sharpe −0.28); trend252 in hindsight 0.41 (D-049).
  User chose option 1 → **H-023** combined book (trend252 + H-007) registered with holdout criteria (D-050);
  hindsight-only: $1M 8.4%/yr Sharpe 0.53, $100k 2.3%/yr (integer contracts). **Next: holdout run needs the
  user's go** (`research/HOLDOUT_UNLOCK`, data ≈ $0.27).
- **Budget (D-019/D-048):** $125 credit approved; code cap $123; **spent ≈ $121.2** (+ ≤ $0.15 possible
  partial charges from 3 interrupted streams) → ≈ $3.7 of credit left. No more data purchases without the user. One year cannot pass G7.

## Open questions
- Recheck detector calibration (D-018) on more MBO days (needs the user's OK for MBO)
- CME fees after 2026-10-01 (SER #9799) → [costs](../02-market-structure/costs-fees-slippage.md)
- Roll rule for NQ/MES/MNQ not measured (ES only)

## Key numbers
- ES: tick 0.25 = $12.50. Fees about $2.26/side, $4.51 per round turn. Market-in/market-out ≈
  **1.36 ticks ≈ $17** before slippage.
- Latency 100 ms (stress 250/500). Fees ×1.5 and ×2 stress. Gates G1–G11 (≥ 200 trades,
  DSR ≥ 0.95, PBO ≤ 0.10, plateau, MC 5th percentile > 0, cluster medoid) + G12 placebo p ≤ 0.05.

## Where things are
- [decisions](decisions.md) · [journal/](../journal/) · [inbox/](../inbox/) · [results/](../results/README.md) · [roadmap](../06-roadmap.md)
- Code: `data/` (Phase 1) · `features/` (Phase 2) · `backtest/` (Phase 3) · `scripts/` · `config/` · `tools/vault.py`
- Routine: `research/ROUTINE.md` (rules) · `research/QUEUE.md` (work) · `research/CHANGELOG.md`
