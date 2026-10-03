"""H-019 month-end rebalancing fade (registry research/hypotheses/H-019.yaml)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from strategies.bars_common import COLS, placebo_p, px, same_contract_px, sym_of, trade

KEYS = ("min_abs_bp",)
HOLD, LOOKBACK = 4, 17


def ret_bp(P, ds, i0: int, i1: int):
    """Return (bp) of the contract traded on ds[i1], from its 15:00 close on ds[i0] to ds[i1]."""
    a, b = same_contract_px(P, ds[i1], ds[i0], "p1500"), px(P, sym_of(ds[i1]), ds[i1], "p1500")
    return None if a is None or b is None else (b / a - 1) * 1e4


def closes(P, dates) -> list:
    """Trading days with a 15:00 CT close (drops holiday sessions halted early)."""
    return [d for d in sorted(dates) if px(P, sym_of(d), d, "p1500") is not None]


def fade_trade(P, ds, ie, ix, sig_bp, min_abs_bp, adverse_ticks, fee_rt, point_value):
    if sig_bp is None or sig_bp == 0 or abs(sig_bp) < min_abs_bp:
        return None
    a, b = px(P, sym_of(ds[ie]), ds[ie], "p1500"), same_contract_px(P, ds[ie], ds[ix], "p1500")
    if a is None or b is None:
        return None
    return trade(ds[ix], -int(np.sign(sig_bp)), a, b, adverse_ticks, fee_rt, point_value)


def month_windows(ds) -> list:
    """(index of previous month's last day, index of T-4, index of T) per month."""
    last = [i for i in range(len(ds)) if i + 1 == len(ds) or (ds[i + 1].year, ds[i + 1].month) != (ds[i].year, ds[i].month)]
    out = []
    for k in range(1, len(last)):
        t, m0 = last[k], last[k - 1]
        if t - HOLD > m0:
            out.append((m0, t - HOLD, t))
    return out


def trades(P, dates, p, adverse_ticks, fee_rt, point_value) -> pd.DataFrame:
    ds = closes(P, dates)
    out = [t for m0, ie, ix in month_windows(ds)
           if (t := fade_trade(P, ds, ie, ix, ret_bp(P, ds, m0, ie), p["min_abs_bp"], adverse_ticks, fee_rt, point_value))]
    return pd.DataFrame(out, columns=COLS)


def turn_days(ds) -> set:
    """Indices in the last 6 or first 2 trading days of any month."""
    ym = [(d.year, d.month) for d in ds]
    out = set()
    for i in range(len(ds)):
        from_start = sum(1 for j in range(max(i - 2, 0), i) if ym[j] == ym[i])
        to_end = sum(1 for j in range(i + 1, min(i + 7, len(ds))) if ym[j] == ym[i])
        if (i >= 2 and from_start < 2) or (i + 6 < len(ds) and to_end < 6):
            out.add(i)
    return out


def placebo(P, dates, p, adverse_ticks, fee_rt, point_value, oos_dates, n_draws=10000, seed=5):
    """G12: is month-end special? Same fade (trailing 17-day return, 4-day hold) at non-turn-of-month times."""
    ds, oos = closes(P, dates), set(oos_dates)
    real = [t["net_pnl"] for m0, ie, ix in month_windows(ds) if ds[ix] in oos
            and (t := fade_trade(P, ds, ie, ix, ret_bp(P, ds, m0, ie), p["min_abs_bp"], adverse_ticks, fee_rt, point_value))]
    bad, pool = turn_days(ds), []
    for ie in range(LOOKBACK, len(ds) - HOLD):
        ix = ie + HOLD
        if ds[ix] not in oos or any(j in bad for j in range(ie, ix + 1)):
            continue
        t = fade_trade(P, ds, ie, ix, ret_bp(P, ds, ie - LOOKBACK, ie), p["min_abs_bp"], adverse_ticks, fee_rt, point_value)
        if t:
            pool.append(t["net_pnl"])
    return placebo_p(real, pool, n_draws, seed)
