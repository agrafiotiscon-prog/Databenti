---
type: result
date: 2026-10-04
tags: [R9, combined-book, descriptive, not-evidence]
---
# Trend252 + H-030 month-end sleeve, risk-balanced at 15% vol: DESCRIPTIVE ONLY (hindsight)

Both sleeves were selected on 2010-2025 data (trend252 = best H-022 variant in hindsight; H-030 = best R9 idea),
so these numbers are an upper bound, not evidence. Evidence so far: trend252 passed the single holdout test weakly
(D-052); H-030 was confirmed on TN/UB (H-032, D-062). Combination: `portfolio/combine.py` (causal trailing-252-day
weights; with two uncorrelated sleeves inverse-vol and ERC coincide), 15% target vol, sleeve P&L scaled linearly
(costs scale with it; integer rounding ignored), 2011-06..2025-09.

| | ann. return | ann. vol | Sharpe |
|---|---|---|---|
| trend252 alone ($1M) | 4.7% | 15.8% | 0.30 |
| H-030 pre\|3\|all alone ($1M, 4 x $250k notional) | 1.2% | 1.7% | 0.74 |
| **combined, 15% vol target** | **12.7%** | 15.4% | **0.82** (max DD −21%) |

Correlation of the sleeves' daily P&L: 0.005. By year (%): 2011 −0.6, 2012 −4.6, 2013 21.3, 2014 42.2, 2015 14.5,
2016 −4.1, 2017 3.6, 2018 12.9, 2019 15.4, 2020 43.0, 2021 −6.3, 2022 27.2, 2023 −6.0, 2024 17.1, 2025 (to Sep) 5.5.
**Leverage note:** equal risk needs ~9x the H-030 sleeve, i.e. ~$9M of Treasury futures notional for 3 days a month on
$1M capital (margin roughly $0.2M) - feasible on futures, but a real concentration in month-end days.
Next: forward paper tracking of exactly this book (scripts/paper_track.py) - the only truly new evidence.
