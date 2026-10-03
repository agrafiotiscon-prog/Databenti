"""H-008 fade extreme 5-minute order-flow imbalance (registry research/hypotheses/H-008.yaml).

z of a bucket uses only the previous 20 buckets of the same session; the signal is known at the
bucket's end (known_at), and the order fills on a later record after latency.
"""
from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from backtest.bracket import Day, simulate
from backtest.costs import CostModel
from data.sessions import CT
from features.common import BUY_AGGRESSOR, SELL_AGGRESSOR

KEYS = ("z", "hold_min", "stop_ticks")
NO_TARGET = 100_000
LOOKBACK = 20


def _ct(d: date, h: int, m: int) -> int:
    return (pd.Timestamp(d.isoformat(), tz=CT) + pd.Timedelta(hours=h, minutes=m)).value


def prepare_day(trades: pd.DataFrame, d: date, state: dict) -> pd.DataFrame:
    s = trades["side"].astype(str)
    signed = np.where(s == BUY_AGGRESSOR, trades["size"], np.where(s == SELL_AGGRESSOR, -trades["size"], 0)).astype(float)
    b = pd.Series(signed, index=trades.index).resample("5min", label="left", closed="left").sum()
    prev = b.shift(1).rolling(LOOKBACK, min_periods=LOOKBACK)
    sd = prev.std(ddof=1)
    z = (b - prev.mean()) / sd.where(sd > 0)            # flat history -> no signal (not +-inf)
    known = pd.DatetimeIndex(b.index + pd.Timedelta("5min")).as_unit("ns").asi8
    return pd.DataFrame({"known_at": known, "delta": b.to_numpy(), "z": z.to_numpy()}).dropna()


def day_trades(day: Day, ev: pd.DataFrame, p: dict, d: date, costs: CostModel) -> list[dict]:
    last_entry, flatten = _ct(d, 14, 25), _ct(d, 14, 55)
    sig = ev[(ev["z"].abs() >= p["z"]) & (ev["known_at"] <= last_entry)]
    out, free_at = [], -1
    hold = int(pd.Timedelta(minutes=p["hold_min"]).value)
    for k, zz in zip(sig["known_at"].to_numpy(), sig["z"].to_numpy()):
        if k <= free_at:
            continue
        tr = simulate(day, int(k), -int(np.sign(zz)), p["stop_ticks"], NO_TARGET, min(int(k) + hold, flatten), costs)
        if tr is None:
            continue
        tr["trading_date"] = d
        out.append(tr)
        free_at = tr["exit_ts"]
    return out
