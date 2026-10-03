"""H-011 fade large deviations from the session VWAP (registry research/hypotheses/H-011.yaml).

VWAP and the deviation sd use only trades up to each 1-minute bar's end (expanding, causal); the
signal is known at the bar end and filled on a later record after latency.
"""
from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from backtest.bracket import Day, simulate
from backtest.costs import CostModel
from data.sessions import CT

KEYS = ("k", "stop_ticks")
TICK = 0.25
TIME_STOP = pd.Timedelta("30min")


def _ct(d: date, h: int, m: int) -> int:
    return (pd.Timestamp(d.isoformat(), tz=CT) + pd.Timedelta(hours=h, minutes=m)).value


def prepare_day(trades: pd.DataFrame, d: date, state: dict) -> pd.DataFrame:
    px = trades["price"].to_numpy(float)
    q = trades["size"].to_numpy(float)
    vwap = np.cumsum(px * q) / np.cumsum(q)
    dev = px - vwap
    n = np.arange(1, len(dev) + 1)
    mean = np.cumsum(dev) / n
    var = np.maximum(np.cumsum(dev * dev) / n - mean * mean, 0.0)
    sd = np.sqrt(var * n / np.maximum(n - 1, 1))
    f = pd.DataFrame({"px": px, "vwap": vwap, "sd": sd}, index=trades.index)
    m = f.resample("1min", label="left", closed="left").last().dropna()
    known = pd.DatetimeIndex(m.index + pd.Timedelta("1min")).as_unit("ns").asi8
    z = (m["px"] - m["vwap"]) / m["sd"].where(m["sd"] > 0)
    return pd.DataFrame({"known_at": known, "z": z.to_numpy(), "dist_ticks": ((m["px"] - m["vwap"]) / TICK).to_numpy()}).dropna()


def day_trades(day: Day, ev: pd.DataFrame, p: dict, d: date, costs: CostModel) -> list[dict]:
    first, last_entry, flatten = _ct(d, 9, 30), _ct(d, 14, 25), _ct(d, 14, 55)
    sig = ev[(ev["z"].abs() >= p["k"]) & (ev["known_at"] >= first) & (ev["known_at"] <= last_entry)]
    out, free_at = [], -1
    for k, zz, dist in zip(sig["known_at"].to_numpy(), sig["z"].to_numpy(), sig["dist_ticks"].to_numpy()):
        if k <= free_at:
            continue
        target = max(1.0, round(abs(dist)))                # back to VWAP as of the signal
        tr = simulate(day, int(k), -int(np.sign(zz)), p["stop_ticks"], target, min(int(k) + TIME_STOP.value, flatten), costs)
        if tr is None:
            continue
        tr["trading_date"] = d
        out.append(tr)
        free_at = tr["exit_ts"]
    return out
