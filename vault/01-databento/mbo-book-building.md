---
type: topic
tags: [databento]
updated: 2026-10-02
---
# Databento MBO: building the book correctly (CME)

## Action semantics [doc]
| Action | Effect on book |
|---|---|
| `A` Add | Insert the order at the **back** of its price level's queue. |
| `C` Cancel | Reduce the order's size by `size`. If it reaches 0, remove the order (and the level if it is empty). |
| `M` Modify | Change price and/or size. **A price change or a size *increase* loses priority** (the order moves to the back). A size decrease keeps priority. An `M` for an unknown `order_id` is treated as an Add. |
| `R` Clear | Remove every resting order for the instrument. |
| `T` Trade | Aggressor trade summary. **Does not change the book.** |
| `F` Fill | A resting order was (partly) filled. **Does not change the book.** |
| `N` None | No book effect. It can carry `F_LAST`. |

Databento's reference implementation (the "Queue position" tutorial) applies only `A/C/M/R` and
ignores `T/F/N`.

## CME specifics [doc]
- **FIFO priority equals message order.** Databento does not expose CME tag 37707
  (MDOrderPriority), but messages for one `instrument_id` are never reordered, even when
  timestamps are equal. Process records **in file order** and never re-sort within a day.
  *(Phase 1 fix: the loader no longer re-sorts concatenated chunks.)*
- **`F_LAST` per instrument.** CME sets end-of-event once per multi-instrument event; Databento
  sets `F_LAST` on the last record *per instrument*. Between records without `F_LAST` the book is
  mid-update, and the apparent BBO may already have traded through. **Sample book state only
  right after an `F_LAST` record.**
- **Trade Summary normalization.** Each CME trade summary becomes one `T` record (with the
  aggressor's `order_id` if one is defined), followed by one `F` record per passive order hit.
  If the aggressor itself was resting (a modify that crossed), it also gets an `F`.
- **Implied trades** can have `side = N`.
- **Weekly MBO snapshot.** At the start of the weekly session (Sunday), CME replays orders that
  persist from the prior week (GTC orders, for example). Databento re-sorts them into priority
  order and sets `F_SNAPSHOT | F_BAD_TS_RECV`.
- **Daily synthetic snapshot at 00:00:00 UTC, Monday to Friday.** Databento injects a `R` clear
  followed by an `A` for every resting order, in priority order, flagged `F_SNAPSHOT`
  (`F_BAD_TS_RECV` too). It is included whenever a historical request spans midnight UTC.
  Snapshot `ts_event` values are the orders' original times. Their `ts_recv` is the snapshot time.
- Before the open and during the daily pause, a **locked or crossed book is normal** because
  orders are accepted but not matched until the uncrossing.
- Implied orders are **not** in MBO. CME publishes implied depth only via MBP (2 levels).
  Databento's `cmbp-1` merges it in. For outright ES, implied liquidity matters mostly in roll
  week through calendar spreads.

## Consequences for our code

1. **Cache by UTC day.** Each UTC-day MBO file starts with a full snapshot, so it is
   self-contained. Our cache layout (`<schema>/<symbol>/<YYYY-MM-DD>.dbn.zst`) already does this.
   A CME session (17:00 CT → 16:00 CT) spans two UTC days. Rebuild the book from the earlier
   day's 00:00 UTC snapshot.
2. **Exclude `F_SNAPSHOT` records from every activity feature.** Count them in the book state
   only. Otherwise every midnight looks like a burst of thousands of new orders (spoof and
   iceberg detectors would fire).
3. **Separate fills from cancels. [inferred, verify on real data]** Because `T/F` do not touch
   the book, a resting order that gets fully filled must be removed by a later `C` (or reduced
   by an `M`) in the same event. A naive "cancel" counter will therefore count **fills as
   cancels**. Implemented rule (`features/book.annotate_mbo`): each order keeps an
   *unexplained fill* balance, which can carry across events. `C`/`M` reductions covered by
   that balance are fill-removals. A same-price `M` that leaves more than `displayed − filled`
   is an iceberg **refill**. `fill_explained` must sum to the fill volume, and
   `scripts/verify_data.py` checks this on real data.
4. **Native icebergs show the same `order_id` refilling.** See
   [ES contract](../02-market-structure/es-contract-and-sessions.md#icebergs). A Fill larger than
   the order's displayed size, or a size-increasing `M` right after fills, identifies a native
   iceberg.
5. **`F_MAYBE_BAD_BOOK`** means book-dependent features are invalid until the next `R`
   or snapshot. Mark those intervals and exclude them.
6. **`hftbacktest`'s Databento converter raises on `action == 'N'`** (verified in its source,
   v2.4.4). Filter out `N` records before converting.

## Reference implementation
Databento's tutorials "Limit order book construction", "State management of resting orders" and
"Queue position of an order" give a `Book` class using `SortedDict` price levels with per-level
order lists. Queue position is the sum of sizes ahead of our `order_id` at that level. We will
port that logic into `features/book.py` (Phase 2) and test it on hand-made event sequences
before trusting it on real data.

## Queue estimation without MBO (from Databento's tutorial) [doc]
With only MBP data, assume a cancel at our level happens *ahead of us* with probability `p(x)`,
where `x` is our relative position. Cancels are more likely *behind* us, because front orders
value their priority. Databento's bias family:
`p_k(x) = x^(1+k)` for `k ≤ 0` (and `1-(1-x)^(1-k)` for `k > 0`).
In their ES example `k ≈ -0.8 … -0.95` tracked the true MBO queue much better than uniform
(`k=0`). hftbacktest's `PowerProbQueueModel` is the same idea.

## Real-data findings (session 5, 2024-03-05) [data]
- Databento's MBO snapshot is at **00:00 UTC of each daily file** only. Replaying a time slice
  loses the resting book (7,828 unknown orders in RTH), so always replay from the snapshot →
  [mbo-warmup-2024-03-05](../results/mbo-warmup-2024-03-05.md).
- Fill accounting is exact once two cases are recorded: hidden iceberg reserve (F beyond the
  displayed size, then removal; 0.48% of fill volume) and orders modified into the market
  (F reported on the order *before* the M that moves it to the fill price; 0.12%) →
  [mbo-fill-reconciliation-2024-03-05](../results/mbo-fill-reconciliation-2024-03-05.md).
- Native iceberg refill = `F` then a same-price `M` on the **same order id in the same event**
  (100% of 3,018 refills; mostly 1-lot clips) → [mbo-iceberg-refills-2024-03-05](../results/mbo-iceberg-refills-2024-03-05.md).
