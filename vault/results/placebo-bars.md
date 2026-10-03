---
type: result
date: 2026-10-03
tags: [placebo, G12, H-005, H-009]
---
# G12 placebo diagnostics for long-only bar rules (no selection)

## H-005 turn of month (entry_k = 2, exit_day = 3, i.e. 4-day holds)
- real: 128 trades, mean $-28.4/trade; random 4-day holds within a month: mean $292.9, 95th pct $812.7
- **one-sided p = 0.8439**

## H-009 overnight drift (weeknight holds, 15:00 -> 08:00 CT), gross of costs
- 2407 nights: overnight mean $54.8, close-to-close mean $78.1 (time share 17/24 -> $55.3)
- overnight minus time share: mean $-0.5, t = -0.02, **bootstrap one-sided p = 0.5060**
- after costs (~$29.5 per round trip incl. 1 tick adverse per side) the overnight mean is $25.3/night

