"""Level-1 event-driven backtester (Phase 3, R3.1: market orders).

Design: vault/04-backtesting/fill-and-latency-models.md.

  * Records (e.g. TBBO: each trade with the best bid/ask just before it) are replayed in
    file order. The strategy callback gets ONE record at a time plus a context; it never
    receives the frame, so it cannot see the future.
  * An order submitted while handling record i (time t_i) arrives at t_i + latency.
    Nothing is filled before arrival.
  * Market orders fill against the book AT ARRIVAL. L1 trade data only shows the book just
    before each trade, so the book at arrival lies between the last record before arrival
    and the first record at/after it; we take the WORSE of the two (buy: higher ask, sell:
    lower bid). Conservative by construction.
  * Fees per contract per side from config/costs.toml (x fee_multiplier for stress).
  * Position limit (default 1 contract): orders that would exceed it are rejected and logged.
  * Open position at the end is flattened at the worse side of the last book (flagged).
No market impact, no reaction of others to our orders (stated in every report).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np
import pandas as pd

from .costs import CostModel

L1_COLUMNS = ["bid_px", "ask_px", "bid_sz", "ask_sz"]


def l1_from_tbbo(tbbo: pd.DataFrame) -> pd.DataFrame:
    """Databento TBBO frame -> engine input (index ts_recv, file order kept)."""
    out = tbbo.rename(columns={"bid_px_00": "bid_px", "ask_px_00": "ask_px",
                               "bid_sz_00": "bid_sz", "ask_sz_00": "ask_sz"})
    keep = L1_COLUMNS + [c for c in ("price", "size", "side") if c in out.columns]
    return out[keep]


@dataclass
class Order:
    side: int                 # +1 buy, -1 sell
    qty: int
    submit_ts: pd.Timestamp
    arrival_ts: pd.Timestamp
    submit_pos: int
    tag: str = ""


@dataclass
class Context:
    """What the strategy may use: its own state and order entry. No market data beyond the record."""
    position: int = 0
    max_position: int = 1
    pending: list[Order] = field(default_factory=list)
    rejected: list[dict] = field(default_factory=list)
    _now: pd.Timestamp | None = None
    _pos: int = -1
    _latency: pd.Timedelta = pd.Timedelta(0)

    def exposure_if_filled(self) -> int:
        return self.position + sum(o.side * o.qty for o in self.pending)

    def market(self, side: int, qty: int = 1, tag: str = "") -> Order | None:
        if side not in (1, -1) or qty <= 0:
            raise ValueError("side must be +1/-1 and qty > 0")
        if abs(self.exposure_if_filled() + side * qty) > self.max_position:
            self.rejected.append({"ts": self._now, "side": side, "qty": qty, "reason": "position_limit", "tag": tag})
            return None
        o = Order(side, qty, self._now, self._now + self._latency, self._pos, tag)
        self.pending.append(o)
        return o


Strategy = Callable[[pd.Timestamp, object, Context], None]


@dataclass
class Result:
    fills: pd.DataFrame
    trades: pd.DataFrame
    rejected: pd.DataFrame
    costs: CostModel

    @property
    def net_pnl(self) -> float:
        return float(self.trades["net_pnl"].sum()) if len(self.trades) else 0.0


def run(l1: pd.DataFrame, strategy: Strategy, costs: CostModel, max_position: int = 1) -> Result:
    if not set(L1_COLUMNS) <= set(l1.columns):
        raise ValueError(f"l1 needs columns {L1_COLUMNS}")
    ts = pd.DatetimeIndex(l1.index).as_unit("ns")   # asi8 must be ns to compare with Timestamp.value
    t_ns = ts.asi8
    bid, ask = l1["bid_px"].to_numpy(float), l1["ask_px"].to_numpy(float)
    ctx = Context(max_position=max_position, _latency=pd.Timedelta(milliseconds=costs.latency_ms))
    fills: list[dict] = []
    rows = l1.itertuples(index=False)

    def fill(o: Order, j: int, end: bool = False) -> None:
        # book at arrival: between record j-1 (last before arrival) and j (first at/after)
        lo = max(j - 1, o.submit_pos)
        if o.side > 0:
            px = np.nanmax(ask[lo:j + 1])
        else:
            px = np.nanmin(bid[lo:j + 1])
        ctx.position += o.side * o.qty
        fills.append({"submit_ts": o.submit_ts, "arrival_ts": o.arrival_ts, "fill_ts": ts[j],
                      "side": o.side, "qty": o.qty, "price": float(px), "fee": costs.fee(o.qty),
                      "tag": o.tag, "end_flatten": end})

    for i, rec in enumerate(rows):
        if ctx.pending:                                   # orders that have arrived by now
            due = [o for o in ctx.pending if o.arrival_ts.value <= t_ns[i]]
            for o in due:
                ctx.pending.remove(o)
                fill(o, i)
        ctx._now, ctx._pos = ts[i], i
        strategy(ts[i], rec, ctx)

    ctx.pending.clear()                                   # never arrived before the data ended
    if ctx.position != 0 and len(ts):
        o = Order(-int(np.sign(ctx.position)), abs(ctx.position), ts[-1], ts[-1], len(ts) - 1, "end_flatten")
        fill(o, len(ts) - 1, end=True)
    f = pd.DataFrame(fills, columns=["submit_ts", "arrival_ts", "fill_ts", "side", "qty", "price", "fee",
                                     "tag", "end_flatten"])
    return Result(f, round_trips(f, costs), pd.DataFrame(ctx.rejected), costs)


def round_trips(fills: pd.DataFrame, costs: CostModel) -> pd.DataFrame:
    """Pair fills into flat-to-flat trades (volume-weighted entry and exit prices)."""
    cols = ["entry_ts", "exit_ts", "side", "qty", "entry_px", "exit_px", "gross_pnl", "fees", "net_pnl", "ticks"]
    out, pos, cur = [], 0, None
    for r in fills.itertuples(index=False):
        if pos == 0:
            cur = {"entry_ts": r.fill_ts, "side": r.side, "in_q": 0, "in_v": 0.0, "out_q": 0, "out_v": 0.0,
                   "cash": 0.0, "fees": 0.0}
        if r.side == cur["side"]:
            cur["in_q"] += r.qty; cur["in_v"] += r.qty * r.price
        else:
            cur["out_q"] += r.qty; cur["out_v"] += r.qty * r.price
        cur["cash"] -= r.side * r.qty * r.price
        cur["fees"] += r.fee
        pos += r.side * r.qty
        if pos == 0:
            gross = cur["cash"] * costs.point_value
            q = cur["in_q"]
            out.append((cur["entry_ts"], r.fill_ts, cur["side"], q, cur["in_v"] / q, cur["out_v"] / cur["out_q"],
                        gross, cur["fees"], gross - cur["fees"], gross / costs.tick_value / q))
    return pd.DataFrame(out, columns=cols)
