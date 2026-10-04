---
type: result
date: 2026-10-04
tags: [phase-5, leaderboard, gates]
---
# Hypothesis leaderboard (each evaluated exactly once; gates G1–G11 on out-of-sample data)

Total hypothesis trials logged: **227** (every DSR uses this global count). "Best" = most gates
passed out of sample; **no hypothesis passes all 11, so none is promoted.**

**Holdout confirmation (D-052):** [H-023](h023-holdout.md) (trend252 portfolio + pre-FOMC sleeve, chosen in hindsight
and pre-registered in D-050) was run once on the 2025-10..2026-10 holdout: **CONFIRM by its fixed rule** - book
+8.7%, Sharpe 0.72 on $1M; all profit from the trend sleeve (Sharpe 0.89), the FOMC sleeve lost (−$18k, 8 trades);
+1.6% at $100k. One year = weak evidence (Sharpe SE ~1). The holdout is now spent.

| Rank | Hypothesis | Data | Gates passed | OOS trades | OOS net | OOS t | Verdict |
|---|---|---|---|---|---|---|---|
| **1a** | [H-030](h030-report.md) **Treasury futures long into month-end** (last 3/5 days; ZN+ZB or all 4) | 15 y daily, ZT/ZF/ZN/ZB | **9/12** (most ever) | 472 | +$173,130 on $1M (+1.4%/yr at ~2% vol) | 2.21 (daily) | **strongest candidate, not promoted** (fails G3 DSR N=214, G5 plateau vs opposite-sign post variants, G11). All pre variants t~3, all post variants < 0; scales with duration (ZT 4 bp → ZB 27 bp); stable 2010-17 vs 2018-25; **CONFIRMED on TN/UB by [H-032](h032-report.md)** (t 4.5, drift-neutral t 5.1, 15/16 years; D-062) |
| 1b | [H-020](h020-report.md) volatility-managed long (63-day vol < 1-y median) | 15 y hourly | **8/12** (most) | 79 | +$182,206 | 3.89* | not promoted: **fails G12 (p = 0.118: regime series shifted in time with the same 57% long share earn nearly as much - mostly equity drift)**, G1 (79 multi-week holds), G3 (raw-N DSR 0.56). *per-trade t is inflated by month-long holds |
| **1** | [H-007](h007-report.md) pre-FOMC drift (24 h window) | 15 y hourly | **6/11** | 98 | +$21,296 | **1.95** | best candidate; placebo vs random days p = 0.063 (borderline); fails G1 (8 events/yr), G3, G5, G6, G10 |
| ~~1=~~ | [H-012](h012-report.md) FOMC-cycle even weeks | 15 y hourly | 6/11 | 226 | +$82,006 | 1.23 | **DEMOTED by placebo: 22/30 shifted calendars do as well (p ≈ 0.74) - the profit is equity drift, not a Fed effect**; passes G1 (226 trades); fails G3 (t < 2, DSR), G4/G10 (2-variant space), G6 (2023-24 = +$61k), G11 |
| ~~2~~ | [H-009](h009-report.md) overnight drift | 15 y hourly | 5/11 | 2,552 | +$68,478 | 1.05 | **placebo: overnight earns exactly its time share of the drift (p = 0.51)** - not promising: negative at 2 ticks/side, PBO 0.63; 9/13 years > 0, all variants > 0 |
| 3 | [H-010](h010-report.md) daily reversal | 15 y hourly | 5/11 | 1,074 | +$82,956 | 1.38 | not promising: 2020 alone +$75k (concentrated), 6/13 years |
| 3b | [H-014](h014-report.md) time-series momentum (long/short) | 15 y hourly | 4/12 | 361 | +$47,697 | 0.51 | not promising: 5/13 years, unstable lookback choice |
| 3c | [H-018](h018-report.md) Monday reversal (fade Friday's RTH move) | 15 y hourly | 5/12 | 329 | +$36,866 | 1.64 | not promising: **placebo p = 0.24 - fading on Tue-Fri does as well, so Monday is not special** (it is a subset of H-010); 2022 + 2025 = +$37k, 7/13 years |
| 3d | [H-017](h017-report.md) option-expiration week (Fri -> Thu, long) | 15 y hourly | 5/12 | 86 | +$26,312 | 0.83 | not promising: placebo p = 0.43 vs random non-OPEX 4-day holds (equity drift); PBO 0.88 |
| 4d | [H-019](h019-report.md) month-end rebalancing fade (ES-only proxy) | 15 y hourly | 1/12 | 86 | −$10,300 | −0.34 | not promising; placebo p = 0.41. Run 1 ([buggy](h019-report-run1-buggy.md), 63/183 months) showed 7/12 and p = 0.029 - an artefact of the data bug (D-041) |
| 4e | [H-021](h021-report.md) buy after a sharp 3-day decline (z <= -1.5/-2) | 15 y hourly | 3/12 | 94 | +$14,176 | 0.25 | not promising: **placebo p = 0.99 - random entry days do better**; 2018/2020/2022/2025 selloffs kept falling |
| 4f | [H-022](h022-report.md) **26-market** trend + carry portfolio, 15% vol target | 15 y daily, 26 futures | 2/12 | 9,690 contract trades | −$548k on $1M (−4.3%/yr) | −1.01 (daily) | not promising; best variant in hindsight (trend252) Sharpe 0.41; placebo p 0.96 |
| 4g | [H-024](h024-report.md) **cross-sectional carry**, 26 futures, within-sector / global ranks | 15 y daily, 26 futures | 1/12 | 7,118 contract trades | −1.5%/yr on $1M | −0.35 (daily) | not promising; equity+FX carry positive, commodity carry lost; placebo p 0.57 |
| 4h | [H-025](h025-report.md) **cross-sectional momentum** 6/12 m (skip 1 m), within-sector / global | 15 y daily, 26 futures | 1/12 | 10,193 contract trades | −1.3%/yr on $1M | −0.32 (daily) | not promising; PBO 0.45, placebo p 0.40; equity gain = likely drift |
| 3e | [H-026](h026-report.md) **commodity basis-momentum** (front − second contract, 6/12 m; time-series + cross-sectional) | 15 y daily, 12 commodities | 4/12 | 6,425 contract trades | +3.1%/yr on $1M | 0.71 (daily) | not promising but best of R8: all 4 variants > 0, 8/13 years; placebo p 0.13, PBO 0.53; energy −$395k |
| — | [H-027](h027-report.md) pre-FOMC drift **replication** on NQ/RTY/YM (daily, fixed) | 15 y daily | n/a (replication) | 122 events | +$143,874 | 1.13 | **does not replicate**: placebo p 0.17 vs random days; NQ t 1.83, YM 0.59, RTY 0.50 - lowers H-007's prior (D-056) |
| 4i | [H-028](h028-report.md) follow 5/15-min aggressor **trade-flow imbalance** for 15/30 min (ES RTH ticks) | 1 y ticks (238 days) | 1/12 | 171 | +$2,566 | 0.65 | insufficient data, and **0/8 variants net > 0 full-period** - OOS gain is fold-selection luck |
| 4j | [H-029](h029-report.md) front-run GSCI commodity index roll (near/far spread) | 15 y daily, 12 commodities | 1/12 | 1,123 | −$90,703 | −1.88 (daily) | not promising: all 4 variants < 0, 11/13 years < 0 (D-059) |
| 3f | [H-031](h031-report.md) Treasury auction cycle (short pre / long post) | 15 y daily + 1,012 auctions | 4/12 | 807 | +$30,591 | 0.50 (daily) | not promising: negative at stress, PBO 0.69; placebo pass = bond drift (D-061) |
| 2a | [H-035](h035-report.md) **month-end rebalancing pressure**: trade against MTD stocks-vs-bonds over the last 3/5 days (ES / 4 indices) | 15 y daily | 6/12 | 400 | +$315,850 on $1M (+2.5%/yr) | 1.25 (daily) | **passes G12 (p 0.047)**, all variants > 0; fails t/DSR, PBO 0.65, concentration, G7 - forward **watch sleeve** (D-065) |
| 3g | [H-036](h036-report.md) volatility-managed trend (21/63/126-day book vol target) | 15 y daily, 26 futures | 6/12 | 9,767 | +6.2%/yr at 16% vol | 1.34 (daily) | no gain over trend252; placebo p 0.25 |
| 4k | [H-034](h034-report.md) equity turn of the month (T-1 → 1st/3rd day) | 15 y daily | 3/12 | 422 | −$64,463 | −0.38 (daily) | equity drift: placebo p 0.88 |
| 4c | [H-016](h016-report.md) pre-holiday (long) | 15 y hourly | 0/12 | 31 | −$2,365 | −0.45 | not promising; ~2-3 events/yr, placebo p = 0.54 |
| 4b | [H-015](h015-report.md) macro-announcement days (jobs, CPI) | 15 y hourly | 0/12 | 165 | −$6,057 | −0.28 | not promising; placebo p = 0.53 (no premium vs random days) |
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

## Weaker calendar ideas H-016..H-018 (session 6, D-039)
Pre-holiday (Ariel 1990), option-expiration week (Stivers & Sun 2013) and the Monday reversal were
each run once with a G12 placebo. None beats its placebo: pre-holiday loses (31 trades), OPEX-week
holds earn no more than random non-OPEX holds (p = 0.43), and the Monday fade is no better than the
same fade on other weekdays (p = 0.24) - it is the H-010 daily reversal on a subset of days.
**H-007 remains the only candidate with timing beyond drift (p = 0.063), and it is not promoted.**

## H-019 and a data-bug lesson (session 6, D-041/D-042)
Run 1 of H-019 looked like the best result so far (7/12 gates, placebo p = 0.029) but used only 63
of 183 month-ends: months containing an early-halted holiday session or a quarterly expiry were
silently dropped. With the bug fixed (same contract's 15:00 closes; trading days = days with a
15:00 close) all 183 months trade and the effect is gone (t = −0.34, 6/13 years). Lesson: **check
event coverage (events found vs. events expected) before reading any result.**

## H-020 volatility-managed exposure (session 6 routine 13:16, D-044)
Passes 8/12 gates - more than any other hypothesis - but not the ones that separate an edge from
drift: random-timing placebo p = 0.118 (beats 88% of circular shifts of its own regime series, so a
weak volatility-timing signal may exist, as Moreira & Muir claim, but it is not significant), only
79 OOS trades, raw-N DSR 0.56. It is a long-only exposure rule, not a trading edge after drift.
Not promoted. **H-007 remains the strongest timing evidence (p = 0.063); neither passes G12.**
