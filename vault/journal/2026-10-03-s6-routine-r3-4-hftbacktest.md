---
type: journal
date: 2026-10-03
tags: [journal]
---
# s6-routine-r3-4-hftbacktest

## 2026-10-03 06:20 UTC
Routine R3.4 (06:15 UTC firing): installed hftbacktest 2.4.4 (added to requirements), wrote backtest/hft_adapter.py (own vectorised Databento MBO converter; the bundled one crashes on N records). Independent cross-check: hftbacktest L3 book and our features.book replay agree on best bid/ask at 3,600/3,600 one-second samples in the first RTH hour of 2024-03-05. Phase 3 code complete; the l3_fifo calibration run needs a limit-order strategy and is queued as R3.5 for Phase 5. Next: Phase 4, R4.1.
