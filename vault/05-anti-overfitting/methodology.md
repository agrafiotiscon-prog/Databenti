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

Only then: **one** holdout evaluation, with the user's sign-off, reported as-is. Nothing is
re-tuned after the holdout.
