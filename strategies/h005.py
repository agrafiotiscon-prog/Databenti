"""H-005 turn of the month (registry research/hypotheses/H-005.yaml)."""
from __future__ import annotations

import pandas as pd

from strategies.bars_common import COLS, px, sym_of, trade

KEYS = ("entry_k", "exit_day")


def trades(P, dates, p, adverse_ticks, fee_rt, point_value) -> pd.DataFrame:
    s = pd.Series(dates, index=pd.Index(dates))
    months = s.groupby([d.year * 12 + d.month for d in dates])
    keys = sorted(months.groups)
    out = []
    for m, nxt in zip(keys[:-1], keys[1:]):
        if nxt != m + 1:
            continue
        cur, new = list(months.get_group(m)), list(months.get_group(nxt))
        if len(cur) < p["entry_k"] or len(new) < p["exit_day"]:
            continue
        de, dx = cur[-p["entry_k"]], new[p["exit_day"] - 1]
        sym = sym_of(de)                                   # entry day's contract for both prices
        e, x = px(P, sym, de, "p1500"), px(P, sym, dx, "p1500")
        if e is None or x is None:
            continue
        out.append(trade(dx, 1, e, x, adverse_ticks, fee_rt, point_value))
    return pd.DataFrame(out, columns=COLS)
