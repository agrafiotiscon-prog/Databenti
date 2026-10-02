---
type: topic
tags: [market-structure]
updated: 2026-10-02
---
# ES (and NQ) contract, sessions, matching

## Contract specs
| | ES | MES | NQ | MNQ |
|---|---|---|---|---|
| Multiplier | $50 × index | $5 × index | $20 × index | $2 × index |
| Tick | 0.25 pt = **$12.50** | 0.25 pt = **$1.25** | 0.25 pt = **$5.00** | 0.25 pt = **$0.50** |
| Months | H, M, U, Z (quarterly) | same | same | same |
| Expiry | 3rd Friday of the contract month; final settlement at the Special Opening Quotation that morning | same | same | same |
| Roll day (market convention) | **Thursday, 8 days before expiry** | same | same | same |
| Matching algorithm | **FIFO** (CME algorithm "F") | FIFO | FIFO | FIFO |
| Exchange margin (mid-2026, varies) | about $22k–24k maintenance | about 1/10 of ES | — | — |

Sources: Databento futures docs and the CME matching-algorithm blog; broker spec pages; a
margin-page search in 2026-10. **Margins change with volatility. Check with your broker.**

## Session times (US/Central, DST-aware)
- Globex: **Sunday–Friday 17:00 → 16:00 CT**, with a **daily maintenance halt 16:00–17:00 CT**.
  Databento's `status` example shows ES `is_trading` going N at 22:00 UTC and Y at 23:00 UTC
  in winter. [doc]
- The old **15:15–15:30 CT halt was eliminated on 2021-06-28**. [doc: CME SER, AMP notice]
  Data before that date has a 15-minute gap, which needs no special code.
- **RTH = 08:30–15:00 CT** (cash equity session 09:30–16:00 ET). ETH = the rest.
- **Holidays and early closes:** for example, Christmas Eve 2024 halted at **18:15 UTC = 12:15
  CT**, and Christmas and New Year's Day were closed. [doc: Databento status example]
  → Take the real schedule from the **`status` schema** (cheap), not from a hard-coded calendar.
- Pre-open and the daily pause can show **locked or crossed books**. Orders are accepted but not
  matched until the uncrossing, and the uncross trades have `side = N`.
- Price limits and circuit breakers exist (coordinated with the equity market). Limit values
  are published in the `statistics` schema. Halts appear in `status`.

## Icebergs on CME (relevant to Phase 2 feature 7) {#icebergs}
- **Native (exchange-held) icebergs:** each refreshed clip **keeps the same OrderID**, but gets a
  new priority (back of the queue). Trades against it can exceed its displayed size. In MBO this
  looks like `F` sizes larger than the visible size and/or an `M` increasing size on the same
  `order_id` right after fills. [doc: CME MBO FAQ; paper: Zotikov & Antonov 2019]
- **Synthetic (ISV-held, e.g. platform-managed) icebergs:** each clip is a **new order**. They
  can only be inferred: a new `A` at the same price, side and (usually) size, arriving within a
  few ms after the previous clip filled or was removed. [paper]
- **Prevalence in ESU19:** native about **4% of traded volume** (0.06% of orders). Synthetic
  about **3–14% of volume**, depending on detector parameters. Median total iceberg size was
  **6 contracts**. [paper] Most icebergs are small. A "big hidden buyer" is rare.

## Implied liquidity
CME's implied engine creates outright liquidity from calendar spreads. It is **not in MBO**.
Implied trades can have `side = N`. The effect is largest in roll week, which our roll rule
mostly avoids.

## Spoofing
Spoofing is illegal under Dodd-Frank §747, and ES has had major enforcement cases (e.g., Sarao).
This project only **detects spoof-like patterns as a research feature**. It never places such
orders. Academic detectors stress the **distance from the touch** and the order's **lifetime**.
