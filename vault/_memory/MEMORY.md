---
type: memory
updated: 2026-10-02
tags: [memory, state]
---
# MEMORY: always-loaded project state (keep it short; details live in linked notes)

## The user
- Wants an **honest** order-flow research and backtesting system for CME index futures (ES first)
  using Databento. The goal is a real edge after **realistic fees, commissions and slippage**,
  not a pretty backtest.
- Wants an **automated, continuously-improving research routine** that logs everything it tries.
- Wants everything **researched before building**, and has authorised overriding their own
  brief when the research is stronger. Wants this vault to be Claude's persistent memory.
- Works in phases: stop after each phase and wait for their OK.
- Shares outside material (e.g. video transcripts) → it goes into `vault/inbox/`.
- The full brief and later directives are in [project-brief](project-brief.md).

## Current state (2026-10-02)
- **Phase 0 (research vault): done.** Index: [00-INDEX](../00-INDEX.md).
- **Phase 1 (data layer): done and patched.**
  - roll rule (`ES.c.0` → `ES.c.1` from the roll Thursday)
  - cost guard ($5)
  - per-UTC-day cache
  - file-order loader
  - flags helpers
  - 38 tests pass (more with the vault tests)
- **Memory system: done.** `CLAUDE.md` imports this file; `tools/vault.py` (journal, decide,
  search, check).
- Video robustness steps integrated: MC on every parameter set, cluster analysis, gates G9–G11.
- **No real data downloaded yet.** There is no API key in the environment.

## Waiting on the user (blocking Phase 1b and 2)
1. ES vs MES (fees about 0.36 vs 1 tick per round turn; margin about $22–24k vs 1/10).
2. Databento budget: usage-based ($125 free credit) vs the Standard plan ($199/mo: 1 year L1 +
   1 month MBO).
3. Holdout = the most recent 12 months?
4. Broker (for `config/costs.yaml`).
5. API key in `.env`, then run the cost dry run (README "Getting data").

## Next step
Phase 1b: dry-run costs, then download ≤ $5, then verification scripts (roll crossover,
fill-removal reconciliation, side-N share, snapshot handling, `status`-based hours). Then
Phase 2 features per [feature-definitions](../03-order-flow/feature-definitions.md).

## Open questions (verify on real data)
- When ES liquidity actually crosses at the roll (convention: Thursday, 8 days before expiry;
  Databento's `ES.v.0` example suggests later) → [rolls](../01-databento/symbology-and-rolls.md)
- Whether MBO fill-removals appear as `C`/`M` records → [MBO](../01-databento/mbo-book-building.md)
- CME fee changes effective 2026-10-01 (SER #9799) → [costs](../02-market-structure/costs-fees-slippage.md)

## Key numbers to remember
- ES: tick 0.25 = $12.50. Fees about $2.26/side, $4.51 per round turn. Market-in/market-out ≈
  **1.36 ticks ≈ $17** per round trip before latency slippage.
- Default latency 100 ms; stress tests at 250 and 500 ms. Costs stress-tested at ×1.5 and ×2.
- Gates: ≥ 200 trades, DSR ≥ 0.95, PBO ≤ 0.10, plateau, MC 5th percentile > 0, cluster medoid.

## Where things are
- Decisions log: [decisions](decisions.md)
- Session journals: [journal/](../journal/)
- Inbox (user-supplied material): [inbox/](../inbox/)
- Roadmap: [06-roadmap](../06-roadmap.md)
