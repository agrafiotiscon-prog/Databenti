"""H-020 volatility-managed exposure, long only (registry research/hypotheses/H-020.yaml).

Regime known at day i's 15:00 CT close; positions are traded at day i+1's 09:00 price via the
H-014 segment accounting (rolls = extra round trip).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from strategies.bars_common import px, same_contract_px, sym_of
from strategies.h014 import segments

KEYS = ("vol_lookback",)
MEDIAN_DAYS, MIN_SHARE = 252, 0.8


def daily_returns(P, ds) -> list:
    out = [None]
    for i in range(1, len(ds)):
        a, b = same_contract_px(P, ds[i], ds[i - 1], "p1500"), px(P, sym_of(ds[i]), ds[i], "p1500")
        out.append(None if a is None or b is None else b / a - 1)
    return out


def regime(P, dates, lookback: int) -> list[int]:
    """1 = long, 0 = flat, per date in `dates` (days without a 15:00 close carry the last value)."""
    ds = [d for d in dates if px(P, sym_of(d), d, "p1500") is not None]
    r = np.array([np.nan if x is None else x for x in daily_returns(P, ds)])
    vol = np.full(len(ds), np.nan)
    for i in range(lookback, len(ds)):
        w = r[i - lookback + 1:i + 1]
        w = w[~np.isnan(w)]
        if len(w) >= MIN_SHARE * lookback:
            vol[i] = w.std(ddof=1) * np.sqrt(252)
    sig = {}
    for i in range(len(ds)):
        past = vol[max(i - MEDIAN_DAYS, 0):i]
        past = past[~np.isnan(past)]
        sig[ds[i]] = int(vol[i] < np.median(past)) if not np.isnan(vol[i]) and len(past) >= MIN_SHARE * MEDIAN_DAYS else 0
    out, last = [], 0
    for d in dates:
        last = sig.get(d, last)
        out.append(last)
    return out


def trades(P, dates, p, adverse_ticks, fee_rt, point_value) -> pd.DataFrame:
    return segments(P, dates, regime(P, dates, p["vol_lookback"]), adverse_ticks, fee_rt, point_value)


def placebo(P, dates, p, adverse_ticks, fee_rt, point_value, oos_dates, n_draws=500, seed=5):
    """G12: circular shifts (>= 21 days) of the regime series keep its long share and spell lengths."""
    oos = set(oos_dates)
    sides = regime(P, dates, p["vol_lookback"])

    def oos_net(s):
        t = segments(P, dates, s, adverse_ticks, fee_rt, point_value)
        return float(t.loc[t["trading_date"].isin(oos), "net_pnl"].sum())

    real, n = oos_net(sides), len(sides)
    if n < 100:
        return None
    rng = np.random.default_rng(seed)
    shifted = [oos_net(list(np.roll(sides, int(k)))) for k in rng.integers(21, n - 21, size=n_draws)]
    return float((np.array(shifted) >= real).mean())
