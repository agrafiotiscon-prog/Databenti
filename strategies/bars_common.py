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
