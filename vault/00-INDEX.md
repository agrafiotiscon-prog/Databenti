---
type: index
tags: [index]
updated: 2026-10-02
---
# Knowledge vault: order-flow research with Databento (ES/NQ)

This vault holds what was researched before any further code was written. Each note gives the
facts, where they came from (see [SOURCES](SOURCES.md)), and what they mean for this project.
Where the research contradicted the original project brief, the research wins. Every such change
is listed in the [roadmap](06-roadmap.md) with its reason.

Confidence tags used throughout:
- **[doc]**: stated in primary documentation (Databento, CME, broker fee pages).
- **[paper]**: peer-reviewed or working-paper evidence.
- **[inferred]**: our reading of the docs. It must be verified on real data, and a test or check
  exists or is planned for it.
- **[assumption]**: a modelling choice. It is configurable and gets stress-tested.

## How this vault works (Claude's persistent memory)
- **Claude maintains it.** `CLAUDE.md` at the repo root is auto-loaded into every Claude Code
  session and imports [MEMORY](_memory/MEMORY.md), so the current state, decisions and open
  questions survive context compaction and new sessions.
- [MEMORY](_memory/MEMORY.md): short, always-loaded state (who the user is, where we are,
  what's next).
- [decisions](_memory/decisions.md): append-only decision log (D-001…).
- [project brief](_memory/project-brief.md): the user's own requirements, verbatim.
- `journal/`: one note per session (what was asked, done and found).
- `inbox/`: material the user shares (transcripts, links), each with a summary, an assessment,
  and where it was integrated.
- Tooling: `python tools/vault.py journal|decide|inbox|search|check`. `check` runs in pytest,
  so broken links fail the build.
- **Open in Obsidian:** "Open folder as vault" → `vault/`. Links are relative Markdown links, so
  they work in Obsidian and on GitHub. Durable storage is git: every change is committed and
  pushed.

## Map

| # | Note | Use it for |
|---|---|---|
| ★ | [MEMORY](_memory/MEMORY.md) · [decisions](_memory/decisions.md) · [brief](_memory/project-brief.md) | State, why things are the way they are, what the user asked for |
| ★ | [Journal: session 1](journal/2026-10-02-s1-phase1-data-layer.md) · [session 2](journal/2026-10-02-s2-research-vault.md) · [session 3](journal/2026-10-02-s3-memory-and-robustness.md) | Session history |
| ★ | [Inbox: video, four robustness steps](inbox/2026-10-02-video-four-robustness-steps.md) | User-supplied material |
| 1 | [Databento: schemas, fields, flags](01-databento/schemas-and-fields.md) | What every field means; side/aggressor; flags; prices |
| 1 | [Databento: MBO and book building](01-databento/mbo-book-building.md) | Reconstructing the book, FIFO, snapshots, fills vs cancels |
| 1 | [Databento: symbology and rolls](01-databento/symbology-and-rolls.md) | Why `ES.c.0` is wrong in roll week, and what we do instead |
| 1 | [Databento: timestamps and causality](01-databento/timestamps-and-causality.md) | Which timestamp means "known at"; latency |
| 1 | [Databento: pricing and data plan](01-databento/pricing-and-data-plan.md) | What data to buy and how much history |
| 1 | [Databento pitfalls checklist](01-databento/pitfalls.md) | Pre-flight list for every feature and backtest |
| 2 | [ES contract, sessions, matching](02-market-structure/es-contract-and-sessions.md) | Specs, hours, holidays, FIFO, icebergs, implied |
| 2 | [Costs, fees, slippage](02-market-structure/costs-fees-slippage.md) | Real fee numbers and break-even math |
| 3 | [What the evidence says about order flow](03-order-flow/evidence-review.md) | Prior odds of success, honestly |
| 3 | [Feature definitions (causal)](03-order-flow/feature-definitions.md) | Exact, lookahead-free definitions for Phase 2 |
| 4 | [Fill and latency models](04-backtesting/fill-and-latency-models.md) | Market/limit fill rules, queue models, adverse selection |
| 4 | [Engines compared](04-backtesting/engines-compared.md) | Own engine vs hftbacktest vs NautilusTrader |
| 4 | [Metrics](04-backtesting/metrics.md) | How every number in a report is computed |
| 5 | [Anti-overfitting methodology](05-anti-overfitting/methodology.md) | Splits, walk-forward, CPCV, DSR, PBO, gates |
| 5 | [Automated research loop design](05-anti-overfitting/research-loop.md) | The "constantly improving" routine and its guardrails |
| 6 | [Roadmap, revised](06-roadmap.md) | Phases after research, and what changed |
| - | [Going live later (not now)](07-live-later.md) | What a live bot needs; deliberately out of scope |
| - | [Sources](SOURCES.md) | Every URL used |

## The ten rules that came out of the research

1. **Causality uses `ts_recv` plus our latency.** Nothing may act on an event before
   `ts_recv + latency`. → [timestamps](01-databento/timestamps-and-causality.md)
2. **Never trade the expiring ES contract in roll week.** Switch on the CME roll Thursday, eight
   days before expiry. → [rolls](01-databento/symbology-and-rolls.md)
3. **Costs are about 1.4 ticks per ES round trip even before slippage**, if both entry and exit
   are market orders. A strategy whose gross edge per trade is below that is dead on arrival.
   → [costs](02-market-structure/costs-fees-slippage.md)
4. **Order flow predicts mostly at horizons of seconds** (about two price changes), where
   co-located HFTs compete. Our prior that a retail-latency order-flow strategy is profitable
   should be low. → [evidence](03-order-flow/evidence-review.md)
5. **A pessimistic limit fill means price traded *through* the limit.** A touch is not a fill.
   Optimistic fills are the most common way order-flow backtests lie.
   → [fills](04-backtesting/fill-and-latency-models.md)
6. **Passive fills suffer adverse selection.** The fills you get tend to be the ones you didn't
   want. Measure it with markouts.
7. **MBO is expensive and short-history.** Do strategy research on L1 data (trades plus BBO)
   over years. Use MBO over recent months to calibrate fills and to test MBO-only features.
   → [data plan](01-databento/pricing-and-data-plan.md)
8. **In MBO, filled resting orders are removed by later `C`/`M` records, and every UTC midnight
   brings a synthetic snapshot.** Naive "cancel" or "add" counts are wrong.
   → [MBO](01-databento/mbo-book-building.md)
9. **Every trial is logged, and selection is penalised** with the Deflated Sharpe Ratio and PBO,
   using the true trial count. → [methodology](05-anti-overfitting/methodology.md)
10. **The holdout is touched once per candidate, with the user's sign-off.** Nothing is tuned
    after that.
11. **Robustness is judged across the whole parameter grid, not at one point.** That means
    heatmaps, Monte Carlo on *every* parameter set (selecting on the 5th percentile), and
    clustering of all trials. Choose cluster medoids and reject islands.
    → [methodology §6–6c](05-anti-overfitting/methodology.md)
