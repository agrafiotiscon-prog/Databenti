"""Backtest metrics with the exact definitions in vault/04-backtesting/metrics.md (Phase 3, R3.3).

Everything here is computed from ONE backtest result. Not here (Phase 4): the deflated Sharpe
(needs the trial count), PBO, Monte Carlo, and cost/latency stress (re-runs the backtest).
"""
from __future__ import annotations

import math
from datetime import date

import numpy as np
import pandas as pd

MIN_TRADES = 200
MARKOUT_HORIZONS = ("100ms", "1s", "10s", "60s", "300s")


def trade_stats(trades: pd.DataFrame) -> dict:
    n = len(trades)
    out = {"trades": n, "flag_few_trades": n < MIN_TRADES}
    if n == 0:
        return out
    pnl = trades["net_pnl"].to_numpy(float)
    wins, losses = pnl[pnl > 0].sum(), pnl[pnl < 0].sum()
    sd = pnl.std(ddof=1) if n > 1 else np.nan
    out.update({
        "net_pnl": float(pnl.sum()), "win_rate": float((pnl > 0).mean()),
        "avg_trade": float(pnl.mean()), "median_trade": float(np.median(pnl)),
        "avg_ticks": float(trades["ticks"].mean()), "fees": float(trades["fees"].sum()),
        "profit_factor": float(wins / -losses) if losses < 0 else float("inf"),
        "t_stat": float(pnl.mean() / (sd / math.sqrt(n))) if n > 1 and sd > 0 else float("nan"),
    })
    return out


def trading_date_of(ts: pd.Series | pd.DatetimeIndex) -> pd.Series:
    from data.sessions import tag_sessions
    idx = pd.DatetimeIndex(ts)
    return pd.Series(pd.to_datetime(tag_sessions(idx)["trading_date"].to_numpy()).date, index=range(len(idx)))


def daily_pnl(trades: pd.DataFrame, trading_dates: list[date]) -> pd.Series:
    """Net PnL per trading date (by exit), INCLUDING zero days for every date in `trading_dates`."""
    daily = pd.Series(0.0, index=pd.Index(sorted(trading_dates), name="trading_date"))
    if len(trades):
        d = trading_date_of(trades["exit_ts"])
        sums = pd.Series(trades["net_pnl"].to_numpy(float)).groupby(d.to_numpy()).sum()
        extra = set(sums.index) - set(daily.index)
        if extra:
            raise ValueError(f"trades on dates outside trading_dates: {sorted(extra)[:3]}")
        daily.loc[sums.index] = sums.to_numpy()
    return daily


def sharpe(daily: pd.Series, periods: int = 252) -> float:
    sd = daily.std(ddof=1)
    return float(daily.mean() / sd * math.sqrt(periods)) if len(daily) > 1 and sd > 0 else float("nan")


def lo_adjusted_sharpe(daily: pd.Series, periods: int = 252, lags: int = 5) -> float:
    """Lo (2002): scale the per-period SR by sqrt(q / (q + 2 sum_k (q-k) rho_k)) with q = periods."""
    sr = sharpe(daily, periods=1)
    if not np.isfinite(sr):
        return float("nan")
    x = daily.to_numpy(float) - daily.mean()
    denom = (x * x).sum()
    rho = [float((x[k:] * x[:-k]).sum() / denom) if denom > 0 and len(x) > k else 0.0 for k in range(1, lags + 1)]
    q = periods
    eta = q / math.sqrt(q + 2 * sum((q - k) * r for k, r in enumerate(rho, start=1)))
    return float(sr * eta) if np.isfinite(eta) else float("nan")


def probabilistic_sharpe(daily: pd.Series, sr_benchmark: float = 0.0) -> float:
    """PSR (Bailey & Lopez de Prado 2012) of the per-period SR vs a benchmark, with skew/kurtosis."""
    n = len(daily)
    sr = sharpe(daily, periods=1)
    if n < 3 or not np.isfinite(sr):
        return float("nan")
    g3 = float(daily.skew())                     # bias-corrected sample skewness
    g4 = float(daily.kurt()) + 3.0               # pandas gives excess kurtosis
    var = (1 - g3 * sr + (g4 - 1) / 4 * sr * sr) / (n - 1)
    if not var > 0:
        return float("nan")
    z = (sr - sr_benchmark) / math.sqrt(var)
    return float(0.5 * (1 + math.erf(z / math.sqrt(2))))


def drawdown(daily: pd.Series) -> dict:
    eq = daily.cumsum()
    peak = eq.cummax().clip(lower=0.0)          # start from flat (0) capital
    dd = eq - peak
    if len(dd) == 0:
        return {"max_drawdown": 0.0, "max_dd_days": 0}
    under, longest, cur = dd < 0, 0, 0
    for u in under:
        cur = cur + 1 if u else 0
        longest = max(longest, cur)
    return {"max_drawdown": float(dd.min()), "max_dd_days": int(longest)}


def concentration(daily: pd.Series) -> dict:
    total = float(daily.sum())
    top5 = float(daily.nlargest(5).sum())
    k = max(1, int(math.ceil(0.10 * len(daily))))
    top10pct = float(daily.nlargest(k).sum())
    without5 = total - top5
    share5 = top5 / total if total > 0 else float("nan")
    return {"top5_days_share": share5, "top10pct_days_share": top10pct / total if total > 0 else float("nan"),
            "pnl_without_best5": without5,
            "flag_concentrated": bool(total <= 0 or share5 >= 0.5 or without5 <= 0)}


def breakdown(trades: pd.DataFrame) -> dict[str, pd.DataFrame]:
    if not len(trades):
        return {}
    from data.sessions import CT
    t = trades.assign(ts_ct=pd.DatetimeIndex(trades["exit_ts"]).tz_convert(CT))
    keys = {"year": t.ts_ct.dt.year, "month": t.ts_ct.dt.strftime("%Y-%m"),
            "weekday": t.ts_ct.dt.day_name().str[:3], "hour_ct": t.ts_ct.dt.hour}
    return {k: t.groupby(v)["net_pnl"].agg(trades="size", net_pnl="sum", avg="mean",
                                             win_rate=lambda s: (s > 0).mean()) for k, v in keys.items()}


def markouts(fills: pd.DataFrame, l1: pd.DataFrame, horizons=MARKOUT_HORIZONS) -> pd.DataFrame:
    """Signed mid move after each of OUR fills (in ticks of 0.25 by default units of price):
    side * (mid(fill_ts + h) - fill price). Mid at t = last L1 record at or before t."""
    f = fills[~fills.get("end_flatten", False).astype(bool)] if len(fills) else fills
    if not len(f):
        return pd.DataFrame(columns=list(horizons))
    t = pd.DatetimeIndex(l1.index).as_unit("ns").asi8
    mid = ((l1["bid_px"] + l1["ask_px"]) / 2).to_numpy(float)
    out = {}
    for h in horizons:
        tq = pd.DatetimeIndex(f["fill_ts"]).as_unit("ns").asi8 + pd.Timedelta(h).value
        j = np.searchsorted(t, tq, side="right") - 1
        ok = (j >= 0) & (tq <= t[-1])
        m = np.where(ok, mid[np.clip(j, 0, len(mid) - 1)], np.nan)
        out[h] = f["side"].to_numpy() * (m - f["price"].to_numpy(float))
    return pd.DataFrame(out, index=f.index)


def exposure(fills: pd.DataFrame, session_minutes: float) -> float:
    """Share of the given session minutes spent in a position (fills in time order)."""
    if not len(fills) or session_minutes <= 0:
        return 0.0
    pos, last, held = 0, None, 0.0
    for r in fills.sort_values("fill_ts").itertuples(index=False):
        if pos != 0 and last is not None:
            held += (r.fill_ts - last).total_seconds() / 60
        pos += r.side * r.qty
        last = r.fill_ts
    return float(held / session_minutes)


def report(result, l1: pd.DataFrame, trading_dates: list[date], session_minutes: float) -> dict:
    """All single-run metrics; markouts in ticks."""
    tick = result.costs.tick
    daily = daily_pnl(result.trades, trading_dates)
    mk = markouts(result.fills, l1)
    return {
        **trade_stats(result.trades),
        "days": len(daily), "sharpe": sharpe(daily), "sharpe_lo": lo_adjusted_sharpe(daily),
        "psr_vs_0": probabilistic_sharpe(daily), **drawdown(daily), **concentration(daily),
        "exposure": exposure(result.fills, session_minutes),
        "markout_ticks": (mk.mean() / tick).round(3).to_dict() if len(mk) else {},
        "daily": daily, "breakdown": breakdown(result.trades),
    }
