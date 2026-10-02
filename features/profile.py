"""Volume profile (POC, value area) and VWAP with bands (feature 3).

* Developing profile: per bar, using ONLY trades of the session with
  ts_recv < bar end. Today's *completed* profile is never available intraday.
* Prior-session completed levels are fine to use in the next session.
* POC tie-break: price closest to the session's volume-weighted mean, then the
  lower price (deterministic).
* Value area (default 70%): CBOT method -- from the POC, repeatedly add the
  adjacent block of two prices (above vs below) with the larger volume; ties go
  above; a side with < 2 prices left contributes what it has.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .common import TICK, bar_start, clean_trades


def value_area(vol_by_price: pd.Series, pct: float = 0.70) -> tuple[float, float, float]:
    """Return (poc, val, vah) from a Series indexed by price (any order)."""
    v = vol_by_price[vol_by_price > 0].sort_index()
    if v.empty:
        return (np.nan, np.nan, np.nan)
    prices = v.index.to_numpy(dtype=float)
    vols = v.to_numpy(dtype=float)
    vwmean = float((prices * vols).sum() / vols.sum())
    top = np.flatnonzero(vols == vols.max())
    # tie-break: closest to volume-weighted mean, then lower price
    i_poc = int(min(top, key=lambda i: (abs(prices[i] - vwmean), prices[i])))
    lo = hi = i_poc
    total, inside = vols.sum(), vols[i_poc]
    while inside < pct * total and (lo > 0 or hi < len(vols) - 1):
        above = vols[hi + 1: hi + 3].sum() if hi < len(vols) - 1 else -1.0
        below = vols[max(lo - 2, 0): lo].sum() if lo > 0 else -1.0
        if above >= below:
            step = min(2, len(vols) - 1 - hi)
            inside += vols[hi + 1: hi + 1 + step].sum()
            hi += step
        else:
            step = min(2, lo)
            inside += vols[lo - step: lo].sum()
            lo -= step
    return float(prices[i_poc]), float(prices[lo]), float(prices[hi])


def developing_profile(trades: pd.DataFrame, freq: str = "1min", pct: float = 0.70,
                       tick: float = TICK) -> pd.DataFrame:
    """POC/VAL/VAH of the session so far, emitted at each bar end (known_at)."""
    t = clean_trades(trades, tick)
    t["bar_start"] = bar_start(t.index, freq)
    per_bar = t.groupby(["bar_start", "price"])["size"].sum()
    cum = pd.Series(dtype=float)
    rows = []
    for b, vols in per_bar.groupby(level=0, sort=True):
        cum = cum.add(vols.droplevel(0), fill_value=0)
        poc, val, vah = value_area(cum, pct)
        rows.append({"bar_start": b, "poc": poc, "val": val, "vah": vah,
                     "known_at": b + pd.Timedelta(freq)})
    return pd.DataFrame(rows).set_index("bar_start") if rows else pd.DataFrame(
        columns=["poc", "val", "vah", "known_at"])


def session_levels(trades: pd.DataFrame, pct: float = 0.70, tick: float = TICK) -> dict:
    """Completed-session levels -- only for use in LATER sessions."""
    t = clean_trades(trades, tick)
    poc, val, vah = value_area(t.groupby("price")["size"].sum(), pct)
    vw = vwap(trades, tick=tick)
    return {"poc": poc, "val": val, "vah": vah, "high": float(t["price"].max()),
            "low": float(t["price"].min()), "vwap": float(vw["vwap"].iloc[-1]),
            "known_at": t.index[-1]}


def vwap(trades: pd.DataFrame, bands=(1.0, 2.0, 3.0), tick: float = TICK) -> pd.DataFrame:
    """Running session VWAP and volume-weighted std bands, per trade (known_at = ts_recv)."""
    t = clean_trades(trades, tick)
    p0 = t["price"].iloc[0] if len(t) else 0.0       # centre prices for numerical precision
    x = t["price"] - p0
    v = t["size"].astype(float)
    cv = v.cumsum()
    m1 = (v * x).cumsum() / cv
    m2 = (v * x * x).cumsum() / cv
    sd = np.sqrt(np.maximum(m2 - m1 * m1, 0.0))
    out = pd.DataFrame({"vwap": m1 + p0, "sd": sd}, index=t.index)
    for k in bands:
        out[f"upper_{k:g}"] = out["vwap"] + k * sd
        out[f"lower_{k:g}"] = out["vwap"] - k * sd
    out["known_at"] = out.index
    return out


def vwap_bars(trades: pd.DataFrame, freq: str = "1min", **kw) -> pd.DataFrame:
    """VWAP/bands as of each bar end (last trade value inside the bar)."""
    vw = vwap(trades, **kw)
    out = vw.groupby(bar_start(vw.index, freq)).last()
    out.index.name = "bar_start"
    out["known_at"] = out.index + pd.Timedelta(freq)
    return out
