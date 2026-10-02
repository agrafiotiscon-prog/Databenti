---
type: journal
date: 2026-10-02
session: 2
tags: [journal, research]
---
# Session 2: research vault and Phase 1 patches

**User asked:** research everything (Databento specifically, order-flow bots in general,
backtesting) before the next step, and override the brief where the research is stronger.

**How the research was done:**
- Databento's docs are a JavaScript app. Rendered copies were fetched with a crawler user-agent
  through curl, and the navigation was stripped (script in the scratchpad, not kept).
- About 40 Databento doc pages were read: schemas, standards, the GLBX venue notes, the
  symbology, the order-book, slippage, latency and HFT tutorials, and pricing.
- The CME site blocked fetches, so fees were taken from IBKR's CME pass-through and commission
  tables.
- Read the hftbacktest docs and source (installed 2.4.4 locally), the NautilusTrader docs, and
  the papers listed in [SOURCES](../SOURCES.md).

**Key findings:** see [00-INDEX](../00-INDEX.md), "ten rules". Most important:
- `ES.c.0` rolls only at expiry.
- MBO quirks: `F_LAST`, the 00:00 UTC snapshot, T/F records don't change the book, implied
  trades have side N.
- ES fees are about $4.51 per round turn, so market-in/market-out costs ≈ 1.36 ticks.
- The $199 plan includes only 1 month of MBO.
- hftbacktest has an exact L3 FIFO model for Databento MBO, but its converter breaks on N
  actions.
- Order-flow predictability is concentrated within about 2 price changes. 97% of persistent
  Brazilian mini-index day traders lost money.

**Code changes:**
- `data/contracts.py` (roll rule)
- `fetch_sessions` prices all symbols once
- the loader keeps file order and refuses to mix contracts
- `data/flags.py`
- more schemas
- 38 tests pass
- Commit `4a02e1a`

**Conflicts found:** the roll-crossover timing (the convention vs Databento's `ES.v.0` example).
Left as an open question with a configurable offset.

**Waiting on the user:** ES vs MES, data budget/plan, holdout, broker, API key.
