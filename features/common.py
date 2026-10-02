"""Shared helpers: tick grid, bars, side conventions."""
from __future__ import annotations

import numpy as np
import pandas as pd

TICK = 0.25
BUY_AGGRESSOR = "B"    # trade side 'B': buyer lifted the ask
SELL_AGGRESSOR = "A"   # trade side 'A': seller hit the bid
NO_SIDE = "N"          # auction uncross / implied: never assigned to a side


def to_tick(price, tick: float = TICK):
    """Snap prices to the tick grid (avoids float drift in groupbys)."""
    return np.round(np.asarray(price, dtype="float64") / tick) * tick


def clean_trades(trades: pd.DataFrame, tick: float = TICK) -> pd.DataFrame:
    """Minimal normalised trade frame: price (tick-snapped), size (int64), side (str)."""
    out = pd.DataFrame(index=trades.index)
    out["price"] = to_tick(trades["price"].to_numpy(), tick)
    out["size"] = trades["size"].astype("int64").to_numpy()   # uint32 in DBN -> avoid wraparound
    out["side"] = trades["side"].astype(str).to_numpy()
    return out


def bar_start(index: pd.DatetimeIndex, freq: str) -> pd.DatetimeIndex:
    """Left-closed bar label: [start, start + freq)."""
    return index.floor(freq)


def ohlcv_bars(trades: pd.DataFrame, freq: str = "1min", tick: float = TICK) -> pd.DataFrame:
    """OHLCV bars from trades; known_at = bar end."""
    t = clean_trades(trades, tick)
    g = t.groupby(bar_start(t.index, freq))
    bars = pd.DataFrame({
        "open": g["price"].first(), "high": g["price"].max(), "low": g["price"].min(),
        "close": g["price"].last(), "volume": g["size"].sum(),
    })
    bars.index.name = "bar_start"
    bars["known_at"] = bars.index + pd.Timedelta(freq)
    return bars
