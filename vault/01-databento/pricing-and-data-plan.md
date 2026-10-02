# Pricing and the data plan

## How Databento charges [doc]
- **Usage-based:** $/GB of **uncompressed DBN** size. Metadata, symbology and `get_cost` are
  free. New accounts get **$125 in credits** (they expire after 6 months).
- **Streaming (`timeseries.get_range`) is billed every time.** Batch downloads are billed once
  and can be re-downloaded for 30 days. → **We cache every byte locally** (already done in
  Phase 1).
- **CME plans (pricing page, read 2026-10):**
  | Plan | Price | Historical included |
  |---|---|---|
  | Usage-based | pay per GB | anything, priced per GB |
  | Standard | **$199/month** | 16+ years of L0 (OHLCV, definitions, statistics, status), **1 year of L1** (trades, TBBO, MBP-1, BBO), **1 month of L2/L3** (MBP-10, MBO); pay as you go for more; includes live data |
  | Plus | $1,750/month | 16+ years of L1 |
  | Unlimited | $4,500/month | 16+ years of everything |

- MBO and MBP-10 are by far the largest schemas. Trades and TBBO are small. We never guess the
  price: `get_cost` is always called first, and the $5 guard stays.

## Consequence: a two-tier research design (changed from the original brief)
The brief assumed MBO-based queue fills everywhere. With MBO history costly and only one month
in the Standard plan, that would mean **few months of data, too few trades, and no statistical
power.**

| Tier | Data | Span | Purpose |
|---|---|---|---|
| A: research | `trades` + `tbbo` (or `mbp-1`) + `ohlcv-1m` + `status` + `statistics` + `definition` | **years** (MBO-era 2017+ preferred) | Footprint, delta, profile, VWAP, imbalances, absorption (trade-based), signal discovery, walk-forward |
| B: fill calibration | `mbo` (+ `mbp-10`) | **recent weeks to months** | Exact FIFO queue fills via hftbacktest; measure how optimistic tier A's fill rules are; markouts and adverse selection |
| C: MBO-only features | `mbo` | same window as B | Icebergs, spoof-like behaviour, full-depth heatmap. **Statistical power is limited and will be flagged.** |

Order of purchase: (1) a cost dry run for every schema over 2–3 days, (2) a few days of all
schemas to build and validate features, (3) months or years of tier-A data only after
features are tested.

## Size intuition [inferred]
One MBO record is 56 bytes. ES front month generates millions of book events per day. The
exact price comes only from `get_cost`; expect MBO to cost roughly **two orders of magnitude**
more than trades for the same span.
