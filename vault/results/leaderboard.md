---
type: result
date: 2026-10-03
tags: [phase-5, leaderboard, gates]
---
# Hypothesis leaderboard (each evaluated exactly once; gates G1–G11 on out-of-sample data)

Total hypothesis trials logged: **144** (every DSR uses this global count). "Best" = most gates
passed out of sample; **no hypothesis passes all 11, so none is promoted.**

| Rank | Hypothesis | Data | Gates passed | OOS trades | OOS net | OOS t | Verdict |
|---|---|---|---|---|---|---|---|
| **1** | [H-007](h007-report.md) pre-FOMC drift (24 h window) | 15 y hourly | **6/11** | 98 | +$21,296 | **1.95** | best candidate; placebo vs random days p = 0.063 (borderline); fails G1 (8 events/yr), G3, G5, G6, G10 |
| ~~1=~~ | [H-012](h012-report.md) FOMC-cycle even weeks | 15 y hourly | 6/11 | 226 | +$82,006 | 1.23 | **DEMOTED by placebo: 22/30 shifted calendars do as well (p ≈ 0.74) - the profit is equity drift, not a Fed effect**; passes G1 (226 trades); fails G3 (t < 2, DSR), G4/G10 (2-variant space), G6 (2023-24 = +$61k), G11 |
| ~~2~~ | [H-009](h009-report.md) overnight drift | 15 y hourly | 5/11 | 2,552 | +$68,478 | 1.05 | **placebo: overnight earns exactly its time share of the drift (p = 0.51)** - not promising: negative at 2 ticks/side, PBO 0.63; 9/13 years > 0, all variants > 0 |
| 3 | [H-010](h010-report.md) daily reversal | 15 y hourly | 5/11 | 1,074 | +$82,956 | 1.38 | not promising: 2020 alone +$75k (concentrated), 6/13 years |
| 4 | [H-011](h011-report.md) VWAP-deviation fade | 1 y trades | 3/11 | 256 | +$4,070 | 0.68 | not promising (0/4 variants > 0 full period) |
| 5 | [H-003](h003-report.md) last-hour momentum | 15 y hourly | 2/11 | 2,095 | +$7,177 | 0.21 | not promising |
| 6 | [H-004](h004-report.md) follow sweeps | 1 y trades | 2/11 | 202 | −$6,124 | −5.47 | not promising (reliably negative) |
| 7 | [H-006](h006-report.md) gap fade | 15 y hourly | 1/11 | 2,043 | +$20,761 | 0.59 | not promising (0/4 variants > 0 full period) |
| 8 | [H-005](h005-report.md) turn of month (**placebo p = 0.84**) | 15 y hourly | 1/11 | 124 | +$3,141 | 0.12 | no evidence |
| 9 | [H-013](h013-report.md) intraday periodicity | 15 y hourly | 1/11 | 637 | −$36,435 | −2.14 | not promising (reliably negative, 0/4 variants > 0) |
| 10 | [H-008](h008-report.md) 5-min imbalance fade | 1 y trades | 1/11 | 124 | +$653 | 0.18 | not promising (0/8 variants > 0) |
| 11 | [H-002](h002-report.md) momentum + delta filter | 1 y trades | 1/11 | 53 | +$348 | 0.08 | inconclusive |
| 12 | [H-001](h001-report.md) absorption + divergence | 1 y trades | 0/11 | 14 | −$113 | −0.37 | not promising (70/72 variants lose) |

## H-007: why it is the best candidate and why it is still not promoted
- Out of sample 2013-06..2025-09 (13 annual folds): +17.7 ticks/trade after pessimistic costs
  (≈ 2.36 ticks per round trip), positive in 8/13 years, stress (2 ticks/side, fees ×1.5)
  +$18.6k, MC 5th percentile +$11.8k, PBO 0.002, cluster-K DSR 0.98, survives +1 tick per side.
- It is a **pre-registered test of a published effect** (Lucca & Moench 2015) with a stated
  direction, not a mined pattern; only the original 24 h window works (the morning-only variant
  loses, −1.2 ticks/trade) and selection chose it in 10/13 folds.
- No announcement leakage out of sample: since 2013 statements are released at 14:00 ET =
  13:00 CT, exactly our exit; the 2011–2012 12:30 ET releases fall only in early training windows.
- Against it: only 98 trades (t = 1.95), gains concentrated in big-Fed years (2018, 2020,
  2022–2024; 2021 −$4.9k), raw-N DSR ≈ 0. After 126 trials this is **weak evidence**.
- **What would confirm or kill it** (needs the user): (1) one evaluation on the frozen holdout
  (from 2025-10-03, ~8 meetings; low power, but untouched); (2) forward paper trading of the
  fixed rule (enter at 13:00 CT the day before a scheduled statement, exit 12:59 CT on the day).
  No re-tuning on the development data.

## Co-leaders are both Fed-calendar effects (session 6, after H-012)
H-007 (pre-FOMC 24 h drift) and H-012 (even weeks of the FOMC cycle) each pass 6/11 gates with
pessimistic costs, both are pre-registered tests of published effects (Lucca & Moench 2015;
Cieslak, Morse & Vissing-Jorgensen 2019), and both are positive in 8–9 of 13 OOS years. They
overlap (H-007's entry day is in H-012's week 0). **A combined rule must NOT be built from this
observation on 2010–2025 data** (it was formed after seeing both results); the clean tests are the
frozen holdout and forward paper trading, which the user decides on. Neither is promoted.

## Placebo tests (session 6, routine 12:15) → [placebo-fed](placebo-fed.md)
- **H-007:** $324/trade on real FOMC days vs $50 on random non-FOMC days; one-sided p = 0.063.
  Still the best candidate, but borderline.
- **H-012:** with the FOMC calendar shifted by 1–30 trading days, 22 of 30 shifted calendars earn
  as much or more (median $117k vs $75k real). Its profit is long exposure in a rising market, not
  a Fed-cycle effect → demoted.
- Lesson → new gate **G12** (D-032, stricter only): long-only/calendar rules must beat a placebo or
  random-timing benchmark at p ≤ 0.05. Not yet measured for H-005, H-009 (also long-only) - their
  totals likely contain the same equity drift.
- **G12 for H-005 / H-009** → [placebo-bars](placebo-bars.md): turn-of-month holds earn −$28/trade vs
  +$293 for random 4-day holds (p = 0.84); overnight returns equal their 17/24 time share of the
  close-to-close drift (p = 0.51). Both totals are equity drift. **Only H-007 shows a timing effect
  beyond drift (p = 0.063).**
