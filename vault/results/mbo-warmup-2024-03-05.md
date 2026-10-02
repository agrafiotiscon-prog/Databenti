---
type: result
date: 2026-10-02
tags: [verification, phase-1b, mbo]
---
# MBO book warm-up: slicing before replay loses the resting book (2024-03-05, ES.c.0)

Script: scratch comparison, session 5 (same data as [verify-2024-03-05](verify-2024-03-05.md)).
"Cold" = slice the session by time, then replay (old `load_session`). "Warm" = replay from the
first chunk's 00:00 UTC snapshot, then keep only the session (`data.loader.with_book_warmup`).

| Replay | unknown_order records | where | fill reconciliation |
|---|---|---|---|
| RTH, cold | **7,828** | 4,896 in 08:00 CT hour, still 548 in the 14:00 hour | 0.9907 |
| RTH, warm | **0** | | 0.9939 (→ 1.0 with hidden/aggressor fills, see below) |
| Full session, cold | 460 | all 17:00–18:00 CT (before the 00:00 UTC snapshot) | 0.9941 |
| Full session, warm | **0** | | 0.9942 |

- Best bid/ask differed on only ~0.001% of records (new orders join the touch constantly), so a
  touch-only check would have missed the bug. **Depth and queue sizes** were wrong, which
  breaks the heatmap, queue position, iceberg and spoof features.
- Databento puts an MBO snapshot (`F_SNAPSHOT`, starts with an `R` clear) at **00:00 UTC of each
  daily file** [data]; there is none at the 17:00 CT session open or the 08:30 CT RTH open.
- Fix: commit "MBO: rebuild the resting book from the opening snapshot before slicing";
  negative-control test `test_warmup_rebuilds_resting_book`.
- Cost of the fix: a full-session replay now also replays the previous UTC day (~6.5M extra
  records, about +60% replay time).

Fill accounting details: [mbo-fill-reconciliation-2024-03-05](mbo-fill-reconciliation-2024-03-05.md).
