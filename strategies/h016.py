"""H-016 pre-holiday effect (registry research/hypotheses/H-016.yaml)."""
from __future__ import annotations

from datetime import timedelta

import pandas as pd

from strategies.bars_common import COLS, placebo_p, prev_date, px, sym_of, trade

KEYS = ("window",)


def holidays(P) -> set:
    """Weekdays with no hourly bars 08:00-15:00 CT in either series (schedule is published in advance)."""
    have = set(P["ES.c.0"].index) | set(P["ES.c.1"].index)
    if not have:
        return set()
    d, end, out = min(have), max(have), set()
    while d <= end:
        if d.weekday() < 5 and d not in have:
            out.add(d)
        d += timedelta(days=1)
    return out


def pre_holidays(P, dates) -> set:
    hol, ds = holidays(P), sorted(dates)
    out = set()
    for a, b in zip(ds, ds[1:]):
        nxt = a + timedelta(days=1)
        while nxt.weekday() >= 5:
            nxt += timedelta(days=1)
        if nxt in hol and nxt < b:
            out.add(a)
    return out


def one(P, d, window, adverse_ticks, fee_rt, point_value):
    sym = sym_of(d)
    if window == "c2c":
        de = prev_date(P, sym, d)
        if de is None:
            return None
        e, x = px(P, sym, de, "p1500"), px(P, sym, d, "p1500")
    else:
        e, x = px(P, sym, d, "p0900"), px(P, sym, d, "p1500")
    return None if e is None or x is None else trade(d, 1, e, x, adverse_ticks, fee_rt, point_value)


def trades(P, dates, p, adverse_ticks, fee_rt, point_value) -> pd.DataFrame:
    pre = pre_holidays(P, dates)
    out = [t for d in dates if d in pre and (t := one(P, d, p["window"], adverse_ticks, fee_rt, point_value))]
    return pd.DataFrame(out, columns=COLS)


def placebo(P, dates, p, adverse_ticks, fee_rt, point_value, oos_dates, n_draws=10000, seed=5):
    """G12: random non-pre-holiday OOS days, same window and count."""
    pre, oos = pre_holidays(P, dates), set(oos_dates)
    res = {d: one(P, d, p["window"], adverse_ticks, fee_rt, point_value) for d in dates if d in oos}
    real = [t["net_pnl"] for d, t in res.items() if t and d in pre]
    pool = [t["net_pnl"] for d, t in res.items() if t and d not in pre]
    return placebo_p(real, pool, n_draws, seed)
