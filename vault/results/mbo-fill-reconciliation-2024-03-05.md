---
type: result
date: 2026-10-02
tags: [verification, phase-1b, mbo]
---
# MBO fill reconciliation (2024-03-05 RTH, ES.c.0, warm book)

Question (MEMORY open question): does every resting-order fill (`F` record) show up as a size
reduction of that order? Expected ratio ≈ 1.0.

| Component | Lots | Share of F volume |
|---|---|---|
| F volume (resting fills) | 1,499,172 | 100% |
| explained by a C/M reduction of the same order | 1,490,095 | 99.395% |
| **hidden**: filled beyond the displayed size, then the order was removed | 7,226 | 0.482% |
| **aggressor**: F, then an M re-pricing the order to the fill price (same event) | 1,851 | 0.123% |
| unaccounted | **0** | **0.000%** |

Diagnosis (891 (event, order) groups with a gap; 0 orphan fills; every gap group has a
follow-up record for the same order in the same event):
- **Hidden (native iceberg reserve)** [data]: 782 groups where F > the C that removes the order;
  832 of 933 such F rows already had `exceeds_display`. This is real hidden liquidity, now
  recorded as `fill_hidden` on the removal row. Possible future feature.
- **Aggressor fills of modified orders** [data]: 109 groups; 105 have the M at exactly the fill
  price, e.g. a bid of 1 lot modified to 13 lots at the offer: 10 trade at once (CME reports
  them as `F` on that order, *before* the book update), 3 rest. Now kind `modify_price_fill`
  with `fill_aggressor`. These F rows no longer count as iceberg evidence (fills larger than
  the *old* displayed size were false `fill_exceeds_display` hits): native icebergs 1,544 → 1,540.
- The pre-existing code already reset the fill balance on a price modify, so no true cancel was
  mislabelled as a fill removal.

Answer: **the fill/cancel split is exact on real data** (ratio 1.0 with the two new
components). Full session (17:00 CT → 16:00 CT, [verify-2024-03-05](verify-2024-03-05.md)):
1,793,572 F lots = 1,783,088 explained + 7,853 hidden + 2,630 aggressor + **1 lot** unaccounted
(ratio 0.9999994; probably a balance wiped by the 00:00 UTC snapshot's `R` clear).
