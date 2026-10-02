---
type: journal
date: 2026-10-02
session: 1
tags: [journal, phase-1]
---
# Session 1: Phase 1 data layer

**User asked:** to build the project structure and the Phase 1 data layer, stopping after the
phase. Long term, the user wants a self-improving research routine with realistic costs.

**Done:**
- Scaffold: `data/ features/ backtest/ research/ tests/`, `.gitignore` (`.env`, `cache/`),
  `.env.example`, `requirements.txt`, `pyproject.toml`.
- `data/config.py`: the key comes only from `.env`. `data/cost_guard.py`: `get_cost` before any
  download, $5 limit, `cache/spend_log.csv`.
- `data/cache.py` (per-UTC-day chunks, atomic `.part` → rename). `data/download.py`
  (`Downloader`). `data/loader.py` (DBN → DataFrame, plus parquet).
- `data/sessions.py`: US/Central RTH/ETH, the 17:00 CT trading-date rollover, DST.
  `data/rolls.py`: roll detection and back-adjustment.
- 25 offline tests, including a real DBN round trip with synthetic records.
- Commit `3af3a36`.

**Results:** 25/25 tests pass. No real data yet (no API key in the environment).

**Next:** the user's OK, then Phase 2. That was superseded by the research request in session 2.
