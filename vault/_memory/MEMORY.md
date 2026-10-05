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

## Current state (2026-10-05, session 6)
- Phases 0–2 done. **Phase 2 features validated on the first real day** (2024-03-05, ES), incl.
  a visual check ([day-check](../results/day-check-2024-03-05-rth.md)).
- **Real data** (key works; `DATABENTO_API_KEY` is an environment variable). Spent **≈ $122.4** (see Budget below)
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
  not promising (t 0.51). Only H-007 showed timing beyond drift (p 0.063) - weakened by D-052/D-056. H-015 macro days: 0/12, placebo p 0.53.
  H-016 pre-holiday 0/12; H-017 OPEX week 5/12 (placebo p 0.43); H-018 Monday reversal 5/12
  (placebo p 0.24 vs Tue-Fri) - all closed (D-039). H-019 month-end
  rebalancing: run 1 buggy (dropped 2/3 of months, looked good), fixed re-run 1/12 → closed (D-041/42).
  Lesson: check event coverage first. H-020 vol-managed long: 8/12 gates (most) but placebo p 0.118,
  79 trades → not promoted (D-044). H-021 buy-the-selloff 3/12, placebo p 0.99 (D-046).
  Total hypothesis trials: 245. R3.5 fill calibration (D-047): trade_through ≈ L3 FIFO (49 vs 52 maker
  fills), conservative; queue_l1 mildly optimistic.
- Data cached: 238 RTH trade days 2024-11..2025-09; ES hourly bars 2010-06..2025-09 (both ranks).
  Holdout frozen at 2025-10-03. Next: H-007 confirmation needs the user (holdout unlock /
  paper trading); coverage audit done (H-007 sample complete, 122/122); next R6.3 more ideas.
- **User target (D-048): ~15%/yr = Sharpe ≥ 1 at 15% vol** → [return-targets](../04-backtesting/return-targets.md).
  R7: 26 CME futures daily bars 2010-2025 cached (`data/universe.py`, `portfolio/`). H-022 trend+carry
  portfolio OOS −4.3%/yr (Sharpe −0.28); trend252 in hindsight 0.41 (D-049).
  User chose option 1 → **H-023** combined book (trend252 + H-007), pre-registered (D-050). **Holdout run once
  2026-10-04 → CONFIRM by the fixed rule (D-052)** → [h023-holdout](../results/h023-holdout.md): book +8.7%,
  Sharpe 0.72 on $1M; trend sleeve +$108k (Sharpe 0.89, spread across sectors), FOMC sleeve −$18k (8 trades);
  $100k +1.6%. Weak evidence (1 y, Sharpe SE ~1). **Holdout is spent and re-locked**: never select/tune on it;
  future confirmation = forward data after 2026-10-04.
- **Routine resumed active research (D-051, user 2026-10-04):** QUEUE section R8 ($0 cached data; cross-sectional
  carry/momentum, basis-momentum, FOMC replication on other index futures, sleeve combiner, order-flow imbalance).
  R8.1 done: `portfolio/signals.py` (BUILDERS, cross_sectional, momentum_score) + `run_portfolio.py --hypothesis`.
  H-024 cross-sectional carry: not promising (1/12, OOS −1.5%/yr, placebo p 0.57; D-053). H-025 cross-sectional
  momentum: not promising (1/12, −1.3%/yr, placebo p 0.40; D-054). H-026 basis-momentum: 4/12, +3.1%/yr,
  Sharpe 0.20, placebo p 0.13 (best of R8, not promoted; D-055). H-027 FOMC replication on NQ/RTY/YM: does
  not replicate (t 1.13, placebo p 0.17) → H-007 no longer a candidate (D-056). R8.6 done: `portfolio/combine.py` (causal inverse-vol/ERC
  sleeve weights + vol target). H-028 trade-flow imbalance (238 RTH days): 0/8 variants
  > 0, closed (D-057). R8.8 done → [next-ideas-r9](../04-backtesting/next-ideas-r9.md):
  forced scheduled flows outside equities. R9 run in parallel (user asked for 3 at once):
  H-029 GSCI roll 1/12 (D-059); **H-030 Treasury long into month-end 9/12 gates - strongest ever, not promoted**
  (OOS t 2.2, all pre variants t~3, scales with duration, stable both halves, not a roll artefact; D-060) →
  [h030-report](../results/h030-report.md); H-031 auction cycle 4/12 (D-061). Next: H-030 confirmation (UB/TN
  replication ~$0.1 needs the user's OK; paper tracking). R9.1 done: tick runner now measures G12 (`research/placebo.py`). R9.5 done: `scripts/paper_track.py` (trend252 + H-030 pre|3|all ledger, replay-tested;
  forward running needs data = user's OK). **H-032 CONFIRMS H-030 on TN/UB** (never used before;
  t 4.5, drift-neutral t 5.1, 15/16 yrs; D-062) → [h032-report](../results/h032-report.md). Working book trend252 + H-030 at
  15% vol: hindsight 12.7%/yr, Sharpe 0.82 → [combined](../results/combined-trend-h030-descriptive.md). **Forward paper tracking LIVE** from 2026-10-05 (ROUTINE step 2b,
  `paper_track.py --live`, D-063). $100k whole contracts, last 5 y: book +3.9%/yr (H-030 +4.7%, trend −0.8%: trend
  sleeve untradeable at $100k) → [100k](../results/combined-book-100k-last5y.md). Micros (R9.8): $100k book +5.6%/yr last 5 y.
  H-033 post-month-end short: does not confirm (D-064). User: keep going until expectations are exceeded → QUEUE R10
  → R10 run in parallel: H-034 turn-of-month 3/12 (drift), **H-035 rebalancing pressure 6/12, placebo
  p 0.047 → forward watch sleeve** (paper_track `h035_watch`), H-036 vol-managed trend no gain (D-065). R11: H-037 FX month-end 5/12 → NOT confirmed on 6N/6M
  (H-040); H-038 seasonality 0/12; H-039 quarter-end USD 1/12 (D-066). R12: H-041 trend252 on 12 unseen markets: +3.0%/yr, Sharpe 0.19,
  placebo p 0.27 → does not confirm (weak positive; corr 0.61 with the 26-market book; D-067). R13: H-042 dropped (month-end effect = ~2 bp parallel yield decline,
  D-068); H-043 mid-month 15th: does not confirm (D-069). R13.3 done: `scripts/paper_summary.py` (monthly,
  ROUTINE 2b; fixed book weights). H-030 cost-robust (break-even
  5-9 ticks/side). D-070: diminishing returns on cached data → paper tracking is the main work; new data needs the user. Asked the user about forward paper tracking (R8.9, cents/day).
- **R15 (user 2026-10-05: "continue search any concept or strategies"): two published FOMC effects CONFIRMED** (fixed
  rules from papers, 1 trial each, never tested here on rates/FX): **H-044** long Treasuries F-2→F+1 (Hillenbrand 2025):
  t 3.63, drift-neutral 4.62, placebo p 0.002, stronger post-2017 (D-071). **H-045** short USD on FOMC day (Mueller et
  al. 2017): t 3.44, p 0.000, but 2010-14 negative (D-072, lower confidence). Paper sleeves h044/h045 live; **book v2**
  (trend + H-030 + H-044 + H-045, weights fixed, D-073): descriptive Sharpe 0.96 ≈ 14%/yr at 15% vol, last 5 y 0.74
  → [fomc-sleeves-and-book](../results/fomc-sleeves-and-book.md). First forward FOMC window: 2026-10-28 (enter 10-26).
  R15.4 H-046 CFTC hedgers' liquidity provision (KRT 2020, tradable part): does not confirm (t −0.73, D-074;
  `data/cot.py` loader kept). Next: R15.5 more scheduled-event papers (fixed rule, one trial each).
- **Budget (D-019/D-048):** $125 credit approved; code cap $123; **spent ≈ $122.4** (+ ≤ $0.15 possible
  partial charges from 3 interrupted streams) → ≈ $2.5 of credit left. No more data purchases without the user. One year cannot pass G7.

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
