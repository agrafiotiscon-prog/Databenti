---
type: topic
tags: [databento]
updated: 2026-10-02
---
# Databento: schemas, fields, flags

Dataset: **`GLBX.MDP3`**. Databento captures CME Globex MDP 3.0 over UDP multicast in Aurora (DC3).
Coverage starts in June 2010. **Full order-by-order (MBO) data starts on 2017-05-21.** Before that
date the data came from legacy FIX flat files: MBP-10 is the deepest schema, `ts_recv == ts_event`,
and every record has `F_BAD_TS_RECV` set. [doc]
→ **Implication:** MBO-based research cannot go back before mid-2017.

## Schemas relevant to us

| Schema | Level | What it is | Our use |
|---|---|---|---|
| `mbo` | L3 | Every add/cancel/modify/clear/trade/fill, keyed by `order_id` | Book reconstruction, queue position, icebergs, spoof-like behaviour, heatmap (full depth) |
| `mbp-10` | L2 | Top 10 levels (price, size, order count), one record per book update | Heatmap (10 levels), depth features |
| `mbp-1` | L1 | Every top-of-book update plus trades | Spread/touch at any time; market-order fills |
| `tbbo` | L1 | Every trade, with the BBO **just before** the trade | Cheapest way to get aggressor side, size, and touch per trade |
| `bbo-1s` / `bbo-1m` | L1 | BBO sampled every 1 s or 1 m, with last trade forward-filled | Cheap context; too coarse for fills |
| `trades` | L1 | Every trade (`side` = aggressor) | Footprint, delta, profile, VWAP |
| `ohlcv-1s/1m/1h/1d` | L0 | Bars | Context, roll checks, long history |
| `definition` | L0 | Instrument definitions (tick size, expiry, raw symbol) | Contract metadata |
| `statistics` | L0 | Settlement, cleared volume, open interest, session high/low, price limits | Settlement, OI, limits |
| `status` | L0 | Trading-state changes (scheduled and unscheduled) | **Real trading hours, holidays, early closes, halts** |
| `cmbp-1` / `cbbo-*` | L1 | Top of book merged with implied liquidity | Not needed for outright ES |

- MBP-1 is in *book-update space*, TBBO in *trade space*, and BBO in *time space*. TBBO can be
  derived from MBP-1, but not the other way around. [doc]
- The `trades` schema contains Trade records only, **no Fill records**. MBO adds a Fill record
  for every passive order hit. [doc]

## Common fields

| Field | Meaning |
|---|---|
| `ts_recv` | Databento capture-server receive time (ns, UTC). Hardware-timestamped and PTP-synced, with sub-µs accuracy. **Monotonic per symbol. This is the index and sort key.** [doc] |
| `ts_event` | Matching-engine receive time (CME tag 60 TransactTime). [doc] |
| `ts_in_delta` | `ts_recv - sending_time`, where sending time is CME tag 52. It can be negative. [doc] |
| `instrument_id` | Numeric ID. **Unique only within a day** in general; CME IDs are stable per contract in practice. [doc] |
| `price` | int64, 1 unit = 1e-9. `UNDEF_PRICE = INT64_MAX`. Prices can be negative for spreads. Our loader converts to float. [doc] |
| `size` | Quantity in contracts. |
| `action` | `A`dd, `C`ancel, `M`odify, clea`R`, `T`rade, `F`ill, `N`one. [doc] |
| `side` | Meaning depends on `action`. See below. |
| `flags` | Bit field. See below. |
| `sequence` | Venue sequence number. |
| `depth` | (MBP and trades) the book level the event occurred at. |

### `side` semantics [doc]
- **Trade (`T`)**: `A` = the aggressor was a **seller** (hit the bid). `B` = the aggressor was a
  **buyer** (lifted the ask). `N` = no side.
- **Fill (`F`)**: `A` = a resting **sell** order was filled. `B` = a resting **buy** order was
  filled.
- **Add/Modify/Cancel**: the side of the resting order.
- **`N` occurs for:** opening and closing auction trades, trades against non-displayed orders,
  **implied trades**, and off-exchange trades. In CME data the relevant cases are the
  open/re-open uncrossing and implied trades.
  → **Footprint and delta must keep a separate "unknown side" bucket and never guess.**

### `flags` bits [doc]
| Flag | Value | Meaning |
|---|---|---|
| `F_LAST` | 128 | Last record of an event for this `instrument_id`. **Read the book only after a record with `F_LAST`.** |
| `F_TOB` | 64 | Top-of-book message, not an order (not used in GLBX MBO). |
| `F_SNAPSHOT` | 32 | Record comes from a snapshot or replay. |
| `F_MBP` | 16 | Aggregated price-level message (not used in GLBX MBO). |
| `F_BAD_TS_RECV` | 8 | `ts_recv` is inaccurate. |
| `F_MAYBE_BAD_BOOK` | 4 | Unrecoverable gap in the channel; **book state is suspect until the next clear or snapshot**. |
| `F_PUBLISHER_SPECIFIC` | 2 | Venue-specific. |

Test flags with a bitwise AND (`flags & 128`), never with equality. [doc]

## Index timestamp rule [doc]
Every schema has one index timestamp. It is `ts_recv` if the schema has that field, otherwise
`ts_event` (as in OHLCV). Historical requests are **filtered on the index timestamp**, and start
and end are start-inclusive, end-exclusive. `DBNStore.to_df()` indexes the frame by it.

## Python client facts (databento 0.87, verified locally)
- `client.metadata.get_cost(dataset, start, end, symbols, schema, stype_in)` returns USD. Free.
- `client.timeseries.get_range(..., path=...)` streams to a DBN file. **Billed again on every
  call**, so cache everything.
- `client.symbology.resolve(...)` is free.
- `DBNStore.from_file(path).to_df(price_type="float", map_symbols=True)`.
- Batch jobs (`client.batch.submit_job`) are billed once and can be downloaded for 30 days.
  Recommended above about 5 GB. Databento announced changes to the batch API (blog,
  2026-08-26). **Re-read the batch docs before using batch.**
