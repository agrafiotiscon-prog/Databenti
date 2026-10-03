---
type: journal
date: 2026-10-03
tags: [journal]
---
# s6-routine-r2-3-calibration

## 2026-10-03 01:33 UTC
Routine R2.3 (01:15 UTC firing): new scripts/calibrate_mbo.py measures detector quality without strategy outcomes. Synthetic iceberg re-adds are at chance for 1-lot clips (precision ~+2%), +27% for clips >= 2 lots at dt=1ms: defaults changed to dt=1ms, min_clip_size=2, feature marked experimental. Spoof-like: 45% of far adds of any size are pulled untouched within 10 s, big orders less often: descriptive only. Decision D-018. Tests added (incl. negative control). $0.
