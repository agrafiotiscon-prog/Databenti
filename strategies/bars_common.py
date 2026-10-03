"""Shared helpers for bar-based strategies (hourly tables from scripts/run_bars_hypothesis.py)."""
from __future__ import annotations

import pandas as pd

from data.contracts import continuous_symbol

TICK = 0.25
COLS = ["trading_date", "side", "gross_pnl", "fees", "net_pnl", "ticks"]


def px(P: dict, sym: str, d, col: str):
    t = P[sym]
    if d not in t.index or col not in t.columns:
        return None
    v = t.at[d, col]
    return None if pd.isna(v) else float(v)


def prev_date(P: dict, sym: str, d, max_gap_days: int = 5):
    idx = P[sym].index
    i = idx.searchsorted(d) - 1
    if i < 0 or (d - idx[i]).days > max_gap_days:
        return None
    return idx[i]


def trade(exit_date, side: int, entry: float, exit_: float, adverse_ticks: float, fee_rt: float, point_value: float) -> dict:
    e = entry + side * adverse_ticks * TICK
    x = exit_ - side * adverse_ticks * TICK
    gross = side * (x - e) * point_value
    return {"trading_date": exit_date, "side": side, "gross_pnl": gross, "fees": fee_rt, "net_pnl": gross - fee_rt,
            "ticks": gross / (point_value * TICK)}


def sym_of(d) -> str:
    return continuous_symbol(d)


def next_date(P: dict, sym: str, d, max_gap_days: int = 5):
    idx = P[sym].index
    i = idx.searchsorted(d, side="right")
    if i >= len(idx) or (idx[i] - d).days > max_gap_days:
        return None
    return idx[i]


def placebo_p(real: list, pool: list, n_draws: int = 10000, seed: int = 5):
    """One-sided p: share of random same-size draws (without replacement) from `pool` whose mean >= mean(real)."""
    import numpy as np
    pool = np.asarray(pool, float)
    if not len(real) or len(pool) < len(real):
        return None
    rng = np.random.default_rng(seed)
    draws = np.array([rng.choice(pool, size=len(real), replace=False).mean() for _ in range(n_draws)])
    return float((draws >= np.mean(real)).mean())


def _qi(exp) -> int:
    return exp.year * 4 + exp.month // 3


def same_contract_px(P: dict, ref, d, col: str):
    """Price on date d of the contract we trade on date ref (sym_of(ref)), read from whichever
    continuous rank holds that contract on d (Databento's c.0 = nearest expiry on or after d)."""
    from data.contracts import front_expiry
    k = _qi(front_expiry(ref)) + int(sym_of(ref)[-1])
    r = k - _qi(front_expiry(d))
    return px(P, f"ES.c.{r}", d, col) if r in (0, 1) else None
