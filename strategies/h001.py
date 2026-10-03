"""H-001: fade absorption at a developing value-area boundary when delta diverges.

Registry: research/hypotheses/H-001.yaml (space, fixed rules, mechanism). Evaluation: D-020.
Every input is causal: absorption events, the developing profile and divergence bars are each
stamped with `known_at`, and a signal at time t only uses rows with known_at <= t.
"""
from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from backtest.bracket import Day, simulate
from backtest.costs import CostModel
from data.sessions import CT
from features.absorption import absorption_events
from features.common import TICK, ohlcv_bars
from features.footprint import bar_delta, delta_divergence, footprint
from features.profile import developing_profile

ABSORPTION_WINDOW = "30s"
DIV_RECENCY = pd.Timedelta("5min")
TIME_STOP = pd.Timedelta("30min")
LAST_ENTRY_CT = (14, 25)        # no new entries after 14:25 CT (a 30-min trade must end by 14:55)
FLATTEN_CT = (14, 55)


def day_features(trades: pd.DataFrame, min_vols, lookbacks) -> dict:
    prof = developing_profile(trades, "1min")
    bars = ohlcv_bars(trades, "1min").join(bar_delta(footprint(trades, "1min"))[["cum_delta"]])
    return {"profile": prof,
            "absorption": {mv: absorption_events(trades, window=ABSORPTION_WINDOW, min_vol=mv) for mv in min_vols},
            "divergence": {lb: delta_divergence(bars, lb) for lb in lookbacks}}


def signals(feat: dict, min_vol: int, level_tol: int, div_lookback: int, trading_date: date) -> pd.DataFrame:
    """Rows: known_at, side (+1 long after sell absorption, -1 short after buy absorption), level."""
    ev = feat["absorption"][min_vol]
    if ev.empty:
        return pd.DataFrame(columns=["known_at", "side", "level"])
    prof, div = feat["profile"], feat["divergence"][div_lookback]
    last_entry = pd.Timestamp(trading_date.isoformat(), tz=CT) + pd.Timedelta(hours=LAST_ENTRY_CT[0], minutes=LAST_ENTRY_CT[1])
    p_known = pd.DatetimeIndex(prof["known_at"]).as_unit("ns").asi8
    d_known = pd.DatetimeIndex(div["known_at"]).as_unit("ns").asi8
    rows = []
    for r in ev.itertuples(index=False):
        t = pd.Timestamp(r.known_at)
        if t > last_entry:
            continue
        i = np.searchsorted(p_known, t.value, side="right") - 1          # profile known at t
        if i < 0:
            continue
        pr = prof.iloc[i]
        if min(abs(r.level - pr.val), abs(r.level - pr.vah), abs(r.level - pr.poc)) > level_tol * TICK + 1e-9:
            continue
        lo = np.searchsorted(d_known, (t - DIV_RECENCY).value, side="right")
        hi = np.searchsorted(d_known, t.value, side="right")
        recent = div.iloc[lo:hi]
        if r.side == "sell_absorbed" and recent["bullish_div"].any():
            rows.append((t, 1, r.level))
        elif r.side == "buy_absorbed" and recent["bearish_div"].any():
            rows.append((t, -1, r.level))
    return pd.DataFrame(rows, columns=["known_at", "side", "level"])


def trade_day(day: Day, sig: pd.DataFrame, stop_ticks: int, target_ticks: int, trading_date: date,
              costs: CostModel) -> list[dict]:
    """One position at a time: a signal is taken only if it comes after the previous exit."""
    flatten = (pd.Timestamp(trading_date.isoformat(), tz=CT)
               + pd.Timedelta(hours=FLATTEN_CT[0], minutes=FLATTEN_CT[1])).value
    out, free_at = [], -1
    for s in sig.itertuples(index=False):
        k = pd.Timestamp(s.known_at).value
        if k <= free_at:
            continue
        tr = simulate(day, k, int(s.side), stop_ticks, target_ticks, min(k + TIME_STOP.value, flatten), costs)
        if tr is None:
            continue
        tr["trading_date"] = trading_date
        out.append(tr)
        free_at = tr["exit_ts"]
    return out
