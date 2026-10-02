---
type: topic
tags: [databento]
updated: 2026-10-02
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
ES liquidity moves to the next contract on **roll day: the Thursday eight days before the
third-Friday expiry** (usually the 2nd Thursday of Mar/Jun/Sep/Dec). [doc: broker and
education sources] `ES.c.0` keeps pointing at the expiring contract for about **six more
trading days**, while its volume collapses. Order-flow features computed on that contract during
the roll window (thin book, spread widening, roll-related spread trades) would be garbage.

`ES.v.0` follows volume, but uses the **previous day's** volume, so it switches one day after
the liquidity moved (typically the Friday). That causes no lookahead, but it does put one bad
day per quarter into the data.

## Open question: when does ES liquidity actually cross? [conflicting evidence]
- **Market convention:** the roll Thursday, 8 days before expiry. Rollover calendars and broker
  education pages say volume shifts on that day.
- **Databento's own `ES.v.0` example (March 2025, `ohlcv-1d`):** instrument 5002 (ESH5, closing
  near cash) stayed volume-front through Tuesday 2025-03-18, with **723k contracts on Monday
  3/17**. The switch to 4916 (ESM5, about +50 pt carry) came on 3/19. Because `v` uses the
  previous day's volume, the crossover happened on Tuesday of **expiry week**, not on Thursday
  3/13.
- **Likely explanation [inferred]:** in roll week, calendar-spread trading (`ESH5-ESM5`)
  produces leg trades in *both* outrights, which inflates the expiring contract's raw volume
  even after directional trading has moved.
- **Resolution plan (Phase 1b, real data):** for each day of a roll window, compare the two
  contracts on *outright-only* activity: trades with side ≠ N, top-of-book depth, quote update
  counts, and spread width. Then set `roll_days_before` in `data/contracts.py` from the data.
  The parameter is configurable for exactly this reason.

## Our policy
1. **Contract choice per CME trading date** (the session starting 17:00 CT the day before):
   - Before the roll Thursday: front contract (`ES.c.0`).
   - From the roll Thursday through the expiry Friday: next contract (`ES.c.1`).
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
