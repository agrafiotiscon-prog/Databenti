"""H-012 FOMC-cycle even weeks (registry research/hypotheses/H-012.yaml)."""
from __future__ import annotations

import pandas as pd

from strategies.bars_common import COLS, px, sym_of, trade
from strategies.h007 import fomc_dates

KEYS = ("weeks",)
WEEKS = {"even": {0, 2, 4, 6}, "w0_w2": {0, 2}}


def cycle_weeks(dates: list) -> dict:
    """trading date -> FOMC-cycle week (None before the first statement in the data)."""
    pos = {d: i for i, d in enumerate(dates)}
    stmts = [pos[d] for d in fomc_dates() if d in pos]
    out, j = {}, -1
    for i, d in enumerate(dates):
        while j + 1 < len(stmts) and stmts[j + 1] <= i:
            j += 1
        if j + 1 < len(stmts) and stmts[j + 1] - i == 1:
            out[d] = 0                                     # day -1 before the next statement
        elif j >= 0:
            out[d] = (i - stmts[j] + 1) // 5
        else:
            out[d] = None
    return out


def trades(P, dates, p, adverse_ticks, fee_rt, point_value) -> pd.DataFrame:
    wk, keep = cycle_weeks(dates), WEEKS[p["weeks"]]
    inc = [wk[d] is not None and wk[d] in keep for d in dates]
    out, i = [], 1
    while i < len(dates):
        if not inc[i]:
            i += 1
            continue
        j = i
        while j + 1 < len(dates) and inc[j + 1]:
            j += 1
        de, dx = dates[i - 1], dates[j]                     # close before the first day -> close of the last day
        sym = sym_of(de)
        e, x = px(P, sym, de, "p1500"), px(P, sym, dx, "p1500")
        if e is not None and x is not None and (dates[i] - de).days <= 5:
            out.append(trade(dx, 1, e, x, adverse_ticks, fee_rt, point_value))
        i = j + 1
    return pd.DataFrame(out, columns=COLS)
