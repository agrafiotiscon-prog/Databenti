# Going live later (explicitly out of scope now)

The brief says no live trading or broker connections. This note only records what was learned,
so that the research code does not paint us into a corner.

- **Same code path:** Databento's Live API uses the same record types and schemas as historical
  replay, and `DBNStore.replay(callback)` mimics live delivery. Features should be written as
  **incremental, event-driven updaters** (update on each record) so the same code runs live.
  Batch DataFrame versions are for research speed and must match the incremental version in
  tests.
- **Live MBO snapshot:** the live API can send a book snapshot on subscribe. The book is valid
  only after the next `F_LAST`.
- **Execution:** NautilusTrader has a Databento data adapter plus broker adapters. Alternatively,
  a broker API (IBKR, Rithmic, CQG) can be used directly.
- **Order of steps:** gates → holdout → **paper trading** for weeks, comparing live fills to
  simulated fills → tiny size → scale. A kill switch, daily loss limit, max position and
  stale-data watchdog are all mandatory.
- **Latency:** measure real order-entry latency by sending non-marketable orders (the method
  hftbacktest recommends) and feed the measurements back into the backtest latency model.
