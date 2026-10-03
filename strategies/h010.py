"""H-010 daily reversal (registry research/hypotheses/H-010.yaml)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from strategies.bars_common import COLS, prev_date, px, sym_of, trade

KEYS = ("min_abs_bp", "entry_at")


def trades(P, dates, p, adverse_ticks, fee_rt, point_value) -> pd.DataFrame:
    col = "p" + p["entry_at"].replace(":", "")
    out = []
    for d in dates:
        sym = sym_of(d)
        pdv = prev_date(P, sym, d)
        if pdv is None:
            continue
        o, c = px(P, sym, pdv, "p0900"), px(P, sym, pdv, "p1500")
        e, x = px(P, sym, d, col), px(P, sym, d, "p1500")
        if None in (o, c, e, x):
            continue
        r = (c / o - 1) * 1e4
        if r == 0 or abs(r) < p["min_abs_bp"]:
            continue
        out.append(trade(d, -int(np.sign(r)), e, x, adverse_ticks, fee_rt, point_value))
    return pd.DataFrame(out, columns=COLS)
