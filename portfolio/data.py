"""Daily bars for one root: held instrument (v.0), next instrument (v.1), per-instrument closes.

Databento ohlcv-1d bars are UTC days; weekend bars (Sunday evening open) are dropped because the
Monday bar's close supersedes them. Each bar carries the instrument_id it resolved to.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


def load_bars(path: Path) -> pd.DataFrame:
    import databento as db
    df = db.DBNStore.from_file(path).to_df(pretty_ts=True)
    d = pd.DatetimeIndex(df.index)
    df = df[d.weekday < 5].copy()
    df.index = pd.Index([ts.date() for ts in pd.DatetimeIndex(df.index)], name="date")
    df = df[~df.index.duplicated(keep="last")]
    return df[["instrument_id", "close", "volume"]]


@dataclass
class RootData:
    root: str
    dates: list                      # trading dates with a v.0 bar
    held: pd.Series                  # date -> instrument_id of v.0
    nxt: pd.Series                   # date -> instrument_id of v.1 (may be missing)
    closes: dict                     # instrument_id -> pd.Series(date -> close)
    expiry_rank: dict                # instrument_id -> sortable rank (earlier expiry = smaller)


def build(root: str, v0: pd.DataFrame, v1: pd.DataFrame) -> RootData:
    closes: dict = {}
    for df in (v0, v1):
        for iid, g in df.groupby("instrument_id"):
            s = g["close"]
            closes[iid] = s if iid not in closes else pd.concat([closes[iid], s[~s.index.isin(closes[iid].index)]]).sort_index()
    # Expiry order is public calendar metadata (not price information): the earlier-expiring contract
    # stops appearing in the top two by volume first; ties at the end of the data use first appearance.
    seen = pd.concat([v0["instrument_id"], v1["instrument_id"]])
    first = {i: g.index.min() for i, g in seen.groupby(seen)}
    last = {i: g.index.max() for i, g in seen.groupby(seen)}
    end = seen.index.max()
    rank = {i: (last[i] if last[i] < end else pd.Timestamp.max.date(), first[i]) for i in first}
    return RootData(root, list(v0.index), v0["instrument_id"], v1["instrument_id"], closes, rank)


def chain_returns(rd: RootData) -> pd.Series:
    """Return of holding the v.0 instrument of day t-1 from t-1's close to t's close (NaN if unknown)."""
    out = pd.Series(np.nan, index=pd.Index(rd.dates))
    for a, b in zip(rd.dates, rd.dates[1:]):
        s = rd.closes.get(rd.held[a])
        if s is not None and a in s.index and b in s.index and s[a] > 0:
            out[b] = s[b] / s[a] - 1
    return out


def carry_sign(rd: RootData) -> pd.Series:
    """sign(log(P_near / P_far)) from the two top-volume instruments on each date (0 if unknown)."""
    out = pd.Series(0.0, index=pd.Index(rd.dates))
    for d in rd.dates:
        i0, i1 = rd.held.get(d), rd.nxt.get(d)
        if i1 is None or (isinstance(i1, float) and np.isnan(i1)) or i0 == i1:
            continue
        p0, p1 = rd.closes[i0].get(d), rd.closes[i1].get(d)
        if p0 is None or p1 is None or p0 <= 0 or p1 <= 0:
            continue
        near, far = (p0, p1) if rd.expiry_rank[i0] < rd.expiry_rank[i1] else (p1, p0)
        out[d] = float(np.sign(np.log(near / far)))
    return out
