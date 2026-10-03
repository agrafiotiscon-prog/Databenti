"""H-007 pre-FOMC drift (registry research/hypotheses/H-007.yaml); dates from config/fomc_dates.csv."""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

from strategies.bars_common import COLS, prev_date, px, sym_of, trade

KEYS = ("window",)
FOMC = Path(__file__).resolve().parent.parent / "config" / "fomc_dates.csv"


def fomc_dates() -> list[date]:
    return [date.fromisoformat(l) for l in FOMC.read_text().splitlines() if l[:1].isdigit()]


def trades(P, dates, p, adverse_ticks, fee_rt, point_value) -> pd.DataFrame:
    have = set(dates)
    out = []
    for d in fomc_dates():
        if d not in have:
            continue
        if p["window"] == "lm24h":
            sym = sym_of(prev_date(P, sym_of(d), d) or d)
            de = prev_date(P, sym, d)
            if de is None:
                continue
            e, x = px(P, sym, de, "p1300"), px(P, sym, d, "p1300")
        else:
            sym = sym_of(d)
            e, x = px(P, sym, d, "p0900"), px(P, sym, d, "p1300")
        if e is None or x is None:
            continue
        out.append(trade(d, 1, e, x, adverse_ticks, fee_rt, point_value))
    return pd.DataFrame(out, columns=COLS)
