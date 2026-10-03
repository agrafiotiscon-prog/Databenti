---
type: result
date: 2026-10-03
tags: [phase-5, audit, data-quality, D-042]
---
# Event-coverage audit of the bar modules (R6.7, after the H-019 data bug)

Trades found per variant vs. events expected on ES hourly bars 2010-06..2025-09 (3,943 dates, 3,816
with a 15:00 CT close, 184 months). Costs do not affect counts. [inferred] from
`strategies/*.trades` run on the cached bars; script kept in the session scratchpad only.

| Hypothesis | Found / expected | Why some are missing | Systematic? |
|---|---|---|---|
| **H-007 pre-FOMC** | **122 / 122** | none | - (**best candidate's sample is complete**) |
| H-015 macro days | 355-359 / 367 (both) | release on a day without the needed close | no |
| H-017 OPEX week | 180 / 184 | Friday or Thursday not a trading day (Good Friday, Juneteenth) | no |
| H-005 turn of month | 158-170 / 184 | month-ends on early-close days (e.g. day after Thanksgiving) and gaps | mild; H-005 is drift anyway (placebo p 0.84) |
| H-016 pre-holiday | 40-41 / 50 | pre-holiday days that close early (Dec 24, Jul 3) have no 15:00 close - as registered | by definition |
| H-018 Monday reversal | 613 / 717 Mondays (min 0 bp) | Monday after expiry Friday (c.0 has no 15:00 close on expiry day) and after Good Friday | yes, ~4 Mondays/yr; does not touch the conclusion (placebo vs Tue-Fri uses the same rule) |
| H-010 daily reversal | 3,627 / 3,816 | same post-expiry / post-holiday gaps | ~5%, no directional reason |
| H-009 overnight | 3,812-3,815 / 3,816 | - | no |

**Verdict:** no closed hypothesis changes. The only large, systematic drop was H-019 run 1
(63/183 months, D-041), already fixed and re-run. Known residual: modules using
`prev_date` + `sym_of` skip the Monday after a quarterly expiry; new modules should use
`bars_common.same_contract_px`.
