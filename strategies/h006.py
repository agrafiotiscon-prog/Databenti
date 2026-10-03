"""H-006 fade the overnight gap after the open (registry research/hypotheses/H-006.yaml)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from strategies.bars_common import COLS, prev_date, px, sym_of, trade

KEYS = ("min_gap_bp", "exit_at")


def trades(P, dates, p, adverse_ticks, fee_rt, point_value) -> pd.DataFrame:
    col_exit = "p" + p["exit_at"].replace(":", "")
    out = []
    for d in dates:
        sym = sym_of(d)
        pdv = prev_date(P, sym, d)
        if pdv is None:
            continue
        prev, o, x = px(P, sym, pdv, "p1500"), px(P, sym, d, "p0900"), px(P, sym, d, col_exit)
        if None in (prev, o, x):
            continue
        gap = (o / prev - 1) * 1e4
        if abs(gap) < p["min_gap_bp"] or gap == 0:
            continue
        out.append(trade(d, -int(np.sign(gap)), o, x, adverse_ticks, fee_rt, point_value))
    return pd.DataFrame(out, columns=COLS)
