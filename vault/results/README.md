---
type: index
tags: [results]
---
# Results

Every experiment, verification and backtest report lands here as its own note, written by a
script and never edited by hand afterwards:
- `verify-<date>.md`: Phase 1b data checks (`scripts/verify_data.py --date ...`)
- `verify-roll-<YYYY-MM>.md`: roll-crossover check (`scripts/verify_data.py --roll ...`)
- `roll-history-<ROOT>.md`: roll crossover on every expiry from daily bars (`scripts/roll_history.py`)
- `mbo-warmup-2024-03-05.md`, `mbo-fill-reconciliation-2024-03-05.md`: session-5 MBO findings
- later: backtest and gate reports (Phases 3–5)
