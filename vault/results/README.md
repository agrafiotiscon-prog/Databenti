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
- `mbo-warmup-2024-03-05.md`, `mbo-fill-reconciliation-2024-03-05.md`: session-5 MBO findings;
  `mbo-iceberg-refills-2024-03-05.md` (R2.2); `mbo-calibration-<date>.md` (R2.3, `scripts/calibrate_mbo.py`); `day-check-2024-03-05-rth.md` + PNG (R2.4)
- `h0xx-report.md`: one gate report per hypothesis (`scripts/run_bars_hypothesis.py`, `run_hypothesis.py`); `leaderboard.md` ranks them
- `placebo-*.md` (G12), `coverage-audit-bars.md` (R6.7 event coverage), `fill-calibration-<date>.md` (R3.5, `scripts/calibrate_fills.py`), `h019-report-run1-buggy.md` (kept for honesty, D-041)
