# Research routine protocol (read this first on every firing)

A scheduled routine (`trig_01SxDd7cr6pA7egPMDYvJNAH`) fires into this session every hour at :15 UTC (decision D-017; the user asked for 30 min, the platform minimum is 1 hour). Each firing does
**one bounded unit of work** from [QUEUE.md](QUEUE.md), logs it, commits and pushes. The design
is [research-loop](../vault/05-anti-overfitting/research-loop.md); the gates are in
[methodology](../vault/05-anti-overfitting/methodology.md) (G1–G11).

## Every firing
1. Read `vault/_memory/MEMORY.md`, this file and `QUEUE.md`. If a previous unit is still in
   progress (uncommitted changes, a running background job), finish that first.
2. If the user has written since the last firing, their message wins over the queue.
3. Take the first open item in `QUEUE.md`. Work on it for at most ~40 minutes. If it is bigger,
   split it in `QUEUE.md` and do the first piece.
4. Code changes need tests. `python -m pytest` and `python tools/vault.py check` must pass before
   committing. A failing test is never skipped or deleted to get green.
5. Log: one line in `research/CHANGELOG.md` (date, item, outcome); every backtest variant goes
   to `research/trials.jsonl` (append-only, failures included, count never reset); results go
   to `vault/results/`; decisions go through `python tools/vault.py decide`.
6. Update `QUEUE.md` (tick the item, add follow-ups) and `MEMORY.md` (state + next step), add
   a journal entry, then commit and push to the session branch.
7. Notify the user (push notification) only when: a phase finishes, a candidate passes all
   gates, the budget blocks progress, or something is broken that needs them. Otherwise, stay
   quiet.

## What "keep it if it is more profitable" means
- A strategy variant is **kept** (written to `research/CHAMPION.md`) only if it passes **every
  gate G1–G11** on walk-forward out-of-sample data, after realistic costs: `config/costs.toml`
  fees (×1.5 stress), 100 ms latency (250 ms stress), pessimistic fills. A higher in-sample
  number is never a reason to keep anything.
- A new champion replaces the old one only if it passes all gates **and** beats it on the
  out-of-sample 5th-percentile Monte Carlo PnL at 1.5× fees.
- Too-good results (Sharpe > 3, win rate > 70%, PF > 2.5) mean: look for lookahead, leakage or
  optimistic fills first, and write down what was checked.
- Parameters change only inside a hypothesis's declared space and trial budget. New hypotheses
  need a written mechanism ("who pays us, and why?") before any result is seen.

## Hard limits (never)
- No live trading, no broker connections, no orders anywhere.
- Never read or evaluate the holdout (`config/splits.toml`; only `research/HOLDOUT_UNLOCK`,
  created by the user, opens it).
- Never make the cost model, fill model or gate thresholds more optimistic.
- **Data budget:** dry run (`metadata.get_cost`) before every download; at most **$1 per
  firing, $3 per UTC day, $25 in total for the routine** (sum of `cache/download_log.csv` rows
  with `downloaded_at_utc` ≥ 2026-10-02T23:15Z, when the routine started). No MBO without the user's OK. If an item needs more,
  write the exact request and price into `QUEUE.md` under "Needs the user", notify once, and move
  to the next item.
- Never print or commit the API key.
