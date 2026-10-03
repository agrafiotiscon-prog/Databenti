"""H-015 macro-announcement-day premium (registry research/hypotheses/H-015.yaml)."""
from __future__ import annotations

from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from strategies.bars_common import COLS, prev_date, px, sym_of, trade
from strategies.h007 import fomc_dates

KEYS = ("events", "window")
MACRO = Path(__file__).resolve().parent.parent / "config" / "macro_dates.csv"


def macro_dates(kind: str) -> set:
    out = set()
    for l in MACRO.read_text().splitlines():
        if l[:1].isdigit():
            d, k = l.split(",")
            if kind == "both" or k == kind:
                out.add(date.fromisoformat(d))
    return out


def one(P, d, window, adverse_ticks, fee_rt, point_value):
    sym = sym_of(d)
    if window == "c2c":
        de = prev_date(P, sym, d)
        if de is None:
            return None
        e, x = px(P, sym, de, "p1500"), px(P, sym, d, "p1500")
    else:
        e, x = px(P, sym, d, "p0800"), px(P, sym, d, "p1500")
    return None if e is None or x is None else trade(d, 1, e, x, adverse_ticks, fee_rt, point_value)


def trades(P, dates, p, adverse_ticks, fee_rt, point_value) -> pd.DataFrame:
    ev = macro_dates(p["events"])
    out = [t for d in dates if d in ev and (t := one(P, d, p["window"], adverse_ticks, fee_rt, point_value))]
    return pd.DataFrame(out, columns=COLS)


def placebo(P, dates, p, adverse_ticks, fee_rt, point_value, oos_dates, n_draws=10000, seed=5) -> float:
    """G12: random non-event, non-FOMC days, same window and count, over oos_dates."""
    ev, fomc = macro_dates("both"), set(fomc_dates())
    oos = set(oos_dates)
    real = [t["net_pnl"] for d in dates if d in oos and d in macro_dates(p["events"])
            and (t := one(P, d, p["window"], adverse_ticks, fee_rt, point_value))]
    pool = np.array([t["net_pnl"] for d in dates if d in oos and d not in ev and d not in fomc
                     and (t := one(P, d, p["window"], adverse_ticks, fee_rt, point_value))])
    if not real or len(pool) < len(real):
        return None
    rng = np.random.default_rng(seed)
    draws = np.array([rng.choice(pool, size=len(real), replace=False).mean() for _ in range(n_draws)])
    return float((draws >= np.mean(real)).mean())
