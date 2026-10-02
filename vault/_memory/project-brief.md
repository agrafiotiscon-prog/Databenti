---
type: brief
tags: [requirements, user]
---
# Project brief: the user's own requirements (verbatim, plus later directives)

## Original brief (session 1, 2026-10-02)

> **Project: Order-flow research & backtesting system (ES/NQ futures, Databento)**
>
> I want to build an order-flow trading research system in Python using Databento data. The goal is
> to honestly test whether order-flow signals have a real edge, NOT to produce a pretty backtest.
> Work in phases. At the end of each phase, stop, summarize what you built, show test results, and
> wait for my OK before continuing.
>
> **Constraints**
> - Python 3.11+, the official `databento` Python client, pandas/polars, numpy, pytest.
> - API key read from a `.env` file (DATABENTO_API_KEY). Never hardcode or print it. Add `.env` to .gitignore.
> - **Cost guard:** before ANY historical download, call `client.metadata.get_cost(...)` and print the
>   estimated $ cost. Never download anything over $5 without asking me first.
> - Cache all downloaded data locally (DBN or parquet) so nothing is downloaded twice.
> - Dataset: `GLBX.MDP3`. Start with ES front-month (continuous symbol, e.g. `ES.c.0` with `stype_in="continuous"`).
> - Keep code modular: `data/`, `features/`, `backtest/`, `research/`, `tests/`.
>
> **Phase 1: Data layer**
> - Download helper with cost check plus caching for schemas: `trades`, `mbp-10`, `mbo`, `ohlcv-1m`.
> - Start with only 2–3 trading days of ES to keep cost tiny.
> - Handle contract rolls and session times (RTH vs ETH, US/Central timezone).
>
> **Phase 2: Features (each with unit tests on small hand-made examples)**
> 1. Footprint: bid/ask volume per price per bar (use the trade `side` field for aggressor).
> 2. Delta and cumulative delta.
> 3. Volume profile (POC, value area) and VWAP with bands.
> 4. Diagonal imbalances and stacked imbalances (configurable ratio, e.g. 300%).
> 5. Order-book heatmap data from mbp-10 (and an mbo version for full depth).
> 6. Absorption: heavy aggressive volume at a level while price fails to move through it.
> 7. Iceberg detection from MBO: traded volume at a price exceeding visible size / repeated refills.
> 8. Large-order / spoof-like behavior: big resting orders added then cancelled before price reaches them.
> Also a simple plotting script (plotly) to visually check features against price for one day.
>
> **Phase 3: Backtester (event-driven, tick-level)**
> - Realistic fills: market orders pay the spread plus configurable slippage. Limit orders use a
>   queue-position model from MBO (only filled once volume ahead of us has traded), with a
>   pessimistic option.
> - Commissions and exchange fees per contract (configurable).
> - Outputs: trade list, equity curve, win rate, profit factor, Sharpe, max drawdown, avg trade,
>   number of trades, and **results broken down per year and per month**.
>
> **Phase 4: Anti-overfitting research framework**
> - Strict split: in-sample / out-of-sample / final holdout (the holdout is untouched until I say so).
> - Walk-forward optimization.
> - Parameter sensitivity: show a heatmap of results when parameters are nudged ±20%.
> - Log every strategy variant tested (count of trials) so I can see how much searching was done.
> - Flag strategies with < 200 trades or performance concentrated in a few days.
>
> **Phase 5: One example strategy**
> Implement ONE simple, hypothesis-driven strategy as a template, e.g.: "Absorption at a
> volume-profile level + delta divergence → fade, fixed stop/target." Run it through the full
> Phase 4 framework and give me an honest assessment, including if it doesn't work.
>
> **Rules for you**
> - Be skeptical. If results look too good, look for lookahead bias, data leakage, or unrealistic fills first.
> - Never use future data in features (verify with tests).
> - Explain assumptions clearly in a README.
> - Do NOT build live trading or broker connections yet.
>
> Start with Phase 1. First, show me the project structure you plan to create.
>
> ur main task is to create it and set up a routine on constantly improving and backtesting the
> improves also keeping logs of what it has tried and i want realistic slip or fees comission ect so
> it is actually profitable

## Later directives
- **Session 2:** "before i do that i want u to have vault knowledge for how to create a trading bot
  with databento specifically and in general … everything has to be 100% studied and researched
  before taking the next step. Ignore my original prompt if u find something that conflicts with
  it and u think it holds more power." → [D-003 … D-009](decisions.md), [00-INDEX](../00-INDEX.md)
- **Session 3:** the user shared a video checklist (parameter heatmap, MC on every parameter set,
  cluster analysis, IS/OOS + walk-forward) → [inbox note](../inbox/2026-10-02-video-four-robustness-steps.md),
  [D-011](decisions.md).
- **Session 3:** "i want a vault like obsidian but one u control entirely so the data we discuss
  about and everything u do get saved there instead of getting lost on every context window" →
  [D-010](decisions.md), `CLAUDE.md`, `tools/vault.py`.
