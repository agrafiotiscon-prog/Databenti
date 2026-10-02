"""Diagonal and stacked imbalances on footprint bars (feature 4).

Diagonal comparison (buyers lifting at p vs sellers hitting one tick lower):
  buy imbalance at p : ask_vol[p] >= min_vol and ask_vol[p] >= ratio * bid_vol[p - tick]
  sell imbalance at p: bid_vol[p] >= min_vol and bid_vol[p] >= ratio * ask_vol[p + tick]
A missing price level counts as 0 volume. Stacked = >= n_stack consecutive
tick-adjacent prices with same-side imbalance.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .common import TICK


def diagonal_imbalances(fp: pd.DataFrame, ratio: float = 3.0, min_vol: int = 10,
                        tick: float = TICK) -> pd.DataFrame:
    """Adds buy_imb / sell_imb columns to a footprint (same rows)."""
    out = fp.copy()
    key = out.set_index(["bar_start", "price"])
    bid = key["bid_vol"]
    ask = key["ask_vol"]
    below = pd.MultiIndex.from_arrays([out["bar_start"], np.round((out["price"] - tick) / tick) * tick])
    above = pd.MultiIndex.from_arrays([out["bar_start"], np.round((out["price"] + tick) / tick) * tick])
    bid_below = bid.reindex(below).fillna(0).to_numpy()
    ask_above = ask.reindex(above).fillna(0).to_numpy()
    out["buy_imb"] = (out["ask_vol"] >= min_vol) & (out["ask_vol"] >= ratio * bid_below)
    out["sell_imb"] = (out["bid_vol"] >= min_vol) & (out["bid_vol"] >= ratio * ask_above)
    return out


def stacked_imbalances(imb: pd.DataFrame, n_stack: int = 3, tick: float = TICK) -> pd.DataFrame:
    """Zones of >= n_stack consecutive same-side imbalances per bar.

    Returns: bar_start, side ('buy'/'sell'), low, high, count, known_at.
    """
    zones = []
    for side, col in (("buy", "buy_imb"), ("sell", "sell_imb")):
        hits = imb.loc[imb[col], ["bar_start", "price", "known_at"]].sort_values(["bar_start", "price"])
        for b, g in hits.groupby("bar_start", sort=True):
            ticks = np.round(g["price"].to_numpy() / tick).astype(np.int64)
            run_start = 0
            for i in range(1, len(ticks) + 1):
                if i == len(ticks) or ticks[i] != ticks[i - 1] + 1:
                    if i - run_start >= n_stack:
                        zones.append({"bar_start": b, "side": side,
                                      "low": ticks[run_start] * tick, "high": ticks[i - 1] * tick,
                                      "count": i - run_start, "known_at": g["known_at"].iloc[0]})
                    run_start = i
    cols = ["bar_start", "side", "low", "high", "count", "known_at"]
    return pd.DataFrame(zones, columns=cols).sort_values(["bar_start", "side"]).reset_index(drop=True)
