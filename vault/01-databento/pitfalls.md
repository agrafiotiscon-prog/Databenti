---
type: topic
tags: [databento]
updated: 2026-10-02
---
# Pre-flight checklist (run through before trusting any feature or backtest)

Data
- [ ] Data is from the MBO era (≥ 2017-05-21) if any L3 logic is used.
- [ ] One contract per session, chosen by the roll-date rule, not `ES.c.0`.
- [ ] Records processed **in file order**. No re-sorting within a UTC day.
- [ ] `F_SNAPSHOT` records excluded from activity counts (adds, cancels, order-size stats).
- [ ] Book read only after `F_LAST`.
- [ ] Fill-driven `C`/`M` separated from true cancels (reconciliation test passes on real data).
- [ ] `F_MAYBE_BAD_BOOK` intervals marked invalid.
- [ ] `side == 'N'` trades kept in a separate bucket (auction uncross, implied).
- [ ] `UNDEF_PRICE` (NaN after float conversion) handled.
- [ ] Holidays and early closes come from the `status` schema, not assumed.

Causality
- [ ] Every feature has `known_at` (`ts_recv` of its last input).
- [ ] Orders are placed no earlier than `known_at + latency`.
- [ ] Truncation and perturbation tests pass for every feature.
- [ ] Session or rolling statistics (VWAP, profile, z-scores) use only past data. The prior day's
      *completed* profile is fine; today's completed profile is not.
- [ ] No resampling with future-labelled bins.

Fills and costs
- [ ] Market orders fill at the opposite touch **at arrival time** and walk the book if size >
      touch size.
- [ ] Limit orders: the pessimistic mode requires a trade *through* the price. With MBO, use the
      FIFO queue (hftbacktest `L3FIFOQueueModel`).
- [ ] Stop orders become market orders when triggered. No fill at the stop price in gaps.
- [ ] Fees per side from `config/costs.yaml`, and results reported at 1×, 1.5× and 2× costs.
- [ ] Latency stress: 0, 100, 250 and 500 ms.

Statistics
- [ ] Trade count ≥ 200 (user rule). Flag below.
- [ ] Top-5-days PnL share and "drop the best N days" result reported.
- [ ] Trial count logged. DSR uses it.
- [ ] Holdout untouched (the loader refuses holdout dates without an unlock file).
