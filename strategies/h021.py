"""H-021 buy after a sharp 3-day decline, fixed hold (registry research/hypotheses/H-021.yaml)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from strategies.bars_common import COLS, placebo_p, px, same_contract_px, sym_of, trade
from strategies.h020 import daily_returns

KEYS = ("z_min", "hold")
WIN, VOL_N, VOL_MIN = 3, 63, 50


def closes(P, dates) -> list:
    return [d for d in sorted(dates) if px(P, sym_of(d), d, "p1500") is not None]


def zscores(P, ds) -> np.ndarray:
    """z[i] known at ds[i]'s 15:00 close; vol from the 63 returns ending at i-3 (no overlap)."""
    r = np.array([np.nan if x is None else x for x in daily_returns(P, ds)])
    z = np.full(len(ds), np.nan)
    for i in range(WIN + VOL_N, len(ds)):
        w = r[i - WIN + 1:i + 1]
        v = r[i - WIN - VOL_N + 1:i - WIN + 1]
        v = v[~np.isnan(v)]
        if np.isnan(w).any() or len(v) < VOL_MIN:
            continue
        z[i] = (np.prod(1 + w) - 1) / (v.std(ddof=1) * np.sqrt(WIN))
    return z


def hold_trade(P, ds, j, hold, adverse_ticks, fee_rt, point_value):
    """Long from ds[j] 09:00 to ds[j + hold] 09:00 on ds[j]'s contract."""
    if j + hold >= len(ds):
        return None
    e = px(P, sym_of(ds[j]), ds[j], "p0900")
    x = same_contract_px(P, ds[j], ds[j + hold], "p0900")
    return None if e is None or x is None else trade(ds[j + hold], 1, e, x, adverse_ticks, fee_rt, point_value)


def signal_days(z, z_min) -> list[int]:
    return [i for i in range(len(z)) if not np.isnan(z[i]) and z[i] <= -z_min]


def trades(P, dates, p, adverse_ticks, fee_rt, point_value) -> pd.DataFrame:
    ds = closes(P, dates)
    z, out, free_from = zscores(P, ds), [], 0
    for i in signal_days(z, p["z_min"]):
        if i < free_from:
            continue
        t = hold_trade(P, ds, i + 1, p["hold"], adverse_ticks, fee_rt, point_value)
        if t:
            out.append(t)
            free_from = i + 1 + p["hold"]
    return pd.DataFrame(out, columns=COLS)


def placebo(P, dates, p, adverse_ticks, fee_rt, point_value, oos_dates, n_draws=10000, seed=5):
    """G12: random OOS entry days that do not follow a signal day; same hold and count."""
    ds, oos = closes(P, dates), set(oos_dates)
    sig = set(signal_days(zscores(P, ds), p["z_min"]))
    real = trades(P, dates, p, adverse_ticks, fee_rt, point_value)
    real = real.loc[real["trading_date"].isin(oos), "net_pnl"].tolist()
    pool = [t["net_pnl"] for j in range(1, len(ds)) if j - 1 not in sig
            and (t := hold_trade(P, ds, j, p["hold"], adverse_ticks, fee_rt, point_value)) and t["trading_date"] in oos]
    return placebo_p(real, pool, n_draws, seed)
