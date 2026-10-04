"""Random-timing placebo (gate G12) for tick-data strategies (R9.1).

Keeps everything about the out-of-sample trades except their timing: the same days, the same number of
trades per day, the same sides and holding durations, the same costs - only each entry time is redrawn
uniformly inside the session so that the whole hold fits. If the strategy's timing carries information,
the real OOS net should beat most placebo draws. p = share of draws with net >= real.
"""
from __future__ import annotations

from typing import Callable, Iterable

import numpy as np
import pandas as pd


def random_timing_nets(trades: pd.DataFrame, days: Iterable, load_day: Callable, bounds: Callable,
                       simulate_one: Callable, n_draws: int, seed: int = 12) -> np.ndarray:
    """trades: OOS trades with entry_ts, exit_ts, side, trading_date. load_day(d) -> day object;
    bounds(d) -> (start_ns, end_ns); simulate_one(day, entry_ns, side, exit_ns) -> net $ or None.
    Returns n_draws placebo OOS nets. Days are loaded once each."""
    rng = np.random.default_rng(seed)
    sums = np.zeros(n_draws)
    by_day = {d: g for d, g in trades.groupby("trading_date")}
    for d in days:
        g = by_day.get(d)
        if g is None or g.empty:
            continue
        day = load_day(d)
        lo, hi = bounds(d)
        ent = pd.to_datetime(g["entry_ts"]).dt.as_unit("ns").astype("int64").to_numpy()   # force ns (inputs may be us)
        ext = pd.to_datetime(g["exit_ts"]).dt.as_unit("ns").astype("int64").to_numpy()
        dur = np.maximum(ext - ent, 1)
        side = g["side"].to_numpy(int)
        for k in range(n_draws):
            for du, sd in zip(dur, side):
                if hi - du <= lo:
                    continue
                t = int(rng.integers(lo, hi - du))
                net = simulate_one(day, t, int(sd), t + int(du))
                if net is not None:
                    sums[k] += net
    return sums
