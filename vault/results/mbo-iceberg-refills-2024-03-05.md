---
type: result
date: 2026-10-03
tags: [verification, phase-2, mbo, iceberg]
---
# How native iceberg refills appear in Databento MBO (2024-03-05 RTH, ES.c.0, warm book)

Routine item R2.2. Data: cached, $0. Classification from `features.book.annotate_mbo`.

**Pattern [data]:** `F` (fill on the resting order) → `M` on the **same order_id, same price,
same event**, raising the displayed size back up. No new order id and no `A` record.

| Measure | Value |
|---|---|
| `refill` records / distinct orders | 3,018 / 994 |
| refill in the same event as a fill of that order | **100%** |
| displayed part fully filled before the refill | 68% |
| refilled to the order's original displayed size | 72% |
| most common clip (displayed) size | **1 lot** (1,761 of 3,018), then 2, 3, 5, 4, 15 |
| refills per order | median 1, mean 3.0, max 80 |

Implications:
- `annotate_mbo`'s `refill` rule (same-price M after fills, new size > expected) matches the
  real pattern. Together with `exceeds_display` (hidden fills beyond the display, 832 rows; see
  [fill reconciliation](mbo-fill-reconciliation-2024-03-05.md)) it covers both ways a native
  iceberg shows itself. Refills behave like a size increase, so the order goes to the **back of the
  queue**, which is how our `OrderBook` treats it (CME rule [doc]).
- **Synthetic icebergs are a different story:** 156,235 of 851,920 full fill-removals are followed
  within 1 ms by a same-size add at the same price, and **none of them in the same event**. That is
  ordinary order flow (other participants joining the level), and it cannot be told apart from
  a trader's algo re-posting. This is why the synthetic-iceberg detector fires ~45k times per
  day (R2.3).
- Native icebergs are mostly 1-lot clips. A "big hidden order" signal should weight by
  `fill_hidden` volume and refill count, not by the number of orders detected.
