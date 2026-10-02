---
type: journal
date: 2026-10-02
tags: [journal]
---
# s4 decisions and phase 2 features

## 2026-10-02 21:08 UTC
**User asked:** what I need in order to continue. Answered via a questionnaire: ES; pay-as-you-go; 12-month holdout; broker unsure → IBKR default. Logged as D-012..D-015.

**API key:** not present in the environment. The user was told to add DATABENTO_API_KEY as an environment variable in the cloud environment settings (never in chat). config.get_api_key already reads env vars.

**Done (Phase 2 code, without real data):**
- config/costs.toml (IBKR profile; ES/MES/NQ/MNQ; stress settings) and config/splits.toml (12-month holdout policy, walk-forward 12/3/3, 1-day embargo).
- features: common, footprint (+ delta, cum delta, divergence), profile (developing POC/VA with CBOT method, session levels, VWAP + bands), imbalance (diagonal, stacked), absorption (causal, re-arming), book (OrderBook, annotate_mbo with fill accounting + refill detection + fill_explained, mbo/mbp10 heatmaps), iceberg (native, synthetic), spoof (spoof-like pulls).
- tests/causality.py: truncation + perturbation no-lookahead harness, with two negative controls proven to fail.
- scripts/verify_data.py (Phase 1b report → vault/results/) and scripts/plot_day.py (Plotly, markers at known_at).

**Bugs caught during the work:**
- the first absorption alignment helper was wrong → rewritten
- heatmap could straddle an event at a bucket boundary → consistent flag instead of peeking
- a same-size native iceberg refill was invisible to a per-event fill rule → unexplained-fill balance across events
- an MBO causality test could pass vacuously → fixture now generates icebergs, and the tests assert non-empty output

**Results:** 97 tests pass; vault check OK.

**Next:** API key → cost dry run → verify_data on 1 RTH day (trades, mbo, status) and the 2024-03 roll window → fix what the real data contradicts → user sign-off of Phase 2 → Phase 3.
