---
type: journal
date: 2026-10-03
tags: [journal]
---
# s6-routine-r2-2-iceberg-refills

## 2026-10-03 01:17 UTC
Routine R2.2 (firing 00:15 UTC, resumed after the user's usage limit reset): native iceberg refills in Databento MBO are an M on the same order id at the same price in the same event as the fill (3,018 refills, 994 orders, 100% same event, 72% back to the original clip, mostly 1-lot). The 1-ms same-size re-add pattern behind synthetic icebergs occurs 156k times per RTH day and never in the same event, i.e. it is ordinary flow; R2.3 will calibrate. No code change, $0.
