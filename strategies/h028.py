"""H-028: follow strong aggressor trade-flow imbalance in ES RTH (registry research/hypotheses/H-028.yaml).

Interface for scripts/run_hypothesis.py: KEYS, prepare_day(trades, trading_date, state) -> features,
day_trades(day, feat, params, trading_date, costs) -> list of trade dicts.
Causality: the imbalance uses trades strictly before the decision time; the entry is the first trade
at/after it (+ latency inside backtest.bracket.simulate).
"""
from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from backtest.bracket import Day, simulate
from backtest.costs import CostModel
from data.sessions import CT
from features.common import BUY_AGGRESSOR, SELL_AGGRESSOR

KEYS = ("window", "level", "hold")
THRESH = {5: {"q75": 0.07, "q90": 0.09}, 15: {"q75": 0.05, "q90": 0.065}}
NO_STOP = 100_000


def decision_times(d: date) -> list[pd.Timestamp]:
    base = pd.Timestamp(d.isoformat(), tz=CT)
    return [base + pd.Timedelta(hours=9, minutes=30 * k) for k in range(11)]       # 09:00 .. 14:00 CT


def imbalances(trades: pd.DataFrame, times, windows=(5, 15)) -> dict:
    """{(t, w): imb} with imb over [t - w min, t); NaN if no volume."""
    side = trades["side"].astype(str).to_numpy()
    sz = trades["size"].to_numpy(float)
    sg = np.where(side == BUY_AGGRESSOR, sz, np.where(side == SELL_AGGRESSOR, -sz, 0.0))
    t_ns = pd.DatetimeIndex(trades.index).as_unit("ns").asi8
    csg, cv = np.concatenate([[0.0], np.cumsum(sg)]), np.concatenate([[0.0], np.cumsum(sz)])
    out = {}
    for t in times:
        hi = int(np.searchsorted(t_ns, t.value, "left"))                 # strictly before t
        for w in windows:
            lo = int(np.searchsorted(t_ns, (t - pd.Timedelta(minutes=w)).value, "left"))
            v = cv[hi] - cv[lo]
            out[(t, w)] = (csg[hi] - csg[lo]) / v if v > 0 else np.nan
    return out


def prepare_day(trades: pd.DataFrame, d: date, state: dict) -> dict:
    times = decision_times(d)
    return {"times": times, "imb": imbalances(trades, times)}


def day_trades(day: Day, feat: dict, p: dict, d: date, costs: CostModel) -> list[dict]:
    thr = THRESH[p["window"]][p["level"]]
    out, busy_until = [], None
    for t in feat["times"]:
        if busy_until is not None and t < busy_until:
            continue
        imb = feat["imb"][(t, p["window"])]
        if np.isnan(imb) or abs(imb) < thr:
            continue
        exit_t = t + pd.Timedelta(minutes=p["hold"])
        tr = simulate(day, t.value, int(np.sign(imb)), NO_STOP, NO_STOP, exit_t.value, costs)
        if tr is None:
            continue
        tr["trading_date"] = d
        out.append(tr)
        busy_until = exit_t
    return out
