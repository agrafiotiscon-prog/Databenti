"""H-017 option-expiration week (registry research/hypotheses/H-017.yaml)."""
from __future__ import annotations

from datetime import timedelta

import pandas as pd

from data.contracts import third_friday
from strategies.bars_common import COLS, next_date, placebo_p, px, sym_of, trade

KEYS = ("months",)
QUARTERLY = (3, 6, 9, 12)


def windows(dates, months: str) -> list:
    """(entry Friday, exit Thursday) per OPEX month; skipped when either day is not a trading date."""
    ds = set(dates)
    if not ds:
        return []
    out = []
    y, m = min(ds).year, min(ds).month
    while (y, m) <= (max(ds).year, max(ds).month):
        if months == "all" or m in QUARTERLY:
            opx = third_friday(y, m)
            e, x = opx - timedelta(days=7), opx - timedelta(days=1)
            if e in ds and x in ds:
                out.append((e, x))
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def hold(P, e, x, adverse_ticks, fee_rt, point_value):
    sym = sym_of(e)                                   # entry day's contract for both prices
    a, b = px(P, sym, e, "p1500"), px(P, sym, x, "p1500")
    return None if a is None or b is None else trade(x, 1, a, b, adverse_ticks, fee_rt, point_value)


def trades(P, dates, p, adverse_ticks, fee_rt, point_value) -> pd.DataFrame:
    out = [t for e, x in windows(dates, p["months"]) if (t := hold(P, e, x, adverse_ticks, fee_rt, point_value))]
    return pd.DataFrame(out, columns=COLS)


def placebo(P, dates, p, adverse_ticks, fee_rt, point_value, oos_dates, n_draws=10000, seed=5):
    """G12: random 4-trading-day holds (exit in OOS) that do not overlap any OPEX week, same count."""
    oos = set(oos_dates)
    blocked = set()
    for e, x in windows(dates, "all"):
        d = e
        while d <= x:
            blocked.add(d)
            d += timedelta(days=1)
    real = [t["net_pnl"] for e, x in windows(dates, p["months"]) if x in oos
            and (t := hold(P, e, x, adverse_ticks, fee_rt, point_value))]
    pool = []
    for e in dates:
        sym, path = sym_of(e), [e]
        for _ in range(4):
            n = next_date(P, sym, path[-1])
            if n is None:
                break
            path.append(n)
        if len(path) < 5 or path[-1] not in oos or any(d in blocked for d in path):
            continue
        if (t := hold(P, e, path[-1], adverse_ticks, fee_rt, point_value)):
            pool.append(t["net_pnl"])
    return placebo_p(real, pool, n_draws, seed)
