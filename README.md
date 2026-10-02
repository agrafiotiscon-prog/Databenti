# Databenti: order-flow research and backtesting (ES/NQ, Databento)

The goal is to test **honestly** whether order-flow signals have an edge in CME index futures after
realistic costs. The goal is not a good-looking backtest. If the answer is "no edge", that is a
valid and useful result.

## Status

| Phase | Scope | Status |
|---|---|---|
| 1 | Data layer: cost guard, cache, sessions, rolls | **done** |
| 2 | Features: footprint, delta, profile/VWAP, imbalances, heatmap, absorption, icebergs, spoofing | next |
| 3 | Event-driven tick backtester with realistic fills and fees | planned |
| 4 | Anti-overfitting framework (IS/OOS/holdout, walk-forward, sensitivity, trial log) | planned |
| 5 | One example strategy plus an automated, logged research loop | planned |

## Project structure

```
Databenti/
├── .env.example          # copy to .env, add DATABENTO_API_KEY (.env is gitignored)
├── requirements.txt / pyproject.toml
├── data/                 # Phase 1
│   ├── config.py         # settings, API key loading (never printed), client factory
│   ├── cost_guard.py     # get_cost before every download, $5 limit, spend log
│   ├── cache.py          # per-day DBN cache layout, atomic writes
│   ├── download.py       # Downloader: plan -> price -> download missing chunks
│   ├── loader.py         # DBN -> DataFrame (+ parquet cache), slice one session
│   ├── sessions.py       # US/Central sessions: RTH/ETH, trading-date rollover, DST
│   ├── rolls.py          # roll detection, roll calendar, back-adjustment
│   └── fetch.py          # CLI: python -m data.fetch ...
├── features/             # Phase 2
├── backtest/             # Phase 3
├── research/             # Phase 4/5 (trial log, walk-forward, sensitivity)
├── scripts/              # plotting and utilities
├── tests/                # pytest, no network access required
└── cache/                # downloaded data (gitignored)
```

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env        # then put your key in .env
python -m pytest            # all tests run offline
```

## Getting data (Phase 1)

```bash
# 1) Price only. Downloads nothing.
python -m data.fetch --schemas trades mbp-10 mbo ohlcv-1m --start 2024-03-05 --end 2024-03-07 --dry-run

# 2) Download. Already-cached days are skipped. Above $5 it asks you to type 'yes'.
python -m data.fetch --schemas trades ohlcv-1m --start 2024-03-05 --end 2024-03-07
```

In Python:

```python
from datetime import date
from data.download import Downloader
from data.loader import load_session

dl = Downloader()
trades = load_session(dl, "trades", date(2024, 3, 5), rth_only=True)
```

**Start with `trades` and `ohlcv-1m`.** They are cheap. `mbo` and `mbp-10` cost far more per day,
so run `--dry-run` on them first.

## Assumptions and design decisions

### Cost guard
- Every download first calls `client.metadata.get_cost(...)` for every missing chunk and prints
  each estimate and the total.
- If the total is over `DATABENTO_MAX_COST_USD` (default **$5**), it raises `CostLimitExceeded`
  and downloads nothing. The CLI only continues past the limit after you type `yes`.
- Every estimate is appended to `cache/spend_log.csv`.

### Caching
- The cache holds one file per `(dataset, schema, symbol, UTC day)` at
  `cache/GLBX.MDP3/<schema>/<symbol>/<YYYY-MM-DD>.dbn.zst`.
- Cached chunks are neither priced nor downloaded again.
- Downloads are written to `*.part` and then renamed, so a partial download is never treated as
  cached.
- On first load a `.parquet` copy is written next to the DBN file to make reloads faster.

### Sessions (US/Central, DST-aware)
- Globex trades from 17:00 CT to 16:00 CT the next day. The daily maintenance break is
  16:00–17:00 CT.
- **RTH** is 08:30–15:00 CT. **ETH** is the rest of the Globex session.
- A timestamp at or after 17:00 CT belongs to the **next** trading date, so Sunday evening counts
  toward Monday.
- Session-aware fetches pull the UTC days that cover the session. A full ETH+RTH session spans
  two UTC days.
- **Not modelled yet:** exchange holidays and early closes. They appear as missing or short
  sessions. Phase 4 will flag abnormal sessions so they can be excluded.

### Contract rolls
- `ES.c.0` (`stype_in="continuous"`) follows the front month using a calendar rule. Records carry
  the real contract's `instrument_id`, so a roll shows up as an id change. `detect_rolls()` finds
  these changes, and the loader adds a `contract_segment` column.
- **Policy:** order-flow features are computed per contract and never stitched across a roll inside
  one bar or window.
- When levels are compared across days (for example prior-day POC), the prices are back-adjusted
  with `back_adjust()`. The gap is measured from both contracts at the same instant.
- The backtester always trades real, unadjusted contract prices.
- `Downloader.roll_calendar()` uses the free symbology endpoint to show which contract is front on
  each day.
- Alternative: `ES.v.0` rolls by volume, which is closer to where liquidity actually is. This is
  worth comparing in later phases.

### Planned realistic cost model (Phase 3), configurable per contract
These are rough current retail figures. **Check them against your own broker statement.**

| Item | ES (per side) |
|---|---|
| CME exchange fee (non-member) | ~$1.38 |
| NFA fee | $0.02 |
| Clearing and broker commission | ~$0.25–$1.00 |
| **All-in round turn** | **~$3.50–$5.00** |
| Market-order slippage | spread (usually 1 tick = $12.50) plus at least 1 tick extra by default; more in fast markets and outside RTH |
| Limit orders | filled only after the MBO queue ahead of us has traded; the pessimistic mode also requires the price to trade *through* |

A round turn with one tick of slippage costs about **$30 per ES contract**. Many order-flow
"edges" are smaller than that, and Phase 3 is designed to show it.

## About "constantly improving until profitable"

The automated research loop is planned for Phase 5, after the backtester and the anti-overfitting
framework exist. Building it earlier would mean optimizing against nothing. Its design:
- Every variant it tries is written to an append-only trial log (`research/trials.jsonl`) with its
  parameters, data split, and results. The total trial count is always reported.
- It may only search in-sample and out-of-sample data. The final holdout stays locked until you
  unlock it.
- A variant is promoted only if it survives walk-forward testing, ±20% parameter sensitivity, at
  least 200 trades, results that are not concentrated in a few days, and a deflated-Sharpe style
  penalty for the number of trials.

An automated search will **always** find something that looks profitable in-sample if it runs long
enough. That is overfitting, not edge. These rules make the loop's output trustworthy. They cannot
guarantee that a profitable strategy exists, and the loop will report so if none does.
