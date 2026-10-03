---
type: journal
date: 2026-10-03
tags: [journal]
---
# s6-routine-r4-1-holdout

## 2026-10-03 07:18 UTC
Routine R4.1 (07:15 UTC firing): Phase 4 started. data/holdout.py enforces the final holdout in Downloader and load_session (nothing in the holdout is priced, downloaded or loaded without research/HOLDOUT_UNLOCK); a provisional lock from today-12 months applies until holdout_start is frozen at the first >=60-day tier-A pull. research/walkforward.py builds rolling folds with a 1-trading-day embargo from config/splits.toml. R3.5 stays deferred to Phase 5 (needs a limit-order strategy). Next: R4.2.
