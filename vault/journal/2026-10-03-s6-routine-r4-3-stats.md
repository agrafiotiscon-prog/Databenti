---
type: journal
date: 2026-10-03
tags: [journal]
---
# s6-routine-r4-3-stats

## 2026-10-03 09:17 UTC
Routine R4.3 (09:15 UTC firing): research/stats.py implements the deflated Sharpe, PBO via CSCV, the plateau test and three Monte Carlo types exactly as in methodology.md, without scipy. Negative controls: the best of 200 noise strategies looks significant undeflated (PSR > 0.9) but DSR < 0.5; PBO of noise ~0.5, of a real edge < 0.05. Next: R4.4 (cluster analysis + G1-G11 gate report).
