---
type: decision-log
tags: [decisions]
---
# Decision log (append-only; newest at the bottom)

Format: `## D-NNN — title (date)`, then **Decision**, **Why**, **Alternatives**, **Status**.
Add entries with `python tools/vault.py decide "title" --decision ... --why ...`.

## D-001 — Stack and repository layout (2026-10-02)
- **Decision:** Python 3.11, the official `databento` client, pandas/numpy/pyarrow, pytest.
  Packages `data/ features/ backtest/ research/`, plus `tests/`. Cache in `cache/` (gitignored).
- **Why:** this is what the user's brief asked for.
- **Status:** active.

## D-002 — Cost guard and per-UTC-day cache (2026-10-02)
- **Decision:** call `get_cost` for **all** missing chunks before downloading anything. Refuse
  above $5 unless the user explicitly approves. Cache one file per (schema, symbol, UTC day),
  with atomic writes.
- **Why:** the user's brief requires it. Databento bills each streamed request again. MBO's
  00:00 UTC snapshot makes UTC-day chunks self-contained.
- **Status:** active.

## D-003 — Do not use bare `ES.c.0`; use a roll-date rule (2026-10-02)
- **Decision:** `ES.c.0` before the roll Thursday (8 days before expiry), `ES.c.1` from then
  until expiry. One contract per session. The offset is configurable.
  *(Offset superseded by D-016: Monday of expiry week, 4 days before expiry.)*
- **Why:** Databento's `c` rule rolls only at expiry, so the data would sit on a dying contract
  for about a week each quarter.
- **Alternatives:** `ES.v.0` (lags a day, and may be distorted by spread-leg volume), or raw
  symbols (formats vary between 1- and 2-digit years).
- **Status:** active. The crossover day is to be verified on real data (open question).

## D-004 — Two-tier data design (2026-10-02)
- **Decision:** research on years of L1 data (`trades`, `tbbo`/`mbp-1`). Use MBO only for recent
  months to calibrate fills and for MBO-only features.
- **Why:** MBO cost, and the Standard plan includes only 1 month of L2/L3. Statistical power
  needs years.
- **Status:** active.

## D-005 — hftbacktest for L3 FIFO fills instead of our own MBO queue simulator (2026-10-02)
- **Decision:** our own small L1 event engine for research; hftbacktest's `L3FIFOQueueModel`
  plus a latency model to calibrate it on MBO.
- **Why:** a mature, Databento-compatible implementation already exists, so writing our own
  adds bug risk. Caveat: filter `action == 'N'` before its converter.
- **Status:** planned (Phase 3).

## D-006 — Latency-driven slippage, and cost/latency stress tests (2026-10-02)
- **Decision:** default 100 ms decision-to-exchange latency; fills are evaluated at arrival.
  Every report is rerun at fees ×1.5 and ×2 and at latency 250 ms and 500 ms.
- **Why:** slippage is correlated with signals that fire in fast markets.
- **Status:** planned (Phase 3).

## D-007 — Loader preserves file order (2026-10-02)
- **Decision:** never re-sort records within or across a symbol's chunks. Refuse to mix
  symbols in one frame.
- **Why:** CME FIFO priority is carried by Databento's message order, and snapshot records
  carry inaccurate `ts_recv` values.
- **Status:** done.

## D-008 — Statistical gates (2026-10-02)
- **Decision:** walk-forward, DSR, PBO (CSCV), t ≥ 3 hurdle, ±20% plateau, concentration
  flags, ≥ 200 trades; gates G1–G8.
- **Why:** selection bias and multiple testing.
- **Status:** planned (Phase 4).

## D-009 — Gated research loop instead of "improve until profitable" (2026-10-02)
- **Decision:** a hypothesis registry with trial budgets, an append-only trial log, the
  evaluator, and reports. The loop may never touch the holdout, the cost model or the gates.
- **Why:** unconstrained search manufactures false positives.
- **Status:** planned (Phase 5).

## D-010 — Vault as Claude's persistent memory (2026-10-02)
- **Decision:** `CLAUDE.md` (auto-loaded) imports `vault/_memory/MEMORY.md`. The protocol
  requires writing knowledge, decisions, inbox items and journals to the vault and pushing every
  turn. `tools/vault.py` provides journal, decide, search and check. The vault is
  Obsidian-compatible (relative Markdown links, frontmatter, `.obsidian/` settings).
- **Why:** the user asked for a vault Claude controls, so that nothing is lost across context
  windows and sessions. The container is ephemeral; git is the durable store.
- **Status:** active.

## D-011 — Monte Carlo on every parameter set, and cluster analysis (2026-10-02)
- **Decision:** add MC (block bootstrap, execution MC, trade shuffle) for **every** grid point,
  with selection on the 5th percentile. Cluster all trials by PnL correlation to get the
  effective K for the DSR and to find regions, then pick cluster medoids. New gates G9–G11.
- **Why:** a video checklist from the user, cross-checked against López de Prado & Lewis
  (2019). Its claim that passing these steps means "deploy live" is rejected: the holdout and
  paper trading are still required.
- **Status:** planned (Phase 4).

## D-012 — Target instrument: ES (2026-10-02)
- **Decision:** Research and cost model target ES first (fees ~0.36 tick/RT). MES results can be reported under its own cost profile later.
- **Why:** User choice (session 4). ES fees per tick are ~2.8x lower than MES, so small order-flow edges have a chance; capital (~$22-24k margin) is the user's concern for later.
- **Alternatives:** MES (1/10 margin, ~1 tick/RT fees); research ES and trade MES.
- **Status:** active.

## D-013 — Databento billing: pay-as-you-go (2026-10-02)
- **Decision:** Usage-based billing, starting with the $125 free credit. The $5 per-request cost guard stays; ask before anything larger.
- **Why:** User choice (session 4). Cheapest way through Phase 1b-2; the Standard plan can be revisited when multi-month L1 pulls start.
- **Alternatives:** Standard plan $199/mo (1y L1 + 1m MBO included).
- **Status:** active.

## D-014 — Final holdout = most recent 12 months (2026-10-02)
- **Decision:** Reserve the last 12 months of available tier-A data as the final holdout. The exact start date is frozen in config/splits.toml at the first multi-month data pull. The loader will refuse those dates without research/HOLDOUT_UNLOCK (Phase 4).
- **Why:** User choice (session 4). This tests on the newest regime, the one that would actually be traded.
- **Status:** active.

## D-015 — Broker fees: IBKR default, switchable (2026-10-02)
- **Decision:** config/costs.toml holds per-broker profiles. Default ibkr_tiered (ES $2.255/side all-in). Other brokers are added when the user picks one.
- **Why:** User not sure yet (session 4). IBKR figures are verified from its fee pages; the exchange fee is the same for all non-members, so only the commission differs.
- **Status:** active.

## D-016 — ES roll rule: Monday of expiry week (days_before 8 -> 4) (2026-10-02)
- **Decision:** DEFAULT_ROLL_DAYS_BEFORE_EXPIRY = 4 in data/contracts.py: from the Monday of expiry week to expiry, use ES.c.1. This replaces the roll-Thursday convention (8) from the brief and the research note.
- **Why:** Real data. scripts/roll_history.py (ohlcv-1d, ES.c.0 vs ES.c.1, 27 rolls 2019-03..2025-09, $0.04): every roll from 2022-06 to 2025-09 (14 in a row) crossed on the Monday of expiry week. Wrong-contract days: rule 4 = 11 (all in the old regime), rule 7 = 16, rule 8 = 43, previous-day volume (like ES.v.0) = 27. The 2024-03 RTH trades check (verify-roll-2024-03) agrees: c.0 still out-traded c.1 3:1 on Fri 03-08, and c.1 led from Mon 03-11. Calendar-spread legs print equally in both outrights, so they cancel in the comparison. The rule uses only the calendar (no lookahead). The data ends 2025-10-01, before the future 12-month holdout; daily bars do not freeze holdout_start (D-014 is about tier-A order-flow pulls).
- **Alternatives:** 8 (Thursday convention): 2 wrong days per recent roll. 7: right before mid-2022, 1 day early since. ES.v.0: always 1 day late. A per-roll data-driven switch: lookahead risk.
- **Status:** active.
