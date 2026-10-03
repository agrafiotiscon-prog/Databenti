"""H-013 intraday periodicity (registry research/hypotheses/H-013.yaml)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from strategies.bars_common import COLS, sym_of, trade

KEYS = ("lookback", "min_abs_bp")
HOURS = ["0900", "1000", "1100", "1200", "1300", "1400"]


def _returns(t: pd.DataFrame) -> pd.DataFrame:
    r = {}
    for h in HOURS:
        a, b = f"p{h}", f"p{int(h[:2]) + 1:02d}00"
        if a in t.columns and b in t.columns:
            r[h] = t[b] / t[a] - 1
    return pd.DataFrame(r)


def trades(P, dates, p, adverse_ticks, fee_rt, point_value) -> pd.DataFrame:
    sig = {}
    for sym, t in P.items():
        r = _returns(t) * 1e4
        sig[sym] = (r.shift(1).rolling(p["lookback"], min_periods=p["lookback"]).mean(), t)
    out = []
    for d in dates:
        sym = sym_of(d)
        m, t = sig[sym]
        if d not in m.index:
            continue
        for h in HOURS:
            mu = m.at[d, h] if h in m.columns else np.nan
            a, b = f"p{h}", f"p{int(h[:2]) + 1:02d}00"
            if not np.isfinite(mu) or mu == 0 or abs(mu) < p["min_abs_bp"] or pd.isna(t.at[d, a]) or pd.isna(t.at[d, b]):
                continue
            out.append(trade(d, int(np.sign(mu)), float(t.at[d, a]), float(t.at[d, b]), adverse_ticks, fee_rt, point_value))
    return pd.DataFrame(out, columns=COLS)
