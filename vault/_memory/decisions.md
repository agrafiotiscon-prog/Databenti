---
type: decision-log
tags: [decisions]
---
# Decision log (append-only; newest at the bottom)

Format: `## D-NNN — title (date)`, then **Decision**, **Why**, **Alternatives**, **Status**.
Add entries with `python tools/vault.py decide "title" --decision ... --why ...`.

## D-001 — Stack and repository layout (2026-10-02)
- **Decision:** Python 3.11, the official `databento` client, pandas/numpy/pyarrow, pytest.
  Packages `data/ features/ backtest/ research/`, plus `tests/`. Cache in `cache/` (gitignored).
- **Why:** this is what the user's brief asked for.
- **Status:** active.

## D-002 — Cost guard and per-UTC-day cache (2026-10-02)
- **Decision:** call `get_cost` for **all** missing chunks before downloading anything. Refuse
  above $5 unless the user explicitly approves. Cache one file per (schema, symbol, UTC day),
  with atomic writes.
- **Why:** the user's brief requires it. Databento bills each streamed request again. MBO's
  00:00 UTC snapshot makes UTC-day chunks self-contained.
- **Status:** active.

## D-003 — Do not use bare `ES.c.0`; use a roll-date rule (2026-10-02)
- **Decision:** `ES.c.0` before the roll Thursday (8 days before expiry), `ES.c.1` from then
  until expiry. One contract per session. The offset is configurable.
  *(Offset superseded by D-016: Monday of expiry week, 4 days before expiry.)*
- **Why:** Databento's `c` rule rolls only at expiry, so the data would sit on a dying contract
  for about a week each quarter.
- **Alternatives:** `ES.v.0` (lags a day, and may be distorted by spread-leg volume), or raw
  symbols (formats vary between 1- and 2-digit years).
- **Status:** active. The crossover day is to be verified on real data (open question).

## D-004 — Two-tier data design (2026-10-02)
- **Decision:** research on years of L1 data (`trades`, `tbbo`/`mbp-1`). Use MBO only for recent
  months to calibrate fills and for MBO-only features.
- **Why:** MBO cost, and the Standard plan includes only 1 month of L2/L3. Statistical power
  needs years.
- **Status:** active.

## D-005 — hftbacktest for L3 FIFO fills instead of our own MBO queue simulator (2026-10-02)
- **Decision:** our own small L1 event engine for research; hftbacktest's `L3FIFOQueueModel`
  plus a latency model to calibrate it on MBO.
- **Why:** a mature, Databento-compatible implementation already exists, so writing our own
  adds bug risk. Caveat: filter `action == 'N'` before its converter.
- **Status:** planned (Phase 3).

## D-006 — Latency-driven slippage, and cost/latency stress tests (2026-10-02)
- **Decision:** default 100 ms decision-to-exchange latency; fills are evaluated at arrival.
  Every report is rerun at fees ×1.5 and ×2 and at latency 250 ms and 500 ms.
- **Why:** slippage is correlated with signals that fire in fast markets.
- **Status:** planned (Phase 3).

## D-007 — Loader preserves file order (2026-10-02)
- **Decision:** never re-sort records within or across a symbol's chunks. Refuse to mix
  symbols in one frame.
- **Why:** CME FIFO priority is carried by Databento's message order, and snapshot records
  carry inaccurate `ts_recv` values.
- **Status:** done.

## D-008 — Statistical gates (2026-10-02)
- **Decision:** walk-forward, DSR, PBO (CSCV), t ≥ 3 hurdle, ±20% plateau, concentration
  flags, ≥ 200 trades; gates G1–G8.
- **Why:** selection bias and multiple testing.
- **Status:** planned (Phase 4).

## D-009 — Gated research loop instead of "improve until profitable" (2026-10-02)
- **Decision:** a hypothesis registry with trial budgets, an append-only trial log, the
  evaluator, and reports. The loop may never touch the holdout, the cost model or the gates.
- **Why:** unconstrained search manufactures false positives.
- **Status:** planned (Phase 5).

## D-010 — Vault as Claude's persistent memory (2026-10-02)
- **Decision:** `CLAUDE.md` (auto-loaded) imports `vault/_memory/MEMORY.md`. The protocol
  requires writing knowledge, decisions, inbox items and journals to the vault and pushing every
  turn. `tools/vault.py` provides journal, decide, search and check. The vault is
  Obsidian-compatible (relative Markdown links, frontmatter, `.obsidian/` settings).
- **Why:** the user asked for a vault Claude controls, so that nothing is lost across context
  windows and sessions. The container is ephemeral; git is the durable store.
- **Status:** active.

## D-011 — Monte Carlo on every parameter set, and cluster analysis (2026-10-02)
- **Decision:** add MC (block bootstrap, execution MC, trade shuffle) for **every** grid point,
  with selection on the 5th percentile. Cluster all trials by PnL correlation to get the
  effective K for the DSR and to find regions, then pick cluster medoids. New gates G9–G11.
- **Why:** a video checklist from the user, cross-checked against López de Prado & Lewis
  (2019). Its claim that passing these steps means "deploy live" is rejected: the holdout and
  paper trading are still required.
- **Status:** planned (Phase 4).

## D-012 — Target instrument: ES (2026-10-02)
- **Decision:** Research and cost model target ES first (fees ~0.36 tick/RT). MES results can be reported under its own cost profile later.
- **Why:** User choice (session 4). ES fees per tick are ~2.8x lower than MES, so small order-flow edges have a chance; capital (~$22-24k margin) is the user's concern for later.
- **Alternatives:** MES (1/10 margin, ~1 tick/RT fees); research ES and trade MES.
- **Status:** active.

## D-013 — Databento billing: pay-as-you-go (2026-10-02)
- **Decision:** Usage-based billing, starting with the $125 free credit. The $5 per-request cost guard stays; ask before anything larger.
- **Why:** User choice (session 4). Cheapest way through Phase 1b-2; the Standard plan can be revisited when multi-month L1 pulls start.
- **Alternatives:** Standard plan $199/mo (1y L1 + 1m MBO included).
- **Status:** active.

## D-014 — Final holdout = most recent 12 months (2026-10-02)
- **Decision:** Reserve the last 12 months of available tier-A data as the final holdout. The exact start date is frozen in config/splits.toml at the first multi-month data pull. The loader will refuse those dates without research/HOLDOUT_UNLOCK (Phase 4).
- **Why:** User choice (session 4). This tests on the newest regime, the one that would actually be traded.
- **Status:** active.

## D-015 — Broker fees: IBKR default, switchable (2026-10-02)
- **Decision:** config/costs.toml holds per-broker profiles. Default ibkr_tiered (ES $2.255/side all-in). Other brokers are added when the user picks one.
- **Why:** User not sure yet (session 4). IBKR figures are verified from its fee pages; the exchange fee is the same for all non-members, so only the commission differs.
- **Status:** active.

## D-016 — ES roll rule: Monday of expiry week (days_before 8 -> 4) (2026-10-02)
- **Decision:** DEFAULT_ROLL_DAYS_BEFORE_EXPIRY = 4 in data/contracts.py: from the Monday of expiry week to expiry, use ES.c.1. This replaces the roll-Thursday convention (8) from the brief and the research note.
- **Why:** Real data. scripts/roll_history.py (ohlcv-1d, ES.c.0 vs ES.c.1, 27 rolls 2019-03..2025-09, $0.04): every roll from 2022-06 to 2025-09 (14 in a row) crossed on the Monday of expiry week. Wrong-contract days: rule 4 = 11 (all in the old regime), rule 7 = 16, rule 8 = 43, previous-day volume (like ES.v.0) = 27. The 2024-03 RTH trades check (verify-roll-2024-03) agrees: c.0 still out-traded c.1 3:1 on Fri 03-08, and c.1 led from Mon 03-11. Calendar-spread legs print equally in both outrights, so they cancel in the comparison. The rule uses only the calendar (no lookahead). The data ends 2025-10-01, before the future 12-month holdout; daily bars do not freeze holdout_start (D-014 is about tier-A order-flow pulls).
- **Alternatives:** 8 (Thursday convention): 2 wrong days per recent roll. 7: right before mid-2022, 1 day early since. ES.v.0: always 1 day late. A per-roll data-driven switch: lookahead risk.
- **Status:** active.

## D-017 — Hourly automated research routine (2026-10-02)
- **Decision:** A routine (trig_01SxDd7cr6pA7egPMDYvJNAH) fires into this session every hour at :15 UTC and works through research/QUEUE.md one bounded unit at a time, following research/ROUTINE.md. It continues across phases (Phase 2 leftovers -> Phase 3 backtester -> Phase 4 framework -> Phase 5 hypotheses) and notifies the user at each phase end instead of stopping.
- **Why:** User request (session 5): a routine every 30 min that researches, tests, adjusts, logs, keeps what is realistically more profitable and implements it if the backtest shows a true edge. The platform minimum interval is 1 hour. 'Keep' is defined as passing all gates G1-G11 out-of-sample after realistic costs (research-loop note), never a higher in-sample number, because an unconstrained loop manufactures false positives. Budget guard: <= $1/firing, <= $3/day, <= $25 total, no MBO without asking (D-013). This changes the 'stop after each phase' rule for the routine: it notifies instead.
- **Alternatives:** Fresh session per firing (would lose the local data cache and re-pay for downloads); weekly schedule as in the original research-loop note; 30-min chaining via one-shot reminders (would work around the platform limit, rejected).
- **Status:** active.

## D-018 — MBO detector calibration: synthetic icebergs experimental, spoof label descriptive (2026-10-03)
- **Decision:** synthetic_icebergs defaults dt 5ms -> 1ms and new min_clip_size=2 (1-lot clips ignored); the feature is marked EXPERIMENTAL and must not be used by strategies until it beats chance on more days. spoof_like_events keeps min_size=50 but is labelled descriptive only. Fixed before any strategy has used either.
- **Why:** scripts/calibrate_mbo.py on 2024-03-05 RTH (cached, $0, no strategy outcomes used; vault/results/mbo-calibration-2024-03-05-rth.md). Synthetic icebergs: the same-size share of adds right after a level trades out vs 1 s later gives precision about +2% for all clips (pure chance; 23k-45k chains/day were noise), +27% at dt=1ms for clips >= 2 lots, +11% at 5ms, and noisy beyond. Spoof: about 45% of all far adds (>= 4 ticks, 1-50 lots) are pulled untouched within 10 s; >= 50-lot orders (168 that day) are pulled less often (17-27%), so the label carries no excess-pull information. One day only: recheck when more MBO days exist (MBO needs the user's OK).
- **Alternatives:** Keep 5ms/any clip (noise); drop the features entirely (keep them for later validation instead); raise min_size further (too few events to measure).
- **Status:** active.

## D-019 — Data budget = the $125 credit; buy ~1 year of RTH trades (2026-10-03)
- **Decision:** User authorised spending up to the $125 Databento credit (session 6). Hard cumulative cap $120 (5 USD margin), enforced in code from cache/download_log.csv + the $10.02 spent before that log existed. Purchase: ES trades, RTH window only, 2024-11-01..2025-09-30 (~230 days, ~$103) for development; ~8 TBBO RTH days (~$6) to calibrate fills. Trades-only backtests rebuild bid/ask from aggressor prints (backtest.engine.l1_from_trades).
- **Why:** Pricing (2026-10-03): one year of tbbo $232, trades full-day $139, trades RTH-window $0.449/day (19% cheaper) -> ~1 year fits. bbo-1s/ohlcv lack per-trade aggressor side, so no order flow. On 2024-03-05 the rebuilt bid/ask equals TBBO's pre-trade quote 81% of the time, otherwise +-1 tick, mean bias +0.017 ticks (slightly pessimistic); calibration days measure each strategy's own fill error. The most recent pre-holdout year is used (closest regime). Holdout_start freezes at 2025-10-03 with this first multi-month pull (D-014). Limitation: one year cannot satisfy G7 (>= 60% of years) - verdicts will say so.
- **Alternatives:** tbbo for ~5 months (fewer trades, exact quotes); full-day trades for ~9 months; Standard plan $199/mo (outside the credit).
- **Status:** active.

## D-020 — H-001 evaluation protocol (fixed before any result) (2026-10-03)
- **Decision:** Data: RTH trades 2024-11-01..2025-09-30 (D-019). Walk-forward: train 6 months, test 1 month, step 1 month, embargo 1 trading day (research.walkforward with these arguments). In each train window, choose the variant with the highest block-bootstrap 5th-percentile net PnL at 1.5x fees (mean block 7 days, 500 sims); apply it unchanged to the next test month; concatenate test months = OOS. Report: OOS metrics and gates G1-G11 via research.gates; DSR with N = 72 (H-001 trials) and with cluster-based K; PBO via CSCV (S = 8 blocks, so each block holds >= 2 weeks) over all 72 variants' daily PnL on the full development set; stress at 1.5x/2x fees and 250/500 ms latency; per-month table. Every variant is logged via research.trials.append.
- **Why:** The default 12/3/3 walk-forward needs >= 15 months; only ~11 months are affordable. 6/1/1 gives ~5 OOS months with monthly re-selection. Selection on the MC 5th percentile follows methodology 6b (robust objective, not the mean). S = 8 because 16 blocks of ~14 days would be too short for stable per-block Sharpe. Fixing all of this now, before the first H-001 number exists, removes the freedom to choose a favourable protocol afterwards.
- **Alternatives:** Single train/test split (one OOS window, less evidence); 12/3/3 (no folds); selecting on mean IS PnL (luck-prone).
- **Status:** active.

## D-021 — H-001 closed: not promising (2026-10-03)
- **Decision:** Close H-001 (status: closed). Its 72 logged trials remain in research/trials.jsonl and count in future DSR deflation.
- **Why:** Single evaluation per D-020 on 238 RTH days (2024-11-01..2025-09-30): all gates fail; 70 of 72 variants lose after costs (median -1.25 ticks/trade); the 2 positive variants are low-trade noise; PBO 0.16, DSR 0.001 (N=72) / 0.01 (K=18). Gate code reports 'insufficient data' (OOS trades 14 < 200) but the family-wide loss makes the substantive verdict 'not promising'. Report: vault/results/h001-report.md.
- **Status:** active.

## D-022 — H-002 registered and its evaluation protocol fixed (before any result) (2026-10-03)
- **Decision:** H-002 intraday momentum (research/hypotheses/H-002.yaml, 16 variants). Protocol identical to D-020: same 238 cached RTH days, walk-forward 6/1/1 with 1-day embargo, selection on block-bootstrap 5th-pct net at 1.5x fees, DSR with N = this family (16) AND with the global count including H-001 (88), PBO via CSCV S=8, stress 1.5x/2x fees and 250/500 ms. Evaluated once via scripts/run_hypothesis.py.
- **Why:** Chosen from vault/03-order-flow/evidence-review.md section 7: minutes-scale horizon, once-a-day event, peer-reviewed evidence (Gao et al. 2018; Baltussen et al. 2021) with a stated payer (end-of-day hedging flows); order flow enters only as a confirmation filter. Small space (16) keeps deflation mild. Known limits: ~200-240 trades over the year at most, so G1 (>= 200 OOS) and G7 (multi-year) cannot pass - the best possible verdict this round is 'insufficient data'; a clear negative is still informative.
- **Alternatives:** OFI at seconds horizons (best evidence but killed by 100 ms latency); iceberg/spoof features (no MBO budget, noisy labels).
- **Status:** active.

## D-023 — H-003 protocol (bars, 15 years), fixed before any data is downloaded (2026-10-03)
- **Decision:** H-003 (research/hypotheses/H-003.yaml, 4 variants). Walk-forward on calendar years: train 3 years, test 1 year, step 1 year, 1-trading-day embargo (folds from research.walkforward with train_months=36, test_months=12, step_months=12). Selection in each train window: highest block-bootstrap 5th-pct net PnL with fees x1.5 (mean block 7 days, 500 sims). Base cost: 1 tick adverse per side + fees; stress: 2 ticks adverse per side + fees x1.5. G8 substitute for bar data (no tier-B fills possible): OOS net PnL keeps its sign with +1 extra tick per side. G2 uses the stress scenario. DSR with N = all hypothesis trials so far (92). PBO via CSCV with S = 16 (15 years). Evaluated once; download ohlcv-1h ES.c.0 + ES.c.1 2010-06..2025-09 (priced $1.77, cap $120 respected).
- **Why:** H-002 showed a once-a-day strategy needs ~15 years for power; hourly bars give that for $1.77. Costs are deliberately pessimistic because bars carry no quotes. The G8 substitute and every threshold are fixed now, before any data exists locally.
- **Status:** active.

## D-024 — H-002 inconclusive and H-003 not promising: intraday momentum into the close has no reliable edge in ES (2026-10-03)
- **Decision:** Close H-002 (inconclusive, underpowered) and H-003 (not promising). Do not re-test conditional variants (e.g. high-volatility only) on 2010-2025 data: the idea came from seeing H-003's yearly results.
- **Why:** H-002: 1 year of trades, OOS 53 trades, t = 0.08. H-003: 15 years of hourly bars, 2,095 OOS trades over 13 years, t = 0.21, positive in 6/13 years, PBO 0.03, DSR 0.002 (N=92), stress -$49.9k. Total data spend $118.92 of the $120 cap.
- **Status:** active.

## D-025 — H-004 registered; protocol = D-020 (via scripts/run_hypothesis.py) (2026-10-03)
- **Decision:** H-004 sweep continuation (16 variants) is evaluated once with scripts/run_hypothesis.py on the 238 cached RTH days: walk-forward 6/1/1, 1-day embargo, selection on bootstrap 5th-pct net at 1.5x fees, DSR with N = all hypothesis trials (108 incl. this family), PBO S=8, stress 1.5x/2x fees and 250/500 ms.
- **Why:** Uses cached data ($0, budget nearly spent); intraday event strategy with many trades, so one year has power. Prior is low (stated in the registry).
- **Status:** active.

## D-026 — H-004 closed: following sweeps loses (t = -5.5) (2026-10-03)
- **Decision:** Close H-004. Do not test fade-the-sweep variants on the 2024-11..2025-09 trade data (idea derived from this result).
- **Why:** Single evaluation (D-020 protocol): OOS 202 trades, -$6,124, -2.06 ticks/trade, t = -5.5; 0/16 variants positive; gross edge about -0.7 ticks (post-sweep reversion at 100 ms latency). Hypothesis trials now 108.
- **Status:** active.

## D-027 — Batch registration H-005..H-008 and their protocols (before any result) (2026-10-03)
- **Decision:** Bars hypotheses H-005 (turn of month), H-006 (gap fade), H-007 (pre-FOMC drift) use the D-023 protocol (15 y hourly bars, walk-forward 3 y / 1 y, selection on bootstrap 5th pct at 1.5x fees, 1 tick adverse per side + fees, stress 2 ticks + fees x1.5, G8 substitute = sign survives +1 tick per side). H-008 (5-min order-flow imbalance fade) uses the D-020 protocol on the 238 cached RTH days. Each is evaluated once; DSR uses the global hypothesis trial count (126 after this batch). 'Best' = the hypothesis passing the most gates on OOS data; if none passes all, none qualifies. FOMC dates: config/fomc_dates.csv from federalreserve.gov (non-meeting statements, notation votes, conference calls, unscheduled meetings removed; 2025-09-17 restored by hand).
- **Why:** User asked to continue through all hypotheses to find the best (session 6). Registering the whole batch first fixes the family before any of its results are seen; small spaces keep deflation honest.
- **Status:** active.

## D-028 — Leaderboard after 8 hypotheses: H-007 best candidate, nothing promoted (2026-10-03)
- **Decision:** Close H-005, H-006, H-008 (no edge) and H-007 (trial budget spent). H-007 (pre-FOMC drift, 24 h window) is the best candidate (6/11 gates) but is NOT promoted. Its next step needs the user: a single holdout evaluation (create research/HOLDOUT_UNLOCK) and/or forward paper trading of the fixed rule. No re-tuning on development data.
- **Why:** Single evaluations (D-026). H-007 OOS 98 trades, +$21.3k, t = 1.95, 8/13 years positive, PBO 0.002, cluster-K DSR 0.98, survives stress; fails G1 (few events), G3 (raw-N DSR with 126 trials), G5/G10 (2-variant space), G6 (concentration). H-005 t = 0.12, H-006 t = 0.59 (0/4 variants positive full period), H-008 t = 0.18 (0/8). Report: vault/results/leaderboard.md.
- **Status:** active.

## D-029 — User: keep researching without confirmation requests; batch H-009..H-011 registered (2026-10-03)
- **Decision:** Per the user (session 6: 'only confirm if you are sure ... continue'): no confirmation requests; notify only when a candidate passes ALL gates G1-G11 (ROUTINE.md step 7 updated). H-007 holdout/paper steps stay parked until something is certain. Registered before any result: H-009 overnight drift (4), H-010 daily reversal (4) on 15 y hourly bars (D-023 protocol), H-011 VWAP-deviation fade (4) on the cached trades (D-020 protocol). Global hypothesis trials after this batch: 138.
- **Why:** User instruction; batch registration fixes the family before results.
- **Status:** active.

## D-030 — H-009..H-011 closed; leaderboard updated (H-007 still best, nothing promoted) (2026-10-03)
- **Decision:** Close H-009 (overnight drift, 5/11), H-010 (daily reversal, 5/11), H-011 (VWAP fade, 3/11).
- **Why:** Single evaluations. H-009: 2,552 OOS trades, +$68.5k, t = 1.05, 9/13 years, negative at 2 ticks/side, PBO 0.63. H-010: 1,074 trades, +$83.0k, t = 1.38, 2020 alone +$75k, 6/13 years. H-011: 256 trades, t = 0.68, 0/4 variants positive. Hypothesis trials: 138.
- **Status:** active.

## D-031 — Batch H-012..H-013 registered before any result (2026-10-03)
- **Decision:** H-012 FOMC-cycle even weeks (2 variants) and H-013 intraday periodicity (4 variants), both on 15 y hourly bars with the D-023 protocol. Global hypothesis trials after this batch: 144.
- **Why:** Published mechanisms (Cieslak, Morse & Vissing-Jorgensen 2019; Heston, Korajczyk & Sadka 2010) with many trades -> statistical power on cached data at $0.
- **Status:** active.

## D-032 — H-012 co-leader with H-007 (Fed-calendar effects); H-013 negative; nothing promoted (2026-10-03)
- **Decision:** Close H-012 (6/11 gates, co-leader) and H-013 (reliably negative). No combined Fed-calendar rule on 2010-2025 (post-hoc).
- **Why:** H-012: 226 OOS trades, +$82.0k, t = 1.23, 9/13 years, positive under stress. H-013: 637 trades, -$36.4k, t = -2.14, 0/4 variants. Hypothesis trials: 144.
- **Status:** active.

## D-033 — New gate G12 (placebo / random-timing benchmark); H-012 demoted (2026-10-03)
- **Decision:** Add G12 to research/gates.py: a candidate must beat a placebo or random-timing benchmark at one-sided p <= 0.05 (missing = FAIL). H-012 is demoted (placebo p ~ 0.74). H-007 stays the best candidate with placebo p = 0.063 (not significant at 5%).
- **Why:** scripts/placebo_fed.py: H-012's even-week rule with the FOMC calendar shifted 1-30 trading days earns as much in 22/30 cases (median $117k vs $75k real) -> its profit is equity drift. G1-G11 had no benchmark check, so long-only rules in a rising market could look good. Adding a gate only makes promotion harder (never more optimistic).
- **Status:** active.

## D-034 — G12 placebo for H-005/H-009 (both drift); H-014 time-series momentum registered (2026-10-03)
- **Decision:** H-005 and H-009 fail the placebo (p 0.84 and 0.51): their totals are equity drift. Register H-014 time-series momentum (long/short, 4 variants, D-023 protocol + G12 random-sign-timing placebo) before any result. Global trials after it: 148.
- **Why:** scripts/placebo_bars.py results; H-014 chosen because it is long/short (immune to pure drift) with a strong published literature and enough round trips over 13 OOS years.
- **Status:** active.

## D-035 — H-014 closed (not promising) (2026-10-03)
- **Decision:** Close H-014 time-series momentum.
- **Why:** Single evaluation: 361 OOS trades, +$47.7k, t = 0.51, 5/13 years positive, lookback choice unstable across folds; all variants positive full-period consistent with long bias in a rising market. Trials: 148.
- **Status:** active.

## D-036 — H-015 macro-announcement premium registered; G12 measured inside the run (2026-10-03)
- **Decision:** Register H-015 (6 variants, D-023 protocol). The bars runner now computes G12 when a strategy module provides placebo(); H-015's placebo draws random non-event, non-FOMC days with the same window. Release dates: config/macro_dates.csv from bls.gov. Global trials after it: 154.
- **Why:** Savor & Wilson 2013 / Ai & Bansal 2018 give a published mechanism with ~24 events per year (G1 reachable over 13 OOS years). Long-only, so the placebo is mandatory (lesson of D-032). Note: one fetch to bls.gov carried the user's email in its User-Agent by mistake; not repeated.
- **Status:** active.

## D-037 — H-015 closed (no announcement premium) (2026-10-03)
- **Decision:** Close H-015.
- **Why:** Single evaluation: 165 OOS trades, -$6.1k, t = -0.28, 0/12 gates; G12 placebo p = 0.53 (jobs/CPI days not better than random days). Trials: 154.
- **Status:** active.

## D-038 — Batch H-016..H-018 registered before any result (2026-10-03)
- **Decision:** Weaker calendar ideas: H-016 pre-holiday (2), H-017 option-expiration week (2), H-018 Monday reversal (2); D-023 protocol, G12 placebo built in for the long-only H-016/H-017. Global trials after this batch: 160.
- **Why:** User: continue testing. Remaining published calendar effects testable on cached data at $0; priors low and stated.
- **Status:** active.

## D-039 — H-016..H-018 closed (no calendar effect beyond drift) (2026-10-03)
- **Decision:** Close H-016 (pre-holiday), H-017 (OPEX week) and H-018 (Monday reversal) as not promising; R6.6 done.
- **Why:** Each run once: H-016 0/12 gates (31 OOS trades, t -0.45, placebo p 0.54); H-017 5/12 (86 trades, t 0.83, placebo p 0.43 vs random non-OPEX 4-day holds); H-018 5/12 (329 trades, t 1.64, placebo p 0.24 vs the same fade on Tue-Fri; gains concentrated in 2022/2025). H-018's G12 placebo was written into the module before any result (stricter only). Global hypothesis trials 160. H-007 remains the best candidate, not promoted.
- **Status:** active.

## D-040 — H-019 month-end rebalancing registered before any result (2026-10-03)
- **Decision:** Register H-019 (fade the month-to-date ES move over the last 4 trading days; 2 variants; G12 placebo vs the same fade at non-month-end times).
- **Why:** R6.3: strongest remaining idea with a stated payer (calendar-driven pension/balanced-fund rebalancing, Harvey, Mazzoleni & Melone 2025) testable on cached hourly bars at $0. ES-only proxy (no bond data) is a known weakness; ~12 events/yr means G1 (>= 200 OOS trades) is unlikely - recorded in advance.
- **Status:** active.

## D-041 — H-019 run 1 had a data bug; fixed and re-run once (2026-10-03)
- **Decision:** Keep run 1 logged (2 trials, report kept as h019-report-run1-buggy.md), fix the bug, raise H-019's trial budget 2 -> 4 and re-run exactly once; all 4 trials count in the global N.
- **Why:** Run 1 used only 63 of 183 month-ends: (a) holiday sessions halted before 15:00 CT were treated as trading days, so any month containing one had no signal; (b) the chained daily returns broke at Databento's post-expiry rank shift (c.0 has no 15:00 close on expiry Friday). The loss was systematic (most quarterly-expiry months and holiday months dropped), not random. The fix only restores the registered definition (same contract's 15:00 closes; trading days = days with a 15:00 close) - no parameter or rule change. Run 1 looked good (7/12 gates, placebo p 0.029, 30 OOS trades), so the re-run is NOT motivated by a bad result; both results are reported. Same issue can drop a few trades per year in earlier bar modules that use prev_date across expiry weekends or holidays (no directional bias expected; noted in QUEUE as a check).
- **Alternatives:** Report run 1 as is (rejected: it tested a different, data-filtered sample)
- **Status:** active.

## D-042 — H-019 closed (no month-end rebalancing effect in ES alone) (2026-10-03)
- **Decision:** Close H-019 as not promising; add an event-coverage check to the routine's checklist.
- **Why:** Bug-fixed re-run (D-041) on all 183 month-ends: 1/12 gates, OOS 86 trades, -$10.3k, t -0.34, 6/13 years, placebo p 0.41; full-period variant min_abs_bp0 +6.6 ticks/trade before selection, but selection picked 200 bp every fold and lost. Run 1's 7/12 and p 0.029 came from a sample that systematically dropped holiday and expiry months. 164 hypothesis trials. The ES-only proxy (no bond leg) remains a limitation; a proper equity-minus-bond test would need ZN/ZB data (budget: user).
- **Status:** active.

## D-043 — H-020 volatility-managed exposure registered before any result (2026-10-03)
- **Decision:** Register H-020 (long ES only when trailing realised vol < its 1-year median; 2 variants; G12 via circular shifts).
- **Why:** R6.3: published, different mechanism from the closed calendar family (risk timing, not dates); testable on cached hourly bars at $0. Long-only so G12 decides whether it beats plain drift; low-moderate prior given Cederburg et al. (2020).
- **Status:** active.

## D-044 — H-020 closed (vol-managed long: 8/12 gates but fails G12) (2026-10-03)
- **Decision:** Close H-020; not promoted.
- **Why:** One evaluation: OOS 79 trades, +$182k, stress +$180k, PBO 0.001, 9/13 years > 0, cluster-K DSR 1.0, but G12 placebo p 0.118 (circular shifts of the regime with the same long share earn nearly as much), G1 79 < 200, G3 raw-N DSR 0.56 (per-trade t 3.89 is inflated by month-long holds). Coverage 3,815/3,815 daily returns (D-042 check). 166 hypothesis trials.
- **Status:** active.

## D-045 — H-021 buy-the-selloff registered before any result (2026-10-03)
- **Decision:** Register H-021 (long ES at next 09:00 after a 3-day decline of z <= -1.5/-2.0 sigmas; hold 3/5 days; 4 variants; G12 random entry days).
- **Why:** R6.3: a liquidity-provision mechanism with a named payer (mechanical de-risking flows), different from the closed calendar family and from H-010 (1-day, every day). Testable at $0 on cached hourly bars; ~20-40 signals/yr gives a chance at G1.
- **Status:** active.

## D-046 — H-021 closed (buying sharp selloffs is worse than random days) (2026-10-03)
- **Decision:** Close H-021 as not promising.
- **Why:** One evaluation, coverage 3,750/3,750 z-scores (D-042): 3/12 gates, OOS 94 trades +$14k, t 0.25, MC P(loss) 0.22, PBO 0.31, placebo p 0.987 (random OOS entry days with the same hold earn more). Selloffs in 2018, 2020, 2022, 2025 continued; the 2021 gain (+$42k) carries the total. 170 hypothesis trials.
- **Status:** active.

## D-047 — R3.5 fill calibration: keep trade_through default (2026-10-03)
- **Decision:** Keep trade_through as the engine's default limit-fill model; queue_l1 only as a sensitivity check; G8 unchanged.
- **Why:** 77 passive probes on 2024-03-05: maker fills trade_through 49 vs L3 FIFO (hftbacktest, full MBO) 52 vs queue_l1 55; trade_through has the most adverse 60 s markout (median -1.5 ticks) - conservative, close in count to the reference. queue_l1 is mildly optimistic. One day only.
- **Status:** active.

## D-048 — User target 15%/yr -> Sharpe >= ~1 at a 15% vol target; diversified futures daily data bought (2026-10-03)
- **Decision:** Translate the user's '15% annually' into: annualised net return at a 15% volatility target, i.e. OOS Sharpe >= ~1.0 after costs, and report it for every candidate. Start Phase R7: a diversified CME futures portfolio (26 markets, daily bars, volume-ranked continuous v.0/v.1, 2010-06..2025-09, ~$2.45). Raise the code cap from $120 to $123 (still inside the user's $125 credit, D-019).
- **Why:** User (session 6): '11% over 12 years is really bad, it should be like 15% annually; do robust research and engineering'. Return scales with leverage, so the honest target is risk-adjusted: 15%/yr at 15% vol = Sharpe 1.0 net - top-decile for systematic funds (SG Trend index 2010-2024 roughly Sharpe 0.3-0.5). Single-market ES calendar effects are idle ~97% of the time and cannot reach it without dangerous leverage. The best-documented route to Sharpe ~0.7-1 is diversification across many markets and independent signals (time-series momentum, carry; Moskowitz-Ooi-Pedersen 2012, Koijen et al. 2018, Hurst-Ooi-Pedersen 2017). Daily bars for 26 markets cost ~$2.45 (< $5 guard; total stays < $125 the user approved).
- **Alternatives:** Lever H-007 up (rejected: 8 trades/yr, tail risk, not confirmed); keep mining ES on the same data (rejected: 170 trials already, DSR penalty grows)
- **Status:** active.

## D-049 — H-022 closed (diversified trend/carry portfolio fails out of sample) (2026-10-03)
- **Decision:** Close H-022 as not promising; do not select trend252 after the fact; report the user's target as unmet by the classic recipe.
- **Why:** One evaluation, coverage checked (D-042), carry signs verified: walk-forward OOS -4.3%/yr at 15.3% vol (Sharpe -0.28), 4/13 years > 0, placebo p 0.96, stress -$847k on $1M. Full-period trend252 Sharpe 0.41 matches public trend indices after 2010, but choosing it now would be hindsight. 174 hypothesis trials. Spend ~$121.2 of the $125 credit.
- **Status:** active.

## D-050 — User chose option 1 (continue): pre-register combined book H-023 for a single holdout / paper confirmation (2026-10-03)
- **Decision:** Register H-023 = H-022 trend252 portfolio + H-007 lm24h ES sleeve, no parameters, with pass/fail criteria fixed before any holdout data is read. Development-period numbers for the book are descriptive only. The holdout is read only after the user's explicit go (unlock file).
- **Why:** User: 'Continue' after being told option 1 is the default. Both components were selected after seeing results, so only untouched data can test them. Holdout data for 2025-10..2026-10 (26 markets daily + ES hourly) costs < $0.5, inside the remaining ~$3.7.
- **Status:** active.

## D-051 — H-023 holdout unlocked by user; routine resumes research (R8) (2026-10-04)
- **Decision:** User authorised the single H-023 holdout evaluation (research/HOLDOUT_UNLOCK created on their instruction, 2026-10-04) and asked that every routine firing resume new research, engineering and testing; QUEUE R8 added ($0 cached data only). After the H-023 run the unlock file is removed again so later research cannot touch the holdout.
- **Why:** User message 2026-10-04: 'do that and also each routine should do new research now, engineering and testing'. Re-locking keeps the holdout unseen by new hypotheses, which are not pre-registered against it.
- **Status:** active.

## D-052 — H-023 holdout: CONFIRM by pre-registered rule, weak evidence; holdout spent and re-locked (2026-10-04)
- **Decision:** H-023 evaluated once on the holdout 2025-10-03..2026-10-02: book +$90k on $1M (8.7%, Sharpe 0.72, maxDD -8.6%); trend sleeve +$108k (Sharpe 0.89), FOMC sleeve -$18k (8 trades). Verdict CONFIRM by the D-050 criteria. H-023 closed; research/HOLDOUT_UNLOCK removed. Trend252 portfolio becomes the reference sleeve; H-007 is not promoted on its own.
- **Why:** Criteria fixed before the run (net > 0, Sharpe >= 0.4, trend net > 0) were all met. But one year has Sharpe SE ~1, the FOMC sleeve lost, and at $100k the book made 1.6%, so this is a passed falsification test, not proof. The used year may not be reused for selection.
- **Status:** active.

## D-053 — H-024 cross-sectional carry: not promising, closed (2026-10-04)
- **Decision:** H-024 evaluated once (4 variants): 1/12 gates, OOS -1.5%/yr, Sharpe -0.10, placebo p 0.57; closed. No FX/equity-only carry re-test on this data (would be post-hoc selection).
- **Why:** Pre-registered protocol and gates; the only profitable sectors (equity, FX) were identified after seeing results, so testing them now would be snooping. A future FX-carry idea needs fresh data or an independent prior.
- **Status:** active.

## D-054 — H-025 cross-sectional momentum: not promising, closed (2026-10-04)
- **Decision:** H-025 evaluated once (4 variants): 1/12 gates, OOS -1.3%/yr, Sharpe -0.09, PBO 0.45, placebo p 0.40; closed. Relative-value (cross-sectional) premia on this 26-market universe: two failures (H-024, H-025); deprioritise further cross-sectional ideas unless the universe grows.
- **Why:** Pre-registered protocol; both cross-sectional books lose after costs, with thin sectors (2-6 names) and gains only in equities, which looks like drift.
- **Status:** active.

## D-055 — H-026 commodity basis-momentum: not promising (4/12), closed (2026-10-04)
- **Decision:** H-026 evaluated once (4 variants): 4/12 gates, OOS +3.1%/yr, Sharpe 0.20, placebo p 0.13, all variants profitable full-period; closed. Not combined with the trend book now (would be selection on development data); candidate for a future pre-registered forward test if more data is approved.
- **Why:** Fails significance, PBO, MC and G12. The ex-energy result was seen only after the run, so no sub-universe re-test.
- **Status:** active.

## D-056 — H-027 pre-FOMC replication on NQ/RTY/YM: does not replicate; H-007 prior lowered (2026-10-04)
- **Decision:** H-027 (fixed, 1 trial): pooled +$144k over 122 FOMC days but t 1.13, placebo p 0.17 vs random days -> DOES NOT REPLICATE; closed. With the H-023 holdout FOMC sleeve loss (-$18k), H-007 is no longer treated as a candidate; the FOMC sleeve is dropped from future combined-book plans.
- **Why:** Pre-registered criteria (t >= 2, placebo p <= 0.05) not met; the effect is indistinguishable from equity drift post-2010, consistent with the literature on the drift's decline.
- **Status:** active.
