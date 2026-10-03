"""Anti-overfitting statistics (Phase 4, R4.3). Definitions: vault/05-anti-overfitting/methodology.md.

  dsr()             Deflated Sharpe (Bailey & Lopez de Prado 2014), N = trials in the family
  pbo_cscv()        Probability of Backtest Overfitting via CSCV (Bailey et al. 2017), S blocks
  plateau_test()    +-20% neighbourhood: median >= 50% of centre and no sign flip
  block_bootstrap() stationary bootstrap of DAILY PnL (main MC)
  execution_mc()    trade-level: fee multiplier U[1,1.5], 5-20% skipped trades, slippage draws
  shuffle_drawdown() trade-order shuffle (drawdown / losing streak only; never changes total PnL)
"""
from __future__ import annotations

import itertools
import math
from statistics import NormalDist

import numpy as np
import pandas as pd

from backtest.metrics import probabilistic_sharpe

EULER_GAMMA = 0.5772156649015329
_N = NormalDist()


def per_period_sharpe(x) -> float:
    x = np.asarray(x, float)
    sd = x.std(ddof=1) if len(x) > 1 else np.nan
    return float(x.mean() / sd) if sd and np.isfinite(sd) and sd > 0 else float("nan")


def expected_max_sharpe(sr_variance: float, n_trials: int) -> float:
    """SR0: expected maximum of N per-period Sharpe ratios under the null (true SR = 0)."""
    if n_trials < 2 or not sr_variance > 0:
        return 0.0
    return math.sqrt(sr_variance) * ((1 - EULER_GAMMA) * _N.inv_cdf(1 - 1 / n_trials)
                                     + EULER_GAMMA * _N.inv_cdf(1 - 1 / (n_trials * math.e)))


def dsr(daily: pd.Series, trial_sharpes, n_trials: int | None = None) -> float:
    """DSR = PSR(SR0). `trial_sharpes`: per-period SRs of ALL trials in the family (incl. this one)."""
    srs = np.asarray([s for s in trial_sharpes if np.isfinite(s)], float)
    n = n_trials if n_trials is not None else len(srs)
    sr0 = expected_max_sharpe(float(srs.var(ddof=1)) if len(srs) > 1 else 0.0, n)
    return probabilistic_sharpe(daily, sr_benchmark=sr0)


def pbo_cscv(pnl: pd.DataFrame, n_blocks: int = 16) -> dict:
    """pnl: T x N matrix (rows = days in time order, columns = trials) of daily net PnL."""
    m = np.asarray(pnl, float)
    t, n = m.shape
    if n < 2 or n_blocks % 2 or t < n_blocks * 2:
        raise ValueError("need >= 2 trials, an even number of blocks and >= 2 rows per block")
    blocks = np.array_split(np.arange(t), n_blocks)
    lambdas, is_sr, oos_sr = [], [], []
    for combo in itertools.combinations(range(n_blocks), n_blocks // 2):
        is_rows = np.concatenate([blocks[b] for b in combo])
        oos_rows = np.concatenate([blocks[b] for b in range(n_blocks) if b not in combo])
        s_is = np.array([per_period_sharpe(m[is_rows, j]) for j in range(n)])
        s_oos = np.array([per_period_sharpe(m[oos_rows, j]) for j in range(n)])
        best = int(np.nanargmax(s_is))
        rank = (pd.Series(s_oos).rank(method="average").iloc[best])          # 1..n
        omega = rank / (n + 1)
        lambdas.append(math.log(omega / (1 - omega)))
        is_sr.append(s_is[best]); oos_sr.append(s_oos[best])
    lam = np.array(lambdas)
    slope = float(np.polyfit(is_sr, oos_sr, 1)[0]) if len(set(is_sr)) > 1 else float("nan")
    return {"pbo": float((lam <= 0).mean()), "n_combinations": len(lam), "lambda_median": float(np.median(lam)),
            "degradation_slope": slope, "flag": bool((lam <= 0).mean() > 0.2)}


def plateau_test(centre_pnl: float, neighbour_pnls) -> dict:
    nb = np.asarray(list(neighbour_pnls), float)
    med = float(np.median(nb)) if len(nb) else float("nan")
    flips = int((np.sign(nb) != np.sign(centre_pnl)).sum()) if centre_pnl != 0 else len(nb)
    ok = bool(centre_pnl > 0 and len(nb) and med >= 0.5 * centre_pnl and flips == 0)
    return {"pass": ok, "neighbour_median": med, "ratio": med / centre_pnl if centre_pnl else float("nan"),
            "sign_flips": flips}


def _max_dd(cum: np.ndarray) -> float:
    peak = np.maximum.accumulate(np.maximum(cum, 0.0))
    return float((cum - peak).min()) if len(cum) else 0.0


def _summary(net: np.ndarray, sharpe: np.ndarray, dd: np.ndarray) -> dict:
    return {"p_loss": float((net < 0).mean()), "net_p5": float(np.percentile(net, 5)),
            "net_median": float(np.median(net)), "sharpe_p5": float(np.nanpercentile(sharpe, 5)),
            "max_dd_p95": float(np.percentile(dd, 5))}       # dd is negative: 5th pct = 95th worst


def block_bootstrap(daily: pd.Series, mean_block: int = 7, n_sims: int = 2000, seed: int = 0) -> dict:
    """Stationary bootstrap (Politis & Romano 1994): geometric block lengths, circular wrap."""
    x = np.asarray(daily, float)
    t = len(x)
    rng = np.random.default_rng(seed)
    p = 1.0 / mean_block
    nets, srs, dds = np.empty(n_sims), np.empty(n_sims), np.empty(n_sims)
    for s in range(n_sims):
        idx = np.empty(t, int)
        i = rng.integers(t)
        for k in range(t):
            idx[k] = i
            i = rng.integers(t) if rng.random() < p else (i + 1) % t
        y = x[idx]
        nets[s], srs[s], dds[s] = y.sum(), per_period_sharpe(y) * math.sqrt(252), _max_dd(np.cumsum(y))
    return _summary(nets, srs, dds)


def execution_mc(trade_net: np.ndarray, trade_fees: np.ndarray, n_sims: int = 2000, seed: int = 0,
                 skip_range=(0.05, 0.20), fee_mult_range=(1.0, 1.5), slippage_usd=None) -> dict:
    """Trade-level execution luck. Fees are scaled by U[fee_mult_range]; a U[skip_range] share of trades
    is dropped (missed fills); optional per-trade slippage (USD) is drawn from `slippage_usd`."""
    pnl, fees = np.asarray(trade_net, float), np.asarray(trade_fees, float)
    gross = pnl + fees
    rng = np.random.default_rng(seed)
    nets, srs, dds = np.empty(n_sims), np.empty(n_sims), np.empty(n_sims)
    for s in range(n_sims):
        keep = rng.random(len(pnl)) >= rng.uniform(*skip_range)
        y = gross - fees * rng.uniform(*fee_mult_range)
        if slippage_usd is not None and len(slippage_usd):
            y = y - rng.choice(np.asarray(slippage_usd, float), size=len(y))
        y = y[keep]
        nets[s], srs[s], dds[s] = y.sum(), per_period_sharpe(y), _max_dd(np.cumsum(y))
    return _summary(nets, srs, dds)


def shuffle_drawdown(trade_net: np.ndarray, n_sims: int = 2000, seed: int = 0) -> dict:
    """Trade-order shuffle: drawdown and longest losing streak distribution (total PnL is unchanged)."""
    pnl = np.asarray(trade_net, float)
    rng = np.random.default_rng(seed)
    dds, streaks = np.empty(n_sims), np.empty(n_sims)
    for s in range(n_sims):
        y = rng.permutation(pnl)
        dds[s] = _max_dd(np.cumsum(y))
        run = best = 0
        for v in y:
            run = run + 1 if v < 0 else 0
            best = max(best, run)
        streaks[s] = best
    return {"max_dd_p95": float(np.percentile(dds, 5)), "losing_streak_p95": float(np.percentile(streaks, 95))}
