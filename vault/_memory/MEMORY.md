---
type: memory
updated: 2026-10-02
tags: [memory, state]
---
# MEMORY: always-loaded project state (keep it short; details live in linked notes)

## The user
- Wants an **honest** order-flow research and backtesting system for CME index futures using
  Databento. The goal is a real edge after **realistic fees, commissions and slippage**, not a
  pretty backtest.
- Wants an **automated, continuously-improving research routine** that logs everything it tries.
- Wants everything **researched before building**, and has authorised overriding their own
  brief when the research is stronger. Wants this vault to be Claude's persistent memory.
- Works in phases: stop after each phase and wait for their OK.
- Shares outside material (e.g. video transcripts) → it goes into `vault/inbox/`.
- Full brief: [project-brief](project-brief.md).

## Decisions made by the user (session 4) → [decisions](decisions.md) D-012..D-015
- Instrument **ES**. Billing **pay-as-you-go** ($125 credit, $5 guard). Holdout = **last 12
  months** (frozen at the first multi-month pull, `config/splits.toml`). Broker **not chosen**
  → IBKR fees as the default profile (`config/costs.toml`).

## Current state (2026-10-02)
- Phase 0 (research vault): done. Phase 1 (data layer): done and patched.
- **Phase 2 (features): code complete, tested on synthetic data only.** 97 tests, including
  no-lookahead tests with negative controls. Status table:
  [feature-definitions](../03-order-flow/feature-definitions.md#implementation-status-session-4-2026-10-02).
- Phase 1b tooling ready: `scripts/verify_data.py` (writes to `vault/results/`).
  `scripts/plot_day.py` is the Plotly viewer.
- **No real data yet.** `DATABENTO_API_KEY` is not set in the cloud environment (the user adds it
  under environment settings → variables; never paste it in chat).

## Next step (needs the API key)
1. `python -m data.fetch --schemas trades tbbo mbo status --start 2024-03-05 --end 2024-03-05 --rth-only --dry-run`
2. If ≤ $5: run `scripts/verify_data.py --date ... --schemas trades mbo status` and
   `--roll 2024-03`. Then fix whatever the real data contradicts (fill reconciliation, roll
   offset, side-N share).
3. `scripts/plot_day.py` for a visual check, then Phase 2 sign-off by the user → Phase 3
   (backtester).

## Open questions (verify on real data)
- ES roll liquidity crossover day → [rolls](../01-databento/symbology-and-rolls.md)
- MBO fill reconciliation ratio (should be ≈ 1.0) → [MBO](../01-databento/mbo-book-building.md)
- How native iceberg refills actually appear in Databento MBO (M same size? M up?)
- CME fees after 2026-10-01 (SER #9799) → [costs](../02-market-structure/costs-fees-slippage.md)
- Spoof `min_size` default (50) and iceberg `dt` (5 ms) need calibration on real data

## Key numbers
- ES: tick 0.25 = $12.50. Fees about $2.26/side, $4.51 per round turn. Market-in/market-out ≈
  **1.36 ticks ≈ $17** before slippage.
- Latency 100 ms (stress 250/500). Fees ×1.5 and ×2 stress. Gates G1–G11 (≥ 200 trades,
  DSR ≥ 0.95, PBO ≤ 0.10, plateau, MC 5th percentile > 0, cluster medoid).

## Where things are
- [decisions](decisions.md) · [journal/](../journal/) · [inbox/](../inbox/) · [results/](../results/README.md) · [roadmap](../06-roadmap.md)
- Code: `data/` (Phase 1) · `features/` (Phase 2) · `scripts/` · `config/` · `tools/vault.py`
