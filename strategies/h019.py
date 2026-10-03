"""H-019 month-end rebalancing fade (registry research/hypotheses/H-019.yaml)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from strategies.bars_common import COLS, placebo_p, px, sym_of, trade

KEYS = ("min_abs_bp",)
HOLD, LOOKBACK = 4, 17


def chained_bp(P, ds, i0: int, i1: int):
    """Return (bp) from ds[i0] to ds[i1] 15:00 closes, chained from same-contract daily returns."""
    g = 1.0
    for j in range(i0 + 1, i1 + 1):
        s = sym_of(ds[j])
        a, b = px(P, s, ds[j - 1], "p1500"), px(P, s, ds[j], "p1500")
        if a is None or b is None:
            return None
        g *= b / a
    return (g - 1) * 1e4


def fade_trade(P, ds, ie, ix, sig_bp, min_abs_bp, adverse_ticks, fee_rt, point_value):
    if sig_bp is None or sig_bp == 0 or abs(sig_bp) < min_abs_bp:
        return None
    s = sym_of(ds[ie])
    a, b = px(P, s, ds[ie], "p1500"), px(P, s, ds[ix], "p1500")
    if a is None or b is None:
        return None
    return trade(ds[ix], -int(np.sign(sig_bp)), a, b, adverse_ticks, fee_rt, point_value)


def month_windows(ds) -> list:
    """(index of previous month's last day, index of T-4, index of T) per month."""
    last = [i for i in range(len(ds)) if i + 1 == len(ds) or (ds[i + 1].year, ds[i + 1].month) != (ds[i].year, ds[i].month)]
    out = []
    for k in range(1, len(last)):
        t, m0 = last[k], last[k - 1]
        if t - HOLD > m0:
            out.append((m0, t - HOLD, t))
    return out


def trades(P, dates, p, adverse_ticks, fee_rt, point_value) -> pd.DataFrame:
    ds = sorted(dates)
    out = [t for m0, ie, ix in month_windows(ds)
           if (t := fade_trade(P, ds, ie, ix, chained_bp(P, ds, m0, ie), p["min_abs_bp"], adverse_ticks, fee_rt, point_value))]
    return pd.DataFrame(out, columns=COLS)


def turn_days(ds) -> set:
    """Indices in the last 6 or first 2 trading days of any month."""
    ym = [(d.year, d.month) for d in ds]
    out = set()
    for i in range(len(ds)):
        from_start = sum(1 for j in range(max(i - 2, 0), i) if ym[j] == ym[i])
        to_end = sum(1 for j in range(i + 1, min(i + 7, len(ds))) if ym[j] == ym[i])
        if (i >= 2 and from_start < 2) or (i + 6 < len(ds) and to_end < 6):
            out.add(i)
    return out


def placebo(P, dates, p, adverse_ticks, fee_rt, point_value, oos_dates, n_draws=10000, seed=5):
    """G12: is month-end special? Same fade (trailing 17-day return, 4-day hold) at non-turn-of-month times."""
    ds, oos = sorted(dates), set(oos_dates)
    real = [t["net_pnl"] for m0, ie, ix in month_windows(ds) if ds[ix] in oos
            and (t := fade_trade(P, ds, ie, ix, chained_bp(P, ds, m0, ie), p["min_abs_bp"], adverse_ticks, fee_rt, point_value))]
    bad, pool = turn_days(ds), []
    for ie in range(LOOKBACK, len(ds) - HOLD):
        ix = ie + HOLD
        if ds[ix] not in oos or any(j in bad for j in range(ie, ix + 1)):
            continue
        t = fade_trade(P, ds, ie, ix, chained_bp(P, ds, ie - LOOKBACK, ie), p["min_abs_bp"], adverse_ticks, fee_rt, point_value)
        if t:
            pool.append(t["net_pnl"])
    return placebo_p(real, pool, n_draws, seed)
