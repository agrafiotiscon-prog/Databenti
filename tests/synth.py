"""Synthetic market data for tests (shaped like Databento to_df output)."""
from __future__ import annotations

import numpy as np
import pandas as pd

T0 = pd.Timestamp("2024-03-05 14:30:00", tz="UTC")   # 08:30 CT, RTH open


def trades_df(rows, t0: pd.Timestamp = T0) -> pd.DataFrame:
    """rows: (seconds_after_t0, price, size, side)."""
    idx = pd.DatetimeIndex([t0 + pd.Timedelta(seconds=s) for s, *_ in rows], name="ts_recv")
    return pd.DataFrame({"price": [r[1] for r in rows], "size": np.array([r[2] for r in rows], dtype="uint32"),
                         "side": [r[3] for r in rows], "action": "T", "flags": np.uint8(128)}, index=idx)


def random_trades(n: int = 4000, seed: int = 7, t0: pd.Timestamp = T0, with_bbo: bool = True) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    gaps_ms = rng.exponential(600, n).astype(int)
    gaps_ms[rng.random(n) < 0.1] = 0                     # duplicate timestamps happen
    ts = t0 + pd.to_timedelta(np.cumsum(gaps_ms), unit="ms")
    steps = rng.choice([-1, 0, 0, 0, 1], n)
    price = 5000.0 + 0.25 * np.cumsum(steps)
    side = rng.choice(["B", "A", "N"], n, p=[0.48, 0.48, 0.04])
    size = np.minimum(rng.pareto(1.5, n).astype(int) + 1, 300).astype("uint32")
    df = pd.DataFrame({"price": price, "size": size, "side": side, "action": "T",
                       "flags": np.uint8(128)}, index=pd.DatetimeIndex(ts, name="ts_recv"))
    if with_bbo:   # tbbo-like: buyer lifts ask == price, seller hits bid == price
        df["bid_px_00"] = np.where(side == "A", price, price - 0.25)
        df["ask_px_00"] = np.where(side == "B", price, price + 0.25)
    return df
