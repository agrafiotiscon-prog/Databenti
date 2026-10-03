---
type: journal
date: 2026-10-03
tags: [journal]
---
# s6-routine-r2-4-day-check

## 2026-10-03 02:51 UTC
Routine R2.4 (02:15 UTC firing): rendered the 2024-03-05 RTH day chart (plot_day + headless Chromium screenshot, saved to vault/results). Chart is sane, but iceberg markers far from the market exposed a new MBO pattern: orders modified into the market and fully filled trade under their own id at the market price, then their old entry is deleted. annotate_mbo now treats any F away from the resting price as aggressor volume (new kind aggressor_removal); RTH aggressor share 1.27%, native icebergs 1,540 -> 1,432, fills still 100% accounted. Also: late size increases no longer count as iceberg refills. Tests incl. negative controls. Phase 2 complete; next R3.1 (backtester). $0.
