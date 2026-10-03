"""H-004: follow large multi-level aggressive sweeps. Registry: research/hypotheses/H-004.yaml.

Interface for scripts/run_hypothesis.py: KEYS, prepare_day, day_trades.
A sweep is known at its own ts_recv (all its prints share it); the engine fills the order on a
later record after latency, so the decision never uses information from after the sweep.
"""
from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from backtest.bracket import Day, simulate
from backtest.costs import CostModel
from data.sessions import CT
from features.common import BUY_AGGRESSOR, SELL_AGGRESSOR

KEYS = ("min_size", "min_levels", "stop_ticks", "target_ticks")
TIME_STOP = pd.Timedelta("15min")


def _ct(d: date, h: int, m: int) -> int:
    return (pd.Timestamp(d.isoformat(), tz=CT) + pd.Timedelta(hours=h, minutes=m)).value


def prepare_day(trades: pd.DataFrame, d: date, state: dict) -> pd.DataFrame:
    """One row per aggressor event: known_at (ns), side (+1 buy sweep / -1 sell sweep), size, levels."""
    t = trades[trades["side"].astype(str).isin([BUY_AGGRESSOR, SELL_AGGRESSOR])]
    ns = pd.DatetimeIndex(t.index).as_unit("ns").asi8
    g = (pd.DataFrame({"t": ns, "side": t["side"].astype(str).to_numpy(), "size": t["size"].to_numpy(float),
                       "price": t["price"].to_numpy(float)})
         .groupby(["t", "side"], sort=True).agg(size=("size", "sum"), levels=("price", "nunique")).reset_index())
    g["dir"] = np.where(g["side"] == BUY_AGGRESSOR, 1, -1)
    return g[["t", "dir", "size", "levels"]]


def day_trades(day: Day, ev: pd.DataFrame, p: dict, d: date, costs: CostModel) -> list[dict]:
    last_entry, flatten = _ct(d, 14, 40), _ct(d, 14, 55)
    sig = ev[(ev["size"] >= p["min_size"]) & (ev["levels"] >= p["min_levels"]) & (ev["t"] <= last_entry)]
    out, free_at = [], -1
    for t, side in zip(sig["t"].to_numpy(), sig["dir"].to_numpy()):
        if t <= free_at:
            continue
        # act on the first record strictly AFTER the sweep's own prints
        tr = simulate(day, int(t) + 1, int(side), p["stop_ticks"], p["target_ticks"],
                      min(int(t) + TIME_STOP.value, flatten), costs)
        if tr is None:
            continue
        tr["trading_date"] = d
        out.append(tr)
        free_at = tr["exit_ts"]
    return out
