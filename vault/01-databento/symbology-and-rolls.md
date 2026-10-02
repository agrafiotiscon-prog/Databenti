---
type: topic
tags: [databento]
updated: 2026-10-02 (session 5)
---
# Databento symbology and contract rolls

## Symbology types [doc]
- `raw_symbol`: exchange symbol, e.g. `ESM4`. CME mostly uses a **1-digit year**, but some
  recently listed contracts use 2 digits (`NGN25`). **Never construct raw symbols by string
  formatting.** Resolve them.
- `instrument_id`: numeric ID.
- `parent`: `ES.FUT` (all ES futures **and calendar spreads**, e.g. `ESH4-ESZ4`) or `ES.OPT`.
- `continuous`: `[ROOT].[RULE].[RANK]`. **Prices are the original, unadjusted prices.**
  Databento does not back-adjust.

| Rule | Meaning |
|---|---|
| `c` (calendar) | Rank by **nearest expiration**. Rolls only **after the contract expires**. |
| `n` (open interest) | Rank by **previous day's** open interest. |
| `v` (volume) | Rank by **previous day's** volume. |

`symbology.resolve` is free and returns `[{d0, d1, s}]` date ranges (UTC dates, `d1` exclusive).
Databento's docs show `ES.c.0` → instrument 206299 until **2023-03-19**. ESH3 expired on Friday
2023-03-17, so the continuous symbol stayed on the expiring contract through expiry. [doc]

## The problem with `ES.c.0` (a change from the original brief)
Market convention says ES liquidity moves on **the Thursday eight days before the third-Friday
expiry**. [doc: broker and education sources; **contradicted by our data**, see below: the
real crossover is the Monday of expiry week] Either way `ES.c.0` keeps pointing at the
expiring contract until it expires, while its volume collapses. Order-flow features computed on that contract during
the roll window (thin book, spread widening, roll-related spread trades) would be garbage.

`ES.v.0` follows volume, but uses the **previous day's** volume, so it switches one day after
the liquidity moved. That causes no lookahead, but it does put one bad day per quarter into the
data.

## Resolved: when does ES liquidity actually cross? [data, session 5]
Measured with `scripts/roll_history.py` → [roll-history-ES](../results/roll-history-ES.md)
(daily volume of `ES.c.0` vs `ES.c.1`, 27 rolls 2019-03..2025-09, weekend bars folded into
Monday's session):
- **2022-06 → 2025-09: 14 rolls in a row crossed on the Monday of expiry week** (expiry − 4).
- 2019 → 2022-03: usually the **Friday before** expiry week (expiry − 7); 2020-03 and 2020-06
  were already Monday.
- The "roll Thursday" convention (expiry − 8) was **never** the crossover day in this sample.
  Spread legs print the same quantity in both outrights, so they cancel out of "which contract
  trades more". The earlier [inferred] explanation (spread legs inflate the expiring contract)
  was therefore not the cause.
- Cross-checks: the 2024-03 RTH trades check ([verify-roll-2024-03](../results/verify-roll-2024-03.md))
  shows c.0 ahead 3:1 on Fri 03-08 and c.1 ahead from Mon 03-11. Databento's March 2025
  `ES.v.0` example (switch visible on 3/19 = one day after a Monday-3/17 crossover, since `v`
  uses the previous day) also fits.

| Rule | Wrong-contract days (27 rolls) | Last 14 rolls |
|---|---|---|
| **expiry − 4 (Monday of expiry week), our rule** | **11** | **0** |
| expiry − 7 (Friday before) | 16 | 14 |
| expiry − 8 (roll Thursday) | 43 | 28 |
| previous-day volume (`ES.v.0`-like) | 27 | 14 |

Decision: [D-016](../_memory/decisions.md). Re-run the script yearly; if the regime moves again,
change `DEFAULT_ROLL_DAYS_BEFORE_EXPIRY`.

## Our policy
1. **Contract choice per CME trading date** (the session starting 17:00 CT the day before):
   - Before the Monday of expiry week: front contract (`ES.c.0`).
   - From the Monday of expiry week through the expiry Friday: next contract (`ES.c.1`).
   - The rule uses only the calendar, so it causes no lookahead. Implemented in
     `data/contracts.py`.
2. A **whole session uses one contract.** Order-flow state (cumulative delta, profile, book) is
   never stitched across contracts.
3. **Cross-check** the rule against free `symbology.resolve` output for `ES.v.0`. They should
   agree except on the roll day and the day after.
4. For multi-day *price-level* comparisons (prior-day POC, VWAP of yesterday), use
   **difference back-adjustment**. Measure the gap from both contracts at the same instant,
   for example both settlements on roll day from the `statistics` schema.
   **The backtester trades the real contract prices.**
5. **Expiry Friday:** ES stops trading in the expiring contract at the Special Opening
   Quotation (the morning of the third Friday). Our rule has already moved off it by then.
