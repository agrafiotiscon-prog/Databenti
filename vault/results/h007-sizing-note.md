---
type: result
date: 2026-10-03
tags: [H-007, sizing, descriptive]
---
# H-007: what the dollar figures mean in risk terms (descriptive only - not a re-test, no selection)

The user asked whether the by-year figures equal "risking 1% of $100k per trade". They do not: the
report trades **one ES contract** every time, with no stop. Descriptive numbers for the fixed rule
(day-before 13:00 → 13:00 CT, 98 meetings 2013-06..2025-09, 1 tick slippage per side + fees):
- per-trade P&L std **$1,195** (≈ 1.2% of $100k); worst **−$3,630** (−3.6%); best +$4,445;
  7 losses > $1,000, 2 > $2,000. Total +$31.7k for this window-only rule. The walk-forward report
  says +$21.3k because selection picked the losing morning window in 3 of 13 folds.
- **Volatility-scaled sizing** (contracts so that 1 sd of a 1-day move, from the 20 days ending two
  days before the meeting, = $1,000; fractional ≈ MES): avg 1.02 contracts (0.14-2.73), total
  **+$11.0k = +11% on $100k**, worst trade −$2,657, max drawdown $4,724. Lower than fixed size
  because the best years (2020, 2022) were high-volatility, when this sizing cuts exposure.
Script: session scratchpad only (`h007risk.py`); numbers [inferred] from the cached hourly bars.
