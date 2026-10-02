---
type: topic
tags: [order-flow]
updated: 2026-10-02
---
# Feature definitions (causal, testable): the spec for Phase 2

Conventions for all features:
- Input records are processed in file order. Time means `ts_recv` (see
  [causality](../01-databento/timestamps-and-causality.md)).
- Every output row has `known_at` = the `ts_recv` of the last input that affected it.
- Bars are left-closed and right-open: `[start, end)`. A bar's values are emitted at `end` and
  carry `known_at ≤ end`.
- State resets per **session** (ETH+RTH trading date) and per **contract**. A variant resets at
  the RTH open.
- `tick = 0.25`. Prices are floats rounded to the tick grid with `round(p / tick) * tick` to avoid
  float drift.
- Each feature gets: hand-made unit tests, a truncation test (no future data) and a perturbation
  test.

## 1. Footprint (from `trades` or `tbbo`)
For bar *b* and price *p*:
- `ask_vol[b,p]` = Σ size of trades with `side == 'B'` (buyer aggressor, lifted the ask)
- `bid_vol[b,p]` = Σ size with `side == 'A'` (seller aggressor, hit the bid)
- `unk_vol[b,p]` = Σ size with `side == 'N'` (auction uncross, implied). **Never assigned.**
- Optional: `ask_trades`, `bid_trades` counts, and the max single print.
Pitfall: some vendors reverse "bid/ask volume" naming. We use the definitions above everywhere.

## 2. Delta and cumulative delta
- `delta[b] = Σ_p ask_vol − Σ_p bid_vol` (unknown excluded, and `unk_vol` reported alongside).
- `cum_delta` = running sum within the session (ETH or RTH variant), reset at session start and
  never across contracts.
- Also per-trade cumulative delta at tick resolution, for intrabar divergence.
- Divergence: price makes a new N-bar high (or low) while `cum_delta` does not. Defined only on
  completed bars.

## 3. Volume profile and VWAP
- **Developing profile** for the session up to `known_at`: volume per price.
  - **POC** = the price with the max volume. Tie-break: the price closest to the session's
    volume-weighted mean, then the lower price. This is deterministic.
  - **Value area (70%)**: start at the POC and repeatedly add the **adjacent pair** of prices
    (the two above vs the two below) with the larger combined volume, until ≥ 70% of volume is
    included (the CBOT method). Equal → add above. Output VAH and VAL.
  - **Prior-session completed profile** (POC/VAH/VAL of yesterday) is allowed intraday.
    **Today's completed profile is not**, because that is lookahead.
- **VWAP**: running `Σ p·v / Σ v` from the session start. Bands are `VWAP ± k·σ`, where
  σ = sqrt of the running volume-weighted variance `Σ v (p − VWAP)² / Σ v`. k ∈ {1, 2, 3}.
- Variants: RTH-anchored and ETH-anchored. Both are reported, because they differ materially.

## 4. Diagonal and stacked imbalances (per footprint bar)
- **Buy imbalance at p**: `ask_vol[p] ≥ R × bid_vol[p − tick]` and
  `ask_vol[p] ≥ min_vol`. Compare diagonally: buyers lifting at *p* against sellers hitting one
  tick lower.
- **Sell imbalance at p**: `bid_vol[p] ≥ R × ask_vol[p + tick]` and `bid_vol[p] ≥ min_vol`.
- Zero denominators: count as an imbalance only if the numerator is ≥ `min_vol` (configurable).
  Default `R = 3.0` (300%), `min_vol = 10`.
- **Stacked**: ≥ `n_stack` (default 3) consecutive prices with same-direction imbalances. Output
  the zone `[low, high]` and the bar.

## 5. Order-book heatmap
- **MBP-10 version**: at each heatmap bucket end *t* (e.g. 1 s), take the book state from the last
  MBP-10 record with `ts_recv < t`, i.e. **as of** *t* with no forward fill from later records.
  Output (t, price, size, side).
- **MBO version (full depth)**: the book reconstructed from MBO (`A/C/M/R`, sampled after
  `F_LAST`), aggregated to price levels at bucket end. It supports levels beyond 10.
- Exclude `F_MAYBE_BAD_BOOK` intervals.

## 6. Absorption (hypothesis feature; definition must be falsifiable)
At level *L* (the touch at the time of the prints), over a rolling window *W* ending at `known_at`:
- **Sell absorption at bid L**:
  - aggressive sell volume printed at *L* within *W* is ≥ `V_min` (or a z-score ≥ z vs the
    trailing same-time-of-day distribution), **and**
  - no trade printed below *L* within *W*, **and**
  - the bid at *L* is still present at `known_at` (from TBBO/MBP-1: `bid_px ≥ L`).
  - MBO version: the passive volume filled at *L* exceeds the displayed bid size at the window
    start. That implies replenishment or icebergs.
- Mirror image for buy absorption at the ask.
- **Lookahead trap:** "price then failed to break *L*" must not use any data after `known_at`.
  The feature fires at the window end. What happens next is the *label*, not the feature.

## 7. Icebergs (MBO)
- **Native**: same `order_id` with (a) cumulative `F` volume > the maximum displayed size seen for
  that order, or (b) a size-increasing `M` within the same or the next event after an `F` that
  emptied the displayed size. Output the order_id, price, side, peak (display) size, cumulative
  executed so far, and refill count.
- **Synthetic (heuristic)**: after an order at price *p* and side *s* is fully removed by fills,
  a new `A` at the same *p* and *s* with the same size arrives within `dt` (default 5 ms;
  sensitivity 1–50 ms) → it is linked as the next tranche. This is noisy and is reported
  separately.
- Exclude `F_SNAPSHOT` adds. A snapshot re-add is not a refill.

## 8. Large-order and spoof-like behaviour (MBO)
- **Large** = order size ≥ max(`abs_min`, q99 of the trailing order-size distribution).
- **Spoof-like event**: a large order `A`dded at distance ≥ `d_min` ticks from the touch, then
  **truly cancelled** (not fill-removed, see
  [MBO note](../01-databento/mbo-book-building.md)) with
  lifetime < `T_max`, before the touch came within `d_near` ticks of it. Record the size,
  distance and lifetime, and the price move toward or away from it during its lifetime
  (descriptive only).
- The event is known **at the cancel time**, not at the add time. Using it at add time is
  lookahead.
- This is a label of *behaviour*, not *intent*.

## 9. Plotting (`scripts/plot_day.py`)
Plotly figure for one session:
- candles and VWAP bands
- cumulative delta subplot
- POC/VA lines
- imbalance markers
- absorption, iceberg and spoof-like markers at their `known_at`
- an optional heatmap layer

Markers are always drawn at `known_at`, so lookahead is visible to the eye.

## Implementation status (session 4, 2026-10-02)
| # | Feature | Module | Tests | Differences from the spec above |
|---|---|---|---|---|
| 1–2 | Footprint, delta, cum delta, divergence | `features/footprint.py` | hand-made + no-lookahead | none |
| 3 | Developing profile, session levels, VWAP + bands | `features/profile.py` | hand-made + no-lookahead | VWAP variance is computed on prices centred at the first trade, for numerical precision |
| 4 | Diagonal and stacked imbalances | `features/imbalance.py` | hand-made + no-lookahead | none |
| 5 | Heatmap (MBP-10 and MBO) | `features/book.py` | hand-made + no-lookahead | MBO heatmap rows get `consistent=False` if a bucket boundary falls inside an event. We never peek ahead to the event's end |
| 6 | Absorption | `features/absorption.py` | hand-made + no-lookahead | v1 uses trades/TBBO only. The MBO replenishment refinement is still to do |
| 7 | Icebergs (native, synthetic) | `features/iceberg.py` | hand-made + negative cases + no-lookahead | native also detects **same-size refills** via fill accounting (see below) |
| 8 | Spoof-like | `features/spoof.py` | hand-made + negatives + no-lookahead | orders that are price-modified or traded are dropped; non-snapshot clears drop all tracking |
| 9 | Day viewer | `scripts/plot_day.py` | smoke test | markers are drawn at `known_at` |

**Fill accounting (`annotate_mbo`).** F records don't change the book, so a native iceberg that
refills to the *same* displayed size would look like a no-op modify. Each order therefore
carries an *unexplained fill* balance:
- A later C/M that reduces the order by that amount is fill-driven (`fill_removal` /
  `modify_down_fill`).
- A same-price M leaving more than `displayed − filled` is a `refill`.
- `fill_explained` records how much fill each record accounts for. On real data,
  `sum(fill_explained)` should equal the resting-fill volume. `scripts/verify_data.py`
  reports that ratio.

**Causality safeguard:** `tests/causality.py` truncates and perturbs the data after random cut
times. Two deliberately leaky features (today's completed POC, and a centred moving average) are
tests that **must fail** it, and they do. MBO causality tests assert that the fixture produces
output, so the check can't pass vacuously.
