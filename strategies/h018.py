"""H-018 Monday reversal (registry research/hypotheses/H-018.yaml)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from strategies.bars_common import COLS, placebo_p, prev_date, px, sym_of, trade

KEYS = ("min_abs_bp",)


def fade(P, d, min_abs_bp, adverse_ticks, fee_rt, point_value):
    """Fade the previous session's 09:00->15:00 move during d's 09:00->15:00 (same contract series)."""
    sym = sym_of(d)
    pdv = prev_date(P, sym, d)
    if pdv is None:
        return None, None
    o, c = px(P, sym, pdv, "p0900"), px(P, sym, pdv, "p1500")
    e, x = px(P, sym, d, "p0900"), px(P, sym, d, "p1500")
    if None in (o, c, e, x):
        return None, None
    r = (c / o - 1) * 1e4
    if r == 0 or abs(r) < min_abs_bp:
        return None, None
    return pdv, trade(d, -int(np.sign(r)), e, x, adverse_ticks, fee_rt, point_value)


def is_monday_after_friday(d, pdv) -> bool:
    return d.weekday() == 0 and pdv.weekday() == 4 and (d - pdv).days == 3


def trades(P, dates, p, adverse_ticks, fee_rt, point_value) -> pd.DataFrame:
    out = []
    for d in dates:
        pdv, t = fade(P, d, p["min_abs_bp"], adverse_ticks, fee_rt, point_value)
        if t and is_monday_after_friday(d, pdv):
            out.append(t)
    return pd.DataFrame(out, columns=COLS)


def placebo(P, dates, p, adverse_ticks, fee_rt, point_value, oos_dates, n_draws=10000, seed=5):
    """G12 (added before any result, stricter only): is Monday special? Random same-rule fades on
    Tuesday-Friday OOS days, same threshold and count."""
    oos, real, pool = set(oos_dates), [], []
    for d in dates:
        if d not in oos:
            continue
        pdv, t = fade(P, d, p["min_abs_bp"], adverse_ticks, fee_rt, point_value)
        if not t:
            continue
        (real if is_monday_after_friday(d, pdv) else pool if d.weekday() != 0 else []).append(t["net_pnl"])
    return placebo_p(real, pool, n_draws, seed)
