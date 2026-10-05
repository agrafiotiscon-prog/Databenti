# Research queue (the routine takes the first open item; see ROUTINE.md)

Ordered. Split big items before starting them. Tick `[x]` when done and note the commit.

## Phase 2 leftovers: real-data validation (cached 2024-03-05 data, $0)
- [x] R2.1 (session 5: ratio 1.0 RTH, 0.9999994 full; see mbo-fill-reconciliation-2024-03-05) Re-run `scripts/verify_data.py --date 2024-03-05` (RTH and full) with the new fill
      accounting; confirm `fill_accounted_ratio` ≈ 1.0 and write
      `vault/results/mbo-fill-reconciliation-2024-03-05.md` (diagnosis already done in session 5:
      0.48% hidden iceberg reserve, 0.12% orders modified into the market).
- [x] R2.2 (s6: same-order M in the fill's event; see mbo-iceberg-refills-2024-03-05) (removed: 1,544 → 1,540 RTH, 1,850 → 1,843 full) Describe
      how native refills really look in Databento MBO (answers an open question in MEMORY).
- [x] R2.3 (s6, D-018: synthetic dt=1ms + clips>=2, experimental; spoof descriptive) Calibrate on the real distribution: spoof `min_size` (default 50) and synthetic-iceberg
      `dt` (5 ms; 44,893 synthetic icebergs in one RTH looks far too many). Record the choice and
      the evidence; parameters are fixed BEFORE any strategy uses them.
- [x] R2.4 (s6: found fully-filled modify-into-market pattern; see day-check-2024-03-05-rth) `scripts/plot_day.py --date 2024-03-05 --mbo` visual sanity check; save a screenshot
      or summary to `vault/results/`.

## Phase 3: backtester (vault/04-backtesting/)
- [x] R3.1 (s6: backtest/engine.py + costs.py; null baseline in trials.jsonl) L1 event engine skeleton: replay trades/tbbo in file order, strategy callback sees
      only data with `ts_recv + latency <= now`; market orders fill at the book seen at
      arrival (+ latency); fees from `config/costs.toml`. Tests: no-lookahead (negative
      control), fee arithmetic, one-contract position limits.
- [x] R3.2 (s6: limit/stop/cancel, trade_through + queue_l1; fill-mode check in trials.jsonl) Limit and stop orders with `trade_through` (pessimistic) and `queue_l1` fill modes.
- [x] R3.3 (s6: backtest/metrics.py; DSR/PBO/MC/stress belong to Phase 4) Metrics from `vault/04-backtesting/metrics.md` (per-trade, daily PnL, markouts,
      concentration) + per-year/month tables.
- [x] R3.4 (s6: backtest/hft_adapter.py; book = ours on 3,600/3,600 samples) hftbacktest adapter for tier-B `l3_fifo` calibration (MBO; only on cached days).

- [x] R3.5 (s6 routine 16:15, D-047: maker fills TT 49 / L3 52 / queue_l1 55; keep trade_through; vault/results/fill-calibration-2024-03-05.md) Tier-B calibration run: same strategy under trade_through / queue_l1 / hftbacktest l3_fifo
      on the cached MBO day; report fill-rate and PnL differences (needs a limit-order strategy;
      do it with H-001 in Phase 5 if nothing earlier fits).

## Phase 4: research framework (vault/05-anti-overfitting/)
- [x] R4.1 (s6: data/holdout.py provisional+frozen lock in downloads/loads; research/walkforward.py) Holdout lock in the loader (`config/splits.toml`), walk-forward splitter with embargo.
- [x] R4.2 (s6: research/trials.py hash-chained + budget/space checks; research/registry.py) Append-only trial log `research/trials.jsonl` + hypothesis registry
      `research/hypotheses/*.yaml` (mechanism, space, budget written first).
- [x] R4.3 (s6: research/stats.py; noise negative controls pass) DSR, PBO (CSCV), plateau test, Monte Carlo (block bootstrap + execution MC).
- [x] R4.4 (s6: research/clusters.py + research/gates.py; missing evidence = FAIL) Cluster analysis of trials (effective K, medoids) and the G1–G11 gate report.

## Phase 5: first hypothesis
- [x] R5.1 (s6: research/hypotheses/H-001.yaml, 72 variants, committed before any result) Registry entry H-001: absorption at a profile level + delta divergence → fade; fixed
      stop/target; declared space and budget.
- [x] R5.2 (s6: 238 RTH days cached, total spend $117.15; TBBO calibration days not bought - $2.85 left under the cap) Download RTH trades 2024-11-01..2025-09-30 via `Downloader.fetch_rth` in stages
      (stage 1 Jul-Sep 2025 started s6) + ~8 TBBO calibration days; cumulative cap $120.
      Old text: Price the L1 data it needs (trades/tbbo, RTH). Within the routine budget, use what is
      affordable; a meaningful test needs years (see "Needs the user").
- [x] R5.3 (s6: NOT PROMISING - 70/72 variants lose, median -1.25 ticks/trade; H-001 closed, D-021) (runner ready: scripts/run_h001.py per D-020; run ONCE when stage downloads finish) Run, gate, verdict (promising / not promising / insufficient data).

## Next hypotheses ($0: reuse the 238 cached RTH days; one at a time, mechanism first)
- [x] R6.1 (s6: H-002 intraday momentum + order-flow filter, 16 variants, D-022) Pick the next hypothesis from vault/03-order-flow/evidence-review.md with the strongest
      published support (not footprint folklore); write its registry entry and protocol BEFORE
      running anything. Count H-001's 72 trials in the family/global trial tally.
- [x] R6.2 (s6: scripts/run_hypothesis.py) Generic runner: refactor scripts/run_h001.py into scripts/run_hypothesis.py so new
      hypotheses only add a strategy module.

- [x] H-002 (s6): inconclusive, underpowered (1 year: t = 0.08); closed.
- [x] H-003 (s6): last-hour momentum on 15 y of hourly bars: NOT PROMISING (2,095 OOS trades, t = 0.21,
      6/13 years positive); closed. Do not test volatility-conditioned variants on 2010-2025 (snooped).
- [x] H-004 (s6): follow multi-level sweeps: NOT PROMISING, t = -5.5, 0/16 variants > 0; closed (D-025).
      Fade-sweep variants are contaminated on this data.
- [x] H-005..H-008 (s6, D-026/D-027): see vault/results/leaderboard.md. Best: H-007 pre-FOMC (6/11 gates, not promoted).
- [x] H-009..H-011 (s6, D-029): overnight 5/11, daily reversal 5/11, VWAP fade 3/11 - none promoted.
- [x] H-012..H-013 (s6, D-031): FOMC cycle 6/11 (co-leader with H-007), intraday periodicity negative.
- [x] Placebo tests (s6 routine 12:15, D-032): H-012 demoted (p 0.74, equity drift); H-007 p = 0.063; new gate G12.
- [x] R6.5 (s6): H-005 p 0.84, H-009 p 0.51 -> equity drift.
- [x] H-014 (s6): time-series momentum: not promising (t 0.51, 5/13 years).
- [x] H-015 (s6): macro-announcement days: 0/12 gates, placebo p 0.53; closed.
- [x] R6.6 (s6, D-039: H-016 0/12, H-017 5/12 p 0.43, H-018 5/12 p 0.24 - all closed) Remaining weaker calendar ideas (each long-only -> G12 placebo built in): pre-holiday
      (Ariel 1990), option-expiration week (Stivers & Sun 2013), Monday/weekend reversal. Low priors;
      several cannot reach 200 OOS trades. Register before running; keep spaces tiny.
- [x] H-019 (s6, D-040..D-042): month-end rebalancing fade: run 1 buggy (63/183 months), fixed re-run 1/12, p 0.41; closed.
- [x] R6.7 (s6: H-007 122/122 complete; nothing changes; vault/results/coverage-audit-bars.md) Coverage audit of earlier bar modules (H-005..H-018): count events found vs expected; holiday
      sessions halted before 15:00 CT and Databento's post-expiry rank shift can drop trades via prev_date/px.
      Report only (closed hypotheses are not re-run unless a drop is systematic AND large; then decide + log).
- [x] H-020 (s6 routine 13:16, D-043/D-044): volatility-managed long 8/12 gates, fails G12 (p 0.118), G1, G3; closed.
- [x] H-021 (s6 routine, D-045/D-046): buy after 3-day selloff 3/12, placebo p 0.99; closed.
- [x] R7.1 (s6, D-048/D-049): 26-market daily data ($2.26) + portfolio engine; H-022 trend/carry portfolio: OOS −4.3%/yr, Sharpe −0.28; closed.
- [x] R7.2 (s6, D-050): H-023 combined book registered (trend252 + pre-FOMC), scripts/run_h023.py; development numbers descriptive only: $1M 8.4%/yr Sharpe 0.53 (hindsight), $100k 2.3%/yr.
- [x] R7.3 (2026-10-04, D-052): H-023 holdout CONFIRM by rule (book Sharpe 0.72, +8.7% on $1M; trend +$108k, FOMC -$18k);
      weak evidence (1 year). Holdout spent + re-locked. vault/results/h023-holdout.md
- [x] R6.4 H-007 confirmation: superseded by R7.3 (H-007 is the FOMC sleeve of H-023).

## R8: active research again (user, 2026-10-04: "each routine should do new research, engineering and testing")
Rules: $0 data only (cached: 26 futures daily 2010-06..2025-09, ES hourly 2010..2025-09, 238 RTH trade days);
~$3.4 credit left, spend none without the user. One item per firing. Register (mechanism + space + budget)
BEFORE results; coverage check first (D-042); G1-G12; every variant through trials.append(). Target (D-048):
Sharpe >= 1 net. The 2025-10..2026-10 holdout is SPENT (D-052): no new idea may be checked on it; a
future confirmation needs data after 2026-10-04 (forward test). Prefer ideas that are DIFFERENT payers from trend (the trend sleeve is already H-023).
- [x] R8.1 (2026-10-04: portfolio/signals.py BUILDERS + cross_sectional + momentum_score; run_portfolio.py --hypothesis; tests) Engineering: generic portfolio-hypothesis runner (refactor scripts/run_portfolio.py so a new
      cross-market signal only adds a signal function in portfolio/signals.py), with tests; no new result.
- [x] R8.2 (2026-10-04, D-053: not promising, 1/12, OOS -1.5%/yr, placebo p 0.57; vault/results/h024-report.md) H-024 cross-sectional carry across the 26 markets (Koijen, Moskowitz, Pedersen & Vrugt 2018):
      rank by annualised front/next slope within sector, long top / short bottom, vol-scaled. Payer: hedgers.
- [x] R8.3 (2026-10-04, D-054: not promising, 1/12, OOS -1.3%/yr, placebo p 0.40) H-025 cross-sectional (relative) momentum 3/6/12 m, within-sector ranks (Asness, Moskowitz &
      Pedersen 2013). Small space (<= 6 variants).
- [x] R8.4 (2026-10-04, D-055: 4/12, OOS +3.1%/yr, Sharpe 0.20, placebo p 0.13; best of R8, not promoted) H-026 commodity basis-momentum (Boons & Prado 2019): momentum of front minus second-contract returns.
- [x] R8.5 (2026-10-04, D-056: DOES NOT REPLICATE, t 1.13, placebo p 0.17; H-007 prior lowered) H-027 pre-FOMC drift replication on the other equity-index futures in the universe (daily bars,
      close t-1 -> close t on FOMC days): an out-of-market check of H-007's mechanism, not a new tuned strategy.
- [x] R8.6 (2026-10-04: portfolio/combine.py inverse_vol + ERC, causal trailing weights, vol target; tests/test_combine.py; no result) Engineering: risk-parity sleeve combiner (inverse-vol / correlation-aware weights across passing or
      near-passing sleeves), tested on synthetic data; only combines sleeves registered BEFORE seeing the combo.
- [x] R8.7 (2026-10-04, D-057: H-028 insufficient data, 0/8 variants > 0; closed) Order-flow on the 238 RTH days: trade-imbalance (signed volume) predicting 5-30 min ES returns
      (Chordia & Subrahmanyam 2004 style); 1 year -> expect "insufficient data" on G7; report honestly.
- [x] R8.9 (superseded by R9.7: paper_track.py --live from 2026-10-05) Forward paper-tracking of the trend252 book (daily signals + simulated fills logged, no broker):
      needs the user's OK for ongoing data cost (~$0.06/day for 26 daily bars x2) - listed under Needs the user.
- [x] R8.8 (2026-10-04: vault/04-backtesting/next-ideas-r9.md) When R8.2-R8.7 are done: write the next 3-5 ideas from the literature into this queue (mechanism first).

## R9: forced, scheduled flows outside equities (vault/04-backtesting/next-ideas-r9.md); $0 cached data
- [x] R9.1 (2026-10-04: research/placebo.py + --placebo-draws 200 default; dry run on H-028 8 months: G12 measured, p 0.30, nothing logged) Engineering E-1: random-timing placebo (G12) in scripts/run_hypothesis.py (tick runner), with tests.
- [x] R9.2 (2026-10-04, D-059: 1/12, not promising) H-029 front-running the commodity index roll (GSCI 5th-9th business day; Mou 2011): near/far
      calendar spread via portfolio.signals.near_far_returns; coverage of roll months first; placebo.
- [x] R9.3 (2026-10-04, D-060: 9/12 gates, strongest candidate, not promoted) H-030 Treasury futures month-end (index duration extension / Etula et al. 2020): long ZN/ZB last
      k days; month-end coverage first (H-019 lesson); placebo vs random windows.
- [x] R9.4 (2026-10-04, D-061: 4/12, not promising; calendar in config/treasury_auctions.csv) H-031 Treasury auction cycle (Lou, Yan & Zhang 2013): needs the auction calendar from TreasuryDirect
      (no Databento cost); fetch into config/ if the network allows, else park under "Needs the user".
- [x] R9.6 (2026-10-04, D-062: H-032 CONFIRMS on TN/UB) H-030 confirmation: pre-register a replication on UB + TN daily bars (not used so far; ~$0.1, needs the user's OK)
      with the exact H-030 rule fixed in advance (pre-window, k=3, long), and add H-030 to forward paper tracking (R8.9).
- [x] R9.5 (2026-10-04: scripts/paper_track.py ledger + mark; engine.target_contracts refactor, identical to stored H-022 P&L to 1e-11; replay on Sept 2025 OK) Engineering E-2: forward paper-tracking skeleton for trend252, tested on cached data (running it
      forward waits for the user, R8.9).

## Later: new hypotheses (one at a time, mechanism first; see vault/03-order-flow/evidence-review.md)

## Next (user approved, 2026-10-04)
- [x] R9.7 (2026-10-04: scripts/paper_track.py --live + ROUTINE step 2b; first live day 2026-10-05) Forward paper tracking live: daily fetch of the last few days of ohlcv-1d v.0/v.1 for the 26 markets (cost-guarded, cap $0.05/day),
      run scripts/paper_track.py for the new dates (trend252 + H-030, book = combine.py 15% vol), commit the ledger daily;
      monthly summary vs the descriptive expectation (vault/results/combined-trend-h030-descriptive.md).

- [x] R9.8 (2026-10-04, D-064: micros -> $100k book +5.6%/yr last 5 y) $100k realism: whole contracts make the trend sleeve nearly untradeable at $100k (most contracts too large;
      2023 had no positions). Map the universe to CME micro contracts where they exist (MES, MNQ, M2K, MYM, MGC, SIL,
      MCL, M6E, M6A, M6B, micro ags?) and price the data before asking the user; re-run the $100k book descriptively.

## R10: more independent, low-correlation sleeves (user 2026-10-04: "profits still low, continue until you exceed expectations")
Goal: Sharpe >= 1 net for the book (D-048). Each idea: registry first, coverage, G1-G12, then a confirmation on unseen
instruments/data before it may join the paper book. Prefer $0 cached data; credit left ~$3.3.
- [x] R10.1 (2026-10-04, D-065: 3/12, placebo p 0.88) H-034 equity index turn-of-the-month (Lakonishok & Smidt 1988; McConnell & Xu 2008: returns concentrated in
      the last day + first 3 days of the month; payer: month-start inflows from payroll/pension contributions). ES/NQ/RTY/YM
      daily (cached). G12 placebo vs random 4-day windows is essential (equity drift). Confirmation market if it passes:
      none unseen in equities -> forward only.
- [x] R10.2 (replaced by H-035 month-end rebalancing pressure: 6/12, placebo p 0.047, watch sleeve; D-065) H-035 month-end in short-rate futures (SOFR SR3 / Fed funds ZQ): month-end funding/repo pressure is a
      documented money-market effect; same flow family as H-030 but a different instrument. Needs data (~$0.1?): price first.
- [x] R10.3 (2026-10-04, D-065: 6/12, no gain) H-036 trend sleeve improvement with a PRE-REGISTERED rule only: volatility-managed trend (Moreira & Muir 2017
      apply vol-scaling to factors; Harvey et al. 2018 "The impact of volatility targeting") - scale the trend sleeve by its
      own trailing vol; judged forward-only because trend252 was selected on this data.
- [x] R10.4 (2026-10-04, descriptive: quarter-end windows +17.8 bp vs other month-ends +19.6 bp, year-end +21.1 - no amplification; nothing added) Quarter-end / year-end subset of H-030 (larger index extensions at quarter-ends) - descriptive only (subset
      of a confirmed rule; no new trial unless registered as a separate sizing rule).

## R11 (user: "OK move on"; run in parallel)
- [x] R11.1 (D-066: 5/12, not confirmed by H-040 on 6N/6M) H-037 FX month-end hedge rebalancing (Melvin & Prins 2015)
- [x] R11.2 (D-066: 0/12) H-038 return seasonality, time-series (Keloharju, Linnainmaa & Nyberg 2016)
- [x] R11.3 (D-066: 1/12) H-039 quarter-end USD funding squeeze (Du, Tepper & Verdelhan 2018)

## R12
- [x] R12.1 (2026-10-05, D-067: DOES NOT CONFIRM, Sharpe 0.19, placebo p 0.27; positive but weak) H-041 trend252 unchanged on 12 never-used markets.
- [x] R12.2 (2026-10-05: vault/04-backtesting/next-ideas-r9.md section R13) Next ideas: write 3 mechanism-first ideas (prefer forced flows in rates, the only confirmed family; check the
      vault leaderboard before proposing anything similar to a closed idea). Credit left ~$2.5: no purchases > $0.50 without the user.

## R13 (mechanism tests of the confirmed month-end family; $0 cached data)
- [ ] R13.1 H-042 Treasury curve flattener into month-end (DV01-neutral long ZB/short ZT; confirmation UB/TN vs ZF fixed in advance)
- [ ] R13.2 H-043 mid-month (15th) coupon reinvestment, long ZN/ZB (+TN/UB)
- [ ] R13.3 E-3 scripts/paper_summary.py (monthly paper P&L summary for ROUTINE step 2b; first due 2026-11-02)

## Needs the user
- **(2026-10-04) H-030 confirmation (R9.6):** ~$0.1 of UB/TN daily bars for a pre-registered replication; and/or forward paper tracking. Asked in chat.
- **(2026-10-04) Forward paper tracking of the confirmed trend252 book (R8.9):** a few cents/day of daily bars;
  ~$3.4 credit left. Asked in chat.
- **(session 6, after H-022) Direction for the 15%/yr goal (D-048/D-049) - waiting for the user:**
  (1) accept Sharpe ~0.4-0.5 and confirm a pre-registered combination (trend252 + H-007) on the holdout
  or by paper trading; (2) buy multi-year ES tick data (~$140/yr PAYG or a subscription) for order-flow
  research; (3) leverage (not recommended: ~-60% drawdowns). **Answered 2026-10-04:** option 1 (single
  H-023 holdout run) and resume active research every firing (R8).
- (resolved by D-019: credit spent on 1 year of RTH trades; $117.15 of $120 cap used)
- **Old: Data budget for real backtests.** ES trades cost about $0.55 per full UTC day (tbbo ≈ $0.92):
  one year of trades ≈ $140, more than the remaining pay-as-you-go credit (~$112 after
  session 5). G1 needs ≥ 200 OOS trades and G7 needs several years. Options: Standard plan
  ($199/mo, 1 year of L1 included), a larger pay-as-you-go budget, or accept "insufficient data"
  verdicts. The routine stays within $25 until you decide.
