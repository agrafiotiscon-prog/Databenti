"""H-002: intraday momentum into the cash close, optional cumulative-delta confirmation.

Registry: research/hypotheses/H-002.yaml; protocol D-022. Interface for scripts/run_hypothesis.py:
  KEYS, prepare_day(trades, trading_date, state) -> features (state carries the previous close),
  day_trades(day, feat, params, trading_date, costs) -> list of trade dicts.
Causality: the signal uses only trades before 09:00 CT (open30) or before 14:30 CT (day); the entry
is the first trade at/after 14:30 CT, so nothing at or after the decision time feeds the decision.
"""
from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from backtest.bracket import Day, simulate
from backtest.costs import CostModel
from data.contracts import continuous_symbol
from data.sessions import CT
from features.common import BUY_AGGRESSOR, SELL_AGGRESSOR

KEYS = ("signal", "min_abs_bp", "stop_ticks", "delta_filter")
NO_STOP = 100_000          # ticks: effectively no protective stop / no target


def _ct(d: date, h: int, m: int, s: int = 0) -> pd.Timestamp:
    return pd.Timestamp(d.isoformat(), tz=CT) + pd.Timedelta(hours=h, minutes=m, seconds=s)


def prepare_day(trades: pd.DataFrame, d: date, state: dict) -> dict | None:
    """Signal inputs for day d; updates state['prev'] = (symbol, close) for the next day."""
    sym = continuous_symbol(d)
    prev = state.get("prev")
    px = trades["price"].to_numpy(float)
    ts = trades.index
    signed = np.where(trades["side"].astype(str) == BUY_AGGRESSOR, trades["size"],
                      np.where(trades["side"].astype(str) == SELL_AGGRESSOR, -trades["size"], 0)).astype(float)
    cum = np.cumsum(signed)

    t_ns = pd.DatetimeIndex(ts).as_unit("ns").asi8

    def last_before(t: pd.Timestamp):
        i = int(np.searchsorted(t_ns, t.value, "left")) - 1     # strictly before t
        return i if i >= 0 else None

    close_i = last_before(_ct(d, 15, 0))
    state["prev"] = (sym, float(px[close_i])) if close_i is not None else prev
    if prev is None or prev[0] != sym:
        return None                                   # no previous close of the same contract
    out = {"prev_close": prev[1]}
    for name, (h, m) in (("open30", (9, 0)), ("day", (14, 30))):
        i = last_before(_ct(d, h, m))
        if i is None:
            return None
        out[name] = {"ret_bp": (px[i] / prev[1] - 1) * 1e4, "delta": float(cum[i])}
    return out


def day_trades(day: Day, feat: dict | None, p: dict, d: date, costs: CostModel) -> list[dict]:
    if feat is None:
        return []
    s = feat[p["signal"]]
    side = int(np.sign(s["ret_bp"]))
    if side == 0 or abs(s["ret_bp"]) < p["min_abs_bp"]:
        return []
    if p["delta_filter"] and int(np.sign(s["delta"])) != side:
        return []
    stop = p["stop_ticks"] or NO_STOP
    tr = simulate(day, _ct(d, 14, 30).value, side, stop, NO_STOP, _ct(d, 14, 59, 30).value, costs)
    if tr is None:
        return []
    tr["trading_date"] = d
    return [tr]
