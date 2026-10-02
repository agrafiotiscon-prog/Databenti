---
type: journal
date: 2026-10-02
tags: [journal]
---
# s5-real-data-rolls-mbo-routine

## 2026-10-02 23:27 UTC
Session 5: first real Databento data. Key works. Downloaded 2024-03-05 ES trades/tbbo/mbo/status ($2.48 RTH-day chunks + $0.95 for the full-session 03-04 chunks), the 2024-03 roll window trades for c.0 and c.1 (user approved ~$7.48), and ES daily bars 2019-2025-09 ($0.04). Total ≈ $10.06.
Findings: (1) Roll crossover is the Monday of expiry week, 14 rolls in a row since 2022-06 (roll_history.py); rule changed 8 -> 4 days (D-016). (2) Slicing MBO before replay lost the resting book: 7,828 unknown orders in RTH; fixed with a warm-up from the 00:00 UTC snapshot (with_book_warmup). (3) MBO fill accounting is exact: explained + hidden iceberg reserve (0.48%) + aggressor fills of orders modified into the market (0.12%) = 100% of F volume; new kind modify_price_fill also removes false iceberg hits. (4) Side-N share ≈ 0.002%. (5) Bugs fixed: stale .part blocked retries; spend_log overstated spend (now download_log.csv).
User asked for an automated research routine every 30 min; platform minimum is 1 h, so an hourly routine (trig_01SxDd7cr6pA7egPMDYvJNAH, :15 UTC) now works through research/QUEUE.md under research/ROUTINE.md (D-017). Next: R2.2-R2.4, then Phase 3. Needs the user: data budget for multi-year backtests.
