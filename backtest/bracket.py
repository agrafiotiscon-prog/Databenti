"""Fast path for single-entry bracket trades (Phase 5). Same rules as backtest.engine, vectorised.

For one signal (known_at, side) on an L1 frame:
  1. The strategy acts on the first record i0 with ts >= known_at; the market order arrives at
     ts[i0] + latency and fills on the first record j with ts >= arrival at the WORSE of the books
     in records max(j-1, i0)..j (engine.run semantics).
  2. Stop and target are sent when the fill is seen (ts[j]) and become active on the first record
     k with ts >= ts[j] + latency. Target (limit) fills only on a trade strictly through it
     (trade_through) at the target price. Stop triggers on a trade at/through it and fills at the
     worse of the books at the trigger record and the next one. Same record: the stop wins
     (pessimistic).
  3. Time stop / session flatten: a market exit is sent on the first record with ts >= exit time;
     a bracket that fills before that market order arrives wins; otherwise the market exit fills
     at the worse book after latency.
`backtest.engine` remains the reference; tests/test_bracket.py checks the two agree.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .costs import CostModel


@dataclass
class Day:
    t: np.ndarray        # int64 ns, ts_recv in file order
    bid: np.ndarray
    ask: np.ndarray
    px: np.ndarray       # trade price (nan if none)

    @classmethod
    def from_l1(cls, l1: pd.DataFrame) -> "Day":
        return cls(pd.DatetimeIndex(l1.index).as_unit("ns").asi8, l1["bid_px"].to_numpy(float),
                   l1["ask_px"].to_numpy(float), l1["price"].to_numpy(float))


def _first_at_or_after(t: np.ndarray, ts: int) -> int:
    return int(np.searchsorted(t, ts, side="left"))


def _worse(day: Day, side: int, lo: int, hi: int) -> float:
    return float(np.nanmax(day.ask[lo:hi + 1]) if side > 0 else np.nanmin(day.bid[lo:hi + 1]))


def simulate(day: Day, known_at_ns: int, side: int, stop_ticks: float, target_ticks: float,
             exit_at_ns: int, costs: CostModel) -> dict | None:
    t, n, lat = day.t, len(day.t), int(costs.latency_ms * 1_000_000)
    tick = costs.tick
    i0 = _first_at_or_after(t, known_at_ns)
    if i0 >= n:
        return None
    j = _first_at_or_after(t, t[i0] + lat)
    if j >= n:
        return None
    entry = _worse(day, side, max(j - 1, i0), j)
    k = _first_at_or_after(t, t[j] + lat)
    stop_px = entry - side * stop_ticks * tick
    target_px = entry + side * target_ticks * tick
    q = _first_at_or_after(t, max(exit_at_ns, t[j]))               # market exit decided here
    m_arr = _first_at_or_after(t, t[q] + lat) if q < n else n      # ... and filled here
    seg = slice(k, min(m_arr, n - 1) + 1) if q < n else slice(k, n)
    p = day.px[seg]
    if side > 0:
        stop_hit, target_hit = p <= stop_px, p > target_px
    else:
        stop_hit, target_hit = p >= stop_px, p < target_px
    s_idx = np.flatnonzero(stop_hit)
    g_idx = np.flatnonzero(target_hit)
    s_first = s_idx[0] + k if len(s_idx) else None
    g_first = g_idx[0] + k if len(g_idx) else None
    reason = None
    if s_first is not None and (g_first is None or s_first <= g_first):
        jj = min(s_first + 1, n - 1)
        exit_px, exit_i, reason = _worse(day, -side, s_first, jj), jj, "stop"
    elif g_first is not None:
        exit_px, exit_i, reason = target_px, g_first, "target"
    else:
        last = min(m_arr, n - 1)
        exit_px, exit_i, reason = _worse(day, -side, max(last - 1, q if q < n else last), last), last, "time"
    gross = side * (exit_px - entry) * costs.point_value
    fees = costs.fee(1) * 2
    return {"entry_ts": t[j], "exit_ts": t[exit_i], "side": side, "entry_px": entry, "exit_px": exit_px,
            "reason": reason, "gross_pnl": gross, "fees": fees, "net_pnl": gross - fees,
            "ticks": gross / costs.tick_value}
