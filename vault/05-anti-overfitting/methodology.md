---
type: topic
tags: [anti-overfitting]
updated: 2026-10-02
---
# Anti-overfitting methodology

> "Standard statistical techniques designed to prevent regression over-fitting, such as
> hold-out, tend to be unreliable and inaccurate in the context of investment backtests."
> (Bailey, Borwein, López de Prado, Zhu, *The Probability of Backtest Overfitting*)

A single holdout is not enough on its own. Selection bias grows with every variant tried. The
tools below measure and penalise it.

## 1. Data splits (frozen in `config/splits.yaml`, hashed)
- Chronological only.
- **Final holdout** = the most recent block, proposed to be the **last 12 months** of available
  tier-A data. The loader refuses holdout dates unless `research/HOLDOUT_UNLOCK` exists. That
  file is written only by the user, and every holdout evaluation is logged.
- **Development** = everything before the holdout. Within it:
  - **Walk-forward**: e.g. train 12 months → test 3 months, stepping 3 months (rolling, with an
    anchored variant). The performance metric is the **concatenation of test segments only**.
  - **Embargo** of 1 trading day between train and test. Intraday strategies are flat by the
    session close, so purging beyond that is unnecessary. Strategies that hold overnight need
    purging per López de Prado.
- Optional **CPCV** (combinatorial purged cross-validation) to get a *distribution* of OOS
  Sharpe ratios instead of a single path.

## 2. Count every trial
Every evaluated parameter set or variant, kept or discarded, is appended to
`research/trials.jsonl`. Each line records: id, timestamp, git commit, family, hypothesis id,
params, data range, cost-model version, metrics, and the path of its **daily PnL series**. The
daily series are needed for PBO.

## 3. Probabilistic and Deflated Sharpe Ratio (Bailey and López de Prado, 2014)
Use non-annualised per-day SR̂, T days, skewness γ₃ and **non-excess** kurtosis γ₄:

```
PSR(SR*) = Φ( (SR̂ − SR*)·√(T−1) / √(1 − γ₃·SR̂ + (γ₄−1)/4 · SR̂²) )

SR₀ = √Var[SR_trials] · ( (1−γ)·Φ⁻¹(1 − 1/N) + γ·Φ⁻¹(1 − 1/(N·e)) ),   γ = 0.5772 (Euler–Mascheroni)

DSR = PSR(SR₀)
```
N = the number of trials in the family. Var[SR_trials] is the variance of the trials' SRs.
**DSR ≥ 0.95** is required. **DSR < 0.5** means no evidence beyond what the search itself
would produce.

## 4. Probability of Backtest Overfitting via CSCV
1. Build the matrix M (T days × N trials) of daily net PnL.
2. Split the rows into S contiguous blocks (S = 16).
3. For each of the C(S, S/2) ways to choose half the blocks as IS (the rest is OOS):
   - pick the trial with the best IS Sharpe;
   - compute its OOS rank, ω ∈ (0, 1), and λ = ln(ω / (1 − ω)).
4. **PBO = share of combinations with λ ≤ 0**, i.e. the IS winner lands at or below the OOS
   median. **Require PBO ≤ 0.10. Flag anything > 0.2.**
5. Also report the performance degradation: the slope of OOS SR on IS SR.

## 5. Multiple-testing hurdle
Harvey, Liu and Zhu (2016): with extensive data mining a new "factor" needs **t > 3.0**, not 2.0.
For the mean trade PnL (OOS), we require t ≥ 3 for "strong" and t ≥ 2 for "weak/watch".

## 6. Parameter sensitivity (±20%)
- Perturb each parameter by −20, −10, 0, +10 and +20% (integer parameters by ±1 or ±2 steps).
- Show 2-D heatmaps for each parameter pair (net PnL, Sharpe, trades).
- **Plateau test:** the median of the neighbours must be ≥ 50% of the centre's net PnL, and no
  neighbour may flip the sign. Sharp peaks fail.
- **What the heatmap should look like:**
  - *Overfit*: an isolated bright cell or a thin ridge surrounded by losses (an "island").
  - *Robust*: a broad, smooth region of similar colour (a "plateau").
- Also map the heatmap over the **full grid**, not just ±20%, at coarse resolution, so a
  plateau's edges are visible.

## 6b. Monte Carlo on **every** parameter set (not just the winner)
Running MC only on the chosen parameter set is selection after the fact. It tells you about the
path of a winner you already picked. Instead, run it for **every grid point** and turn the MC
*percentiles* into heatmaps of their own. Four MC types, each answering a different question:

| MC type | What is randomised | Answers | Note |
|---|---|---|---|
| Trade-order shuffle | the order of trades | drawdown and losing-streak distribution | **does not change total PnL.** It says nothing about whether the edge exists |
| Stationary block bootstrap | blocks of *daily* PnL (block ≈ 5–10 days) | distribution of Sharpe, net PnL, max DD | keeps autocorrelation and volatility clustering. This is the main MC |
| Execution MC | per-trade latency and slippage draws from the measured distribution, fee multiplier U[1, 1.5], and **randomly skipping 5–20% of trades** (missed fills) | sensitivity to execution luck | approximated at the trade level (no full re-simulation) |
| Parameter jitter | each parameter ± small noise per trial | local robustness | complements the heatmap |

Per grid point, store: P(net PnL < 0), the **5th-percentile** Sharpe and net PnL, and the
**95th-percentile** max drawdown. Selection ranks on the **5th percentile, not the mean**.
That is a robust objective.

## 6c. Cluster analysis (meta-analysis of all trials)
1. **Cluster the trials by the correlation of their daily PnL** (hierarchical clustering, or
   the ONC algorithm from López de Prado & Lewis, 2019).
2. **Effective number of trials K** = the number of clusters. Use K (not just the raw N) in the
   DSR's expected-max-Sharpe term, together with the variance of the cluster-level Sharpes.
   Report **both** the raw-N and K-based DSR. N overstates independence, but K must not be
   gamed by adding redundant variants.
3. **Cluster in parameter space**, with performance as a feature, to find **regions**. A
   candidate is credible if it sits inside a cluster where most members (≥ 70%) are profitable
   OOS and have positive 5th-percentile MC PnL.
4. **Pick the cluster's medoid** (its most central member), not the single best point. The best
   point is the one most inflated by luck.
5. Report how many clusters exist and how each one performs. If one cluster is profitable and its
   neighbours are deeply negative, that is an island, and islands are not trusted.

## 7. Red flags (automatic, shown at the top of every report)
- < 200 trades.
- Top-5-days ≥ 50% of PnL, or PnL ≤ 0 after removing the best 5 days.
- Profitable in < 60% of years, or only in one regime (volatility tercile, or RTH vs ETH).
- Profit factor > 3 or Sharpe > 3 for an intraday strategy. **Treat this as a bug until proven
  otherwise.** Check lookahead, fills and costs first.
- Win rate > 80% with a small avg win and a large avg loss (hidden tail risk).
- Results flip sign under `l3_fifo` vs `trade_through` fills, or at 250 ms latency.

## 8. Promotion gates (a candidate must pass all of them, on development data only)
| Gate | Requirement |
|---|---|
| G1 | ≥ 200 OOS trades (concatenated walk-forward) |
| G2 | OOS net PnL > 0 at **1.5× fees and 250 ms latency** |
| G3 | DSR ≥ 0.95 (N = all family trials) **and** OOS mean-trade t ≥ 2 (t ≥ 3 = strong) |
| G4 | PBO ≤ 0.10 |
| G5 | Passes the ±20% plateau test |
| G6 | Not concentrated (red flags clear) |
| G7 | Positive in ≥ 60% of years in the OOS segments |
| G8 | Tier-B fill check does not flip the sign |
| G9 | Monte Carlo (block bootstrap + execution MC): **5th-percentile net PnL > 0** and P(loss) ≤ 10%, at 1.5× fees |
| G10 | The chosen set is a **cluster medoid**: ≥ 70% of its cluster is profitable OOS, and the cluster is not an island |
| G11 | DSR ≥ 0.95 using the **cluster-based effective K**, with the raw-N DSR also reported |

Only then: **one** holdout evaluation, with the user's sign-off, reported as-is. Nothing is
re-tuned after the holdout.

Passing the holdout is still **not** "ready to deploy live". The next step is **paper trading**,
comparing live fills against simulated fills. See [going live later](../07-live-later.md). A
four-step checklist (heatmap → MC on every set → clusters → IS/OOS + walk-forward) is necessary
but not sufficient. It cannot detect lookahead bias, optimistic fills or wrong costs. Those are
covered by sections 1–5 and the [pitfalls checklist](../01-databento/pitfalls.md).

## Sources for 6b/6c
- López de Prado & Lewis (2019), *Detection of false investment strategies using unsupervised
  learning methods*, Quantitative Finance 19(9). Uses clustering to estimate the effective number
  of trials.
- A user-supplied video checklist (summary in [inbox](../inbox/2026-10-02-video-four-robustness-steps.md)).

## Implementation (session 6, routine R4.1)
- `data/holdout.py`: `check()` is called by `Downloader.fetch_sessions/fetch_days` (before
  anything is priced) and by `load_session`; it raises `HoldoutLocked` for dates in the holdout
  unless `research/HOLDOUT_UNLOCK` exists. Until `holdout_start` is frozen, a **provisional**
  holdout from today − 12 months applies. `maybe_freeze()` writes `holdout_start` at the first
  tier-A request spanning ≥ 60 days; it never moves afterwards.
- `research/walkforward.py`: rolling folds from `[walk_forward]` in `config/splits.toml`
  (12 m train → 3 m test, step 3 m, 1 trading-day embargo), development dates only.
- R4.3 `research/stats.py`: `dsr` (SR0 from the variance of all trial SRs and N), `pbo_cscv`
  (S blocks, λ = logit of the IS winner's OOS rank, degradation slope), `plateau_test`,
  `block_bootstrap` (stationary, mean block 7 days), `execution_mc` (fees × U[1,1.5], 5–20%
  skipped trades, optional slippage draws), `shuffle_drawdown`. Negative controls in the tests:
  the best of 200 noise strategies has PSR > 0.9 but DSR < 0.5; PBO of pure noise ≈ 0.5.
- R4.4 `research/clusters.py` (correlation distance, average linkage, k by silhouette → effective
  K, medoids, island check) and `research/gates.py` (G1–G11 table; **missing evidence = FAIL**;
  verdict promising / not promising / insufficient data — fewer than 2 years or 200 OOS trades is
  "insufficient data").
