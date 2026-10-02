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
