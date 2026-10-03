"""H-009 overnight drift (registry research/hypotheses/H-009.yaml)."""
from __future__ import annotations

import pandas as pd

from strategies.bars_common import COLS, next_date, px, sym_of, trade

KEYS = ("exit_at", "skip_weekends")


def trades(P, dates, p, adverse_ticks, fee_rt, point_value) -> pd.DataFrame:
    col = "p" + p["exit_at"].replace(":", "")
    out = []
    for d in dates:
        sym = sym_of(d)                                     # entry day's contract for both prices
        dn = next_date(P, sym, d)
        if dn is None or (p["skip_weekends"] and (dn - d).days > 1):
            continue
        e, x = px(P, sym, d, "p1500"), px(P, sym, dn, col)
        if e is None or x is None:
            continue
        out.append(trade(dn, 1, e, x, adverse_ticks, fee_rt, point_value))
    return pd.DataFrame(out, columns=COLS)
