"""H-014 time-series momentum, long/short (registry research/hypotheses/H-014.yaml).

Signal at day i's 15:00 CT close (same contract series, lookback trading days); the position is
traded at day i+1's 09:00 CT price. Contract switches (roll rule) close the old segment and open the
new one at that day's 09:00 price. A 'trade' = one contract-segment; its PnL is booked on its exit day.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from strategies.bars_common import COLS, px, sym_of, trade

KEYS = ("lookback",)


def signals(P, dates, lookback: int) -> list[int]:
    out = []
    for i, d in enumerate(dates):
        s = sym_of(d)
        idx = P[s].index
        k = idx.searchsorted(d)
        if k >= len(idx) or idx[k] != d or k - lookback < 0:
            out.append(0)
            continue
        a, b = px(P, s, idx[k - lookback], "p1500"), px(P, s, d, "p1500")
        out.append(0 if a is None or b is None or a == b else int(np.sign(b - a)))
    return out


def segments(P, dates, sides: list[int], adverse_ticks, fee_rt, point_value) -> pd.DataFrame:
    out, cur = [], None                       # cur = (side, sym, entry_px)
    for j in range(1, len(dates)):
        d, want, cs = dates[j], sides[j - 1], sym_of(dates[j])
        if cur is not None and (want != cur[0] or cs != cur[1]):
            x = px(P, cur[1], d, "p0900")
            if x is not None:
                out.append(trade(d, cur[0], cur[2], x, adverse_ticks, fee_rt, point_value))
            cur = None
        if cur is None and want != 0:
            e = px(P, cs, d, "p0900")
            if e is not None:
                cur = (want, cs, e)
    if cur is not None:
        x = px(P, cur[1], dates[-1], "p0900")
        if x is not None:
            out.append(trade(dates[-1], cur[0], cur[2], x, adverse_ticks, fee_rt, point_value))
    return pd.DataFrame(out, columns=COLS)


def trades(P, dates, p, adverse_ticks, fee_rt, point_value) -> pd.DataFrame:
    return segments(P, dates, signals(P, dates, p["lookback"]), adverse_ticks, fee_rt, point_value)
