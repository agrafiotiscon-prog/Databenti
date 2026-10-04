---
type: result
date: 2026-10-04
tags: [H-023, holdout, confirmation]
---
# H-023 holdout evaluation (single, D-050): **CONFIRM (paper trading next)**

Pre-registered criteria: CONFIRM if holdout net > 0 AND Sharpe >= 0.4 AND trend sleeve net > 0; REJECT if net <= 0.

```
{
 "1000000.0": {
  "trend": {
   "net": 108347,
   "ann_return_pct": 10.46,
   "ann_vol_pct": 11.79,
   "sharpe": 0.887,
   "max_dd_pct": -8.67,
   "days": 261
  },
  "fomc": {
   "net": -18071,
   "ann_return_pct": -1.74,
   "ann_vol_pct": 1.2,
   "sharpe": -1.451,
   "max_dd_pct": -2.27,
   "days": 261
  },
  "book": {
   "net": 90276,
   "ann_return_pct": 8.72,
   "ann_vol_pct": 12.04,
   "sharpe": 0.724,
   "max_dd_pct": -8.62,
   "days": 261
  },
  "fomc_trades": 8,
  "first": "2025-10-03",
  "last": "2026-10-02"
 },
 "100000.0": {
  "trend": {
   "net": 7721,
   "ann_return_pct": 7.45,
   "ann_vol_pct": 8.01,
   "sharpe": 0.93,
   "max_dd_pct": -5.72,
   "days": 261
  },
  "fomc": {
   "net": -6024,
   "ann_return_pct": -5.82,
   "ann_vol_pct": 4.01,
   "sharpe": -1.451,
   "max_dd_pct": -7.55,
   "days": 261
  },
  "book": {
   "net": 1698,
   "ann_return_pct": 1.64,
   "ann_vol_pct": 8.98,
   "sharpe": 0.183,
   "max_dd_pct": -8.62,
   "days": 261
  },
  "fomc_trades": 8,
  "first": "2025-10-03",
  "last": "2026-10-02"
 }
}
```

## Checks and honest reading (written after the run, 2026-10-04)
- **Coverage (D-042):** all 26 markets have holdout bars through 2026-10-02 (261 days; grains/livestock 251,
  exchange holidays); same-instrument returns available on >= 99.6% of days; largest daily move 6.8% (ZW) - no bad prints.
- **The verdict is CONFIRM by the rules fixed beforehand, but it is weak evidence.** One year: the standard error
  of an annual Sharpe is ~1.0, so Sharpe 0.72 is not statistically different from 0. It is a pass of a
  falsification test (the book could have lost and did not), not proof of an edge.
- **All of the profit is the trend sleeve** (+$108k on $1M, Sharpe 0.89, spread over many markets: largest
  contributor ZT +$29k; by sector fx +64k, rates +35k, energy +20k, metals +19k, equity +10k, grains -17k,
  livestock -21k; costs $24k). No single market carries it.
- **The pre-FOMC sleeve (H-007) lost:** -$18k over 8 FOMC trades. H-007's out-of-sample case is weaker now.
- Integer rounding at $1M leaves GC, SI and NQ with 0 contracts (large notional) - as in development; it
  missed the gold rally by construction, not by a bug.
- **At $100k the book made +1.6%** (trend +7.7%, FOMC -6.0%): the user's capital level is far from the 15%/yr target.
- Next step per D-050: paper trading (no broker connection from this project), not more backtests on this year.
  The holdout year is now spent: it must not be used to select or tune anything else.
