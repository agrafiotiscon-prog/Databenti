---
type: topic
tags: [backtesting]
updated: 2026-10-02
---
# Backtest engines compared (decision record)

| | Own Python event engine | hftbacktest 2.4.4 | NautilusTrader 1.221 | vectorbt / bar-based |
|---|---|---|---|---|
| Databento input | via our loader | `hftbacktest.data.utils.databento.convert` (MBO only) | native Rust DBN adapter (MBO→deltas, MBP, trades, bars) | via DataFrames |
| L3 FIFO queue | would need to be built | **`L3FIFOQueueModel` (exact)** | L3 book, plus probabilistic `prob_fill_on_limit` | no |
| L2 queue models | would need to be built | Risk-averse, power, log, prob models | `prob_fill_on_limit` | no |
| Latency | would need to be built | **feed + order-entry + response latency, constant or interpolated from real data** | limited (fill-model docs don't cover latency) | no |
| Multi-year L1 research | **yes (cheap data)** | needs depth data (MBP/MBO) | yes | yes, but no tick realism |
| Transparency and testability | full | good (Rust core, numba strategies) | heavy framework | high |
| Path to live trading | no | yes (Rust live bots) | **yes (Databento live and broker adapters)** | no |
| Market impact | none | none (stated) | none for replay | none |

Verified locally: `pip install hftbacktest` works on Python 3.11 and the converter is present.
**Caveat:** the converter raises `ValueError` on MBO `action == 'N'` records, so filter them
first. Its docs note that CME implied orders are absent from MBO.

## Decision
1. **Tier A (research, years of L1 data):** a small own event-driven engine. It replays
   TBBO/MBP-1 plus trades, uses the fill modes in [fill models](fill-and-latency-models.md), and
   has a latency model. It is small enough to unit-test every rule (about 500 lines, not a
   framework).
2. **Tier B (fill calibration on MBO):** **hftbacktest** with `L3FIFOQueueModel` and an explicit
   latency model, instead of writing our own MBO queue simulator. This **replaces** the
   original brief's "build our own MBO queue model". A mature, purpose-built implementation
   carries far less risk of subtle queue bugs. Our own `features/book.py` is still built (for
   features), and it is cross-checked against hftbacktest's book on the same data.
3. **NautilusTrader**: deferred to the (out-of-scope) live phase. It is the natural route to
   paper or live trading with Databento plus a broker, and it reuses the same data.
