---
type: journal
date: 2026-10-02
tags: [journal]
---
# s3 memory and robustness

## 2026-10-02 20:53 UTC
**User asked:** (1) integrate a video checklist: parameter-stability heatmap, Monte Carlo on every parameter set, cluster analysis of all results, IS/OOS + walk-forward; (2) a vault like Obsidian that Claude controls, so that discussions and work persist across context windows and sessions.

**Done:**
- Video summarised and assessed in inbox/2026-10-02-video-four-robustness-steps.md.
- methodology.md extended:
  - §6 heatmap interpretation
  - §6b Monte Carlo on every grid point (trade shuffle, stationary block bootstrap, execution MC with skipped trades and cost draws, parameter jitter; select on the 5th percentile)
  - §6c cluster analysis (López de Prado & Lewis 2019: effective K for DSR, parameter-space regions, pick medoids, reject islands)
  - gates G9–G11
  - note that passing these steps is not 'ready for live'
- Research loop updated to run MC and clustering on every batch.
- Memory system:
  - CLAUDE.md (auto-loaded; imports vault/_memory/MEMORY.md; mandatory vault protocol)
  - _memory/MEMORY.md, decisions.md (D-001..D-011), project-brief.md (user's brief verbatim plus later directives)
  - journal/ for sessions 1–3
  - tools/vault.py (journal, decide, inbox, search, check)
  - tests/test_vault.py (links and frontmatter enforced in pytest)
  - frontmatter on every note
  - vault/.obsidian/app.json (relative Markdown links)

**Verified:** the repo's default branch is claude/loving-ptolemy-glj7ww, so CLAUDE.md is present in new sessions.

**Results:** vault check OK; pytest all green.

**Still waiting on the user:** ES vs MES, data budget, holdout, broker, API key.
