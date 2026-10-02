---
type: topic
tags: [anti-overfitting]
updated: 2026-10-02
---
# The automated research loop ("constantly improving"), done safely

Unconstrained "keep tweaking until it's profitable" is the **definition of overfitting**. With
enough variants, something always looks profitable in-sample. The loop below can still run
automatically, but "improvement" is defined as **passing the gates in
[methodology](methodology.md)**, never as a higher in-sample number.

## Components
1. **Hypothesis registry** (`research/hypotheses/*.yaml`). Each entry has: id, written mechanism
   ("why would this make money, and who pays?"), direction, horizon, the features used, a
   declared parameter space, and a **trial budget** (e.g. ≤ 200 variants). It is written
   *before* any results are seen.
2. **Runner**: picks the next hypothesis and runs a walk-forward search within its declared
   space and budget, on development data only. The holdout is unreachable: the loader enforces
   this.
3. **Trial log** (`research/trials.jsonl`, append-only): every variant, including failures,
   with its daily PnL saved. Logging is never optional, and the count is never reset.
4. **Evaluator**: computes the DSR (with the true N and the cluster-based effective K), PBO,
   sensitivity heatmaps, **Monte Carlo on every parameter set** (block bootstrap plus execution
   MC, with percentile heatmaps), **cluster analysis** of all trials (picking cluster medoids
   and flagging islands), red flags, and gates G1–G11.
5. **Report**: a Markdown/HTML report per run covering what was tried, how many trials (per
   family and all-time), the gate table, cost and latency stress, and per-year and per-month
   breakdowns. It ends with a plain-English verdict: *promising / not promising / insufficient
   data*.
6. **Change log** (`research/CHANGELOG.md`): one line per run, so it is easy to see how much
   searching has been done over time.

## What the loop is allowed to change
- Parameters **inside** a hypothesis's declared space, until the budget is spent.
- New hypotheses only when a human (or Claude, with the reasoning written down) adds a registry
  entry with a mechanism. Each one counts toward the family's N.
- **Never:** the cost model (except to make it more conservative), the fill mode toward
  optimistic, the data splits, the holdout, or the gate thresholds.

## Scheduling (active since session 5, D-017)
Live version: an hourly routine following [research/ROUTINE.md](../../research/ROUTINE.md) and
working through [research/QUEUE.md](../../research/QUEUE.md). Until Phases 3–4 exist it builds
them; afterwards it runs hypotheses through the gates. The original plan:
A scheduled cloud routine (e.g. weekly) that:
1. Optionally pulls new tier-A data. It goes through the **cost guard**, with a fixed monthly
   budget and no MBO without approval.
2. Runs the next N queued hypothesis evaluations.
3. Commits the trial log and report to a branch and opens a PR for review.
4. **Never trades** (live trading is out of scope), never touches the holdout, and never
   raises its own budget.

The Databento API key must live as a secret in the cloud environment, never in the repo.

## Honest expectation
Given the [evidence review](../03-order-flow/evidence-review.md), the most likely output of the
loop is a well-documented series of "**not promising**" verdicts. That is valuable: it is cheap
compared with losing money live. If something does pass every gate and then the holdout, it
deserves paper trading next, not real money.
