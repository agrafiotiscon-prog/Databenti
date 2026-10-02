# Databenti: order-flow research and backtesting (ES/NQ, Databento)

The goal is to test **honestly** whether order-flow signals have an edge in CME index futures after
realistic costs. The goal is not a good-looking backtest. If the answer is "no edge", that is a
valid and useful result.

**Start with the knowledge vault: [`vault/00-INDEX.md`](vault/00-INDEX.md).** It holds the
researched facts (Databento data semantics, CME market structure, real fees, academic evidence,
fill models, anti-overfitting methods) that every design decision here is based on. The changes
from the original brief, and the reasons, are in [`vault/06-roadmap.md`](vault/06-roadmap.md).

## Status

| Phase | Scope | Status |
|---|---|---|
| 0 | Research vault | **done** |
| 1 | Data layer: cost guard, cache, sessions, roll rule, flags | **done** (patched after research) |
| 1b | First real data (≤ $5) plus verification (`scripts/verify_data.py`) | tooling ready; needs `DATABENTO_API_KEY` |
| 2 | Features (footprint, delta, profile/VWAP, imbalances, heatmap, absorption, icebergs, spoof-like) + viewer | **code complete, tested on synthetic data**; awaiting real-data validation |
| 3 | Backtester: own L1 engine plus hftbacktest L3 FIFO calibration | planned |
| 4 | Anti-overfitting framework (walk-forward, DSR, PBO, sensitivity, trial log, gates) | planned |
| 5 | One example strategy plus a gated, logged research loop | planned |

## Project structure

```
Databenti/
├── CLAUDE.md             # auto-loaded by Claude Code; imports vault/_memory/MEMORY.md
├── tools/vault.py        # vault upkeep: journal | decide | inbox | search | check
├── vault/                # researched knowledge base + Claude's persistent memory (Obsidian-compatible)
├── data/                 # Phase 1
│   ├── config.py         # settings, API key loading (never printed), client factory
│   ├── cost_guard.py     # get_cost before every download, $5 limit, spend log
│   ├── cache.py          # per-UTC-day DBN cache layout, atomic writes
│   ├── contracts.py      # quarterly expiry and roll calendar → ES.c.0 / ES.c.1 per trading date
│   ├── download.py       # Downloader: plan → price everything → download missing chunks
│   ├── loader.py         # DBN → DataFrame (+ parquet), file order preserved, slice one session
│   ├── sessions.py       # US/Central sessions: RTH/ETH, trading-date rollover, DST
│   ├── rolls.py          # roll detection, roll calendar parsing, back-adjustment
│   ├── flags.py          # Databento flag bits (F_LAST, F_SNAPSHOT, …) and helpers
│   └── fetch.py          # CLI: python -m data.fetch ...
├── features/             # Phase 2 (spec: vault/03-order-flow/feature-definitions.md)
│   ├── common.py         # tick grid, bars, side conventions
│   ├── footprint.py      # footprint, delta, cumulative delta, divergence
│   ├── profile.py        # developing POC/value area, session levels, VWAP + bands
│   ├── imbalance.py      # diagonal and stacked imbalances
│   ├── absorption.py     # causal absorption events (trades/TBBO)
│   ├── book.py           # MBO order book, annotate_mbo (fill vs cancel, refills), heatmaps
│   ├── iceberg.py        # native and synthetic iceberg detection
│   └── spoof.py          # large-order / spoof-like pull detection
├── scripts/
│   ├── verify_data.py    # Phase 1b real-data checks → vault/results/
│   └── plot_day.py       # Plotly day viewer (markers at known_at) → reports/
├── config/               # costs.toml (fee profiles), splits.toml (holdout policy)
├── backtest/  research/  # Phases 3–5
├── tests/                # pytest, fully offline
└── cache/                # downloaded data (gitignored)
```

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env        # local: put DATABENTO_API_KEY in .env (never commit it)
# cloud sessions: set DATABENTO_API_KEY as an environment variable in the environment settings
python -m pytest            # all tests run offline
```

## Getting data

```bash
# 1) Price only. Downloads nothing. The contract is chosen per date by the roll rule.
python -m data.fetch --schemas trades tbbo mbp-1 mbp-10 mbo ohlcv-1m status \
    --start 2024-03-05 --end 2024-03-07 --rth-only --dry-run

# 2) Download. Cached days are skipped. Above $5 it asks you to type 'yes'.
python -m data.fetch --schemas trades tbbo ohlcv-1m status --start 2024-03-05 --end 2024-03-07
```

```python
from datetime import date
from data.download import Downloader
from data.loader import load_session

dl = Downloader()
trades = load_session(dl, "trades", date(2024, 3, 5), rth_only=True)
```

## Key assumptions (details and sources in the vault)

- **Cost guard:** every download first calls `metadata.get_cost` for all missing chunks
  together and prints each estimate and the total. Above `DATABENTO_MAX_COST_USD` (default
  **$5**) it downloads nothing. Every estimate goes to `cache/spend_log.csv`.
- **Cache:** one file per `(dataset, schema, symbol, UTC day)`.
  - Each UTC day of MBO starts with Databento's 00:00 UTC book snapshot, so every chunk is
    self-contained.
  - Partial downloads are never treated as cached.
- **Record order:** preserved exactly as delivered. CME FIFO priority is carried by message
  order, so the loader never re-sorts.
- **Sessions:** Globex runs 17:00–16:00 CT, with a 16:00–17:00 maintenance break. RTH is
  08:30–15:00 CT. A timestamp at or after 17:00 CT belongs to the next trading date. Holidays and
  early closes will come from the `status` schema (Phase 1b).
- **Rolls:**
  - `ES.c.0` stays on the expiring contract until expiry, so we use `ES.c.0` normally and
    `ES.c.1` from the roll Thursday (8 days before expiry) through expiry.
  - One contract per session, and contracts are never mixed in one frame.
  - The roll offset is configurable, and it will be checked against real liquidity data,
    because the evidence conflicts (see the vault).
- **Costs (ES, IBKR retail, 2026-10):**
  - About **$2.26 per side**: exchange $1.385, NFA $0.02, commission $0.85. That is about
    **$4.51 per round turn**, or 0.36 tick.
  - With the spread, a market-in/market-out round turn costs about **1.36 ticks (≈ $17)**
    before any latency slippage.
  - MES fees are about **1 tick** per round turn.
  - Verify against your own broker: CME changed fees effective 2026-10-01.
- **No live trading or broker connections** in this project.
