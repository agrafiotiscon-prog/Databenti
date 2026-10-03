"""Level-1 event-driven backtester (Phase 3: R3.1 market orders, R3.2 limit/stop/cancel).

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
  * Limit orders: marketable on arrival -> taker fill at the worse book (if within the limit);
    otherwise resting, filled by `trade_through` (a trade strictly through our price, default)
    or `queue_l1` (queue ahead = displayed size at our price when it is/becomes the touch,
    reduced only by trades at our price; cancels ahead are ignored = conservative).
  * Stops trigger on a trade at/through the stop, then fill like a market order at the worse
    of the triggering record's book and the next one.
  * Cancels take effect at their arrival (now + latency); an order can fill meanwhile.
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


def l1_from_trades(trades: pd.DataFrame, tick: float = 0.25) -> pd.DataFrame:
    """Trades-only input (D-019): rebuild the pre-trade bid/ask from aggressor prints.

    side 'B' = buyer-initiated (prints at the ask 99.4% of the time on 2024-03-05), 'A' = seller.
    ask = last buy-print price, bid = last sell-print price, both from trades BEFORE this one;
    a crossed or locked estimate is fixed one tick away from the most recent print. On 2024-03-05
    RTH this equals TBBO's pre-trade quote 81% of the time, otherwise +-1 tick (mean +0.017 ticks).
    Sizes are unknown (set to 0) - queue_l1 needs real quotes, so use trade_through with this input.
    """
    px = trades["price"].to_numpy(float)
    sd = trades["side"].astype(str).to_numpy()
    ask = pd.Series(np.where(sd == "B", px, np.nan)).ffill().shift(1).to_numpy()
    bid = pd.Series(np.where(sd == "A", px, np.nan)).ffill().shift(1).to_numpy()
    last_side = pd.Series(sd).shift(1).to_numpy()
    bad = ~(ask > bid)
    ask = np.where(bad & (last_side == "A"), bid + tick, ask)
    bid = np.where(bad & (last_side == "B"), ask - tick, bid)
    return pd.DataFrame({"bid_px": bid, "ask_px": ask, "bid_sz": 0.0, "ask_sz": 0.0,
                         "price": px, "size": trades["size"].to_numpy(float), "side": sd}, index=trades.index)


@dataclass
class Order:
    side: int                 # +1 buy, -1 sell
    qty: int
    submit_ts: pd.Timestamp
    arrival_ts: pd.Timestamp
    submit_pos: int
    tag: str = ""
    kind: str = "market"      # market | limit | stop
    price: float = np.nan     # limit or stop price
    status: str = "pending"   # pending (in flight) | working (at the exchange) | filled | cancelled
    queue_ahead: float | None = None    # queue_l1: contracts ahead of us; None = unknown (behind the touch)
    cancel_arrival_ts: pd.Timestamp | None = None


@dataclass
class Context:
    """What the strategy may use: its own state and order entry. No market data beyond the record."""
    position: int = 0
    max_position: int = 1
    pending: list[Order] = field(default_factory=list)   # every active order (in flight or working)
    rejected: list[dict] = field(default_factory=list)
    _now: pd.Timestamp | None = None
    _pos: int = -1
    _latency: pd.Timedelta = pd.Timedelta(0)

    def exposure_if_filled(self) -> int:
        """Worst case: every active order on the same side as the position fills."""
        longs = sum(o.qty for o in self.pending if o.side > 0)
        shorts = sum(o.qty for o in self.pending if o.side < 0)
        return max(abs(self.position + longs), abs(self.position - shorts))

    def _submit(self, side: int, qty: int, kind: str, price: float, tag: str) -> Order | None:
        if side not in (1, -1) or qty <= 0:
            raise ValueError("side must be +1/-1 and qty > 0")
        if kind != "market" and not np.isfinite(price):
            raise ValueError(f"{kind} order needs a price")
        trial = Order(side, qty, self._now, self._now + self._latency, self._pos, tag, kind, float(price))
        self.pending.append(trial)
        if self.exposure_if_filled() > self.max_position:
            self.pending.remove(trial)
            self.rejected.append({"ts": self._now, "side": side, "qty": qty, "reason": "position_limit",
                                  "tag": tag, "kind": kind})
            return None
        return trial

    def market(self, side: int, qty: int = 1, tag: str = "") -> Order | None:
        return self._submit(side, qty, "market", np.nan, tag)

    def limit(self, side: int, price: float, qty: int = 1, tag: str = "") -> Order | None:
        return self._submit(side, qty, "limit", price, tag)

    def stop(self, side: int, price: float, qty: int = 1, tag: str = "") -> Order | None:
        return self._submit(side, qty, "stop", price, tag)

    def cancel(self, order: Order) -> None:
        """Takes effect when the cancel ARRIVES (now + latency); the order can fill meanwhile."""
        if order in self.pending and order.cancel_arrival_ts is None:
            order.cancel_arrival_ts = self._now + self._latency


Strategy = Callable[[pd.Timestamp, object, Context], None]


@dataclass
class Result:
    fills: pd.DataFrame
    trades: pd.DataFrame
    rejected: pd.DataFrame
    costs: CostModel
    cancelled: int = 0

    @property
    def net_pnl(self) -> float:
        return float(self.trades["net_pnl"].sum()) if len(self.trades) else 0.0


FILL_MODES = ("trade_through", "queue_l1")


def run(l1: pd.DataFrame, strategy: Strategy, costs: CostModel, max_position: int = 1,
        fill_mode: str = "trade_through") -> Result:
    """fill_mode applies to resting limit orders: trade_through (pessimistic default) or queue_l1."""
    if not set(L1_COLUMNS) <= set(l1.columns):
        raise ValueError(f"l1 needs columns {L1_COLUMNS}")
    if fill_mode not in FILL_MODES:
        raise ValueError(f"fill_mode must be one of {FILL_MODES} (optimistic touch fills are not offered)")
    ts = pd.DatetimeIndex(l1.index).as_unit("ns")   # asi8 must be ns to compare with Timestamp.value
    t_ns = ts.asi8
    bid, ask = l1["bid_px"].to_numpy(float), l1["ask_px"].to_numpy(float)
    bsz, asz = l1["bid_sz"].to_numpy(float), l1["ask_sz"].to_numpy(float)
    has_trades = {"price", "size"} <= set(l1.columns)
    tpx = l1["price"].to_numpy(float) if has_trades else np.full(len(l1), np.nan)
    tsz = l1["size"].to_numpy(float) if has_trades else np.zeros(len(l1))
    ctx = Context(max_position=max_position, _latency=pd.Timedelta(milliseconds=costs.latency_ms))
    fills: list[dict] = []
    n_cancelled = 0
    rows = l1.itertuples(index=False)

    def book_px(side: int, lo: int, j: int) -> float:
        """Worse side of the books in records lo..j (the book in between is unknown)."""
        return float(np.nanmax(ask[lo:j + 1]) if side > 0 else np.nanmin(bid[lo:j + 1]))

    def do_fill(o: Order, j: int, px: float, liquidity: str, end: bool = False) -> None:
        o.status = "filled"
        if o in ctx.pending:
            ctx.pending.remove(o)
        ctx.position += o.side * o.qty
        fills.append({"submit_ts": o.submit_ts, "arrival_ts": o.arrival_ts, "fill_ts": ts[j],
                      "side": o.side, "qty": o.qty, "price": float(px), "fee": costs.fee(o.qty),
                      "tag": o.tag, "end_flatten": end, "kind": o.kind, "liquidity": liquidity})

    def queue_at(o: Order, j: int) -> float | None:
        touch, size = (bid[j], bsz[j]) if o.side > 0 else (ask[j], asz[j])
        better = o.price > touch if o.side > 0 else o.price < touch
        if better:
            return 0.0                    # inside the spread: nobody ahead of us
        return float(size) if o.price == touch else None

    def arrive(o: Order, i: int) -> None:
        lo = max(i - 1, o.submit_pos)
        if o.kind == "market":
            do_fill(o, i, book_px(o.side, lo, i), "taker")
            return
        o.status = "working"
        if o.kind == "limit":
            px = book_px(o.side, lo, i)
            if (o.side > 0 and px <= o.price) or (o.side < 0 and px >= o.price):
                do_fill(o, i, px, "taker")                # marketable on arrival
            elif fill_mode == "queue_l1":
                o.queue_ahead = queue_at(o, i)

    def on_trade(o: Order, i: int) -> None:
        p, q = tpx[i], tsz[i]
        if not np.isfinite(p):
            return
        if o.kind == "stop":
            if (o.side > 0 and p >= o.price) or (o.side < 0 and p <= o.price):
                j = min(i + 1, len(ts) - 1)              # becomes a market order after the trigger
                do_fill(o, j, book_px(o.side, i, j), "taker")
            return
        through = p < o.price if o.side > 0 else p > o.price
        if through:
            do_fill(o, i, o.price, "maker")
        elif fill_mode == "queue_l1" and p == o.price:
            if o.queue_ahead is None:
                o.queue_ahead = queue_at(o, i)
            if o.queue_ahead is not None:
                o.queue_ahead -= q
                if o.queue_ahead < 0:
                    do_fill(o, i, o.price, "maker")
        elif fill_mode == "queue_l1" and o.queue_ahead is None:
            o.queue_ahead = queue_at(o, i)              # our level became the touch: join behind it

    for i, rec in enumerate(rows):
        now = t_ns[i]
        for o in list(ctx.pending):                       # 1. cancels that have arrived
            # strict <: a cancel arriving at the same instant as a trade loses (conservative)
            if o.cancel_arrival_ts is not None and o.cancel_arrival_ts.value < now:
                o.status = "cancelled"
                ctx.pending.remove(o)
                n_cancelled += 1
        for o in [o for o in ctx.pending if o.status == "pending" and o.arrival_ts.value <= now]:
            arrive(o, i)                                  # 2. orders arriving by now
        if has_trades:
            for o in [o for o in ctx.pending if o.status == "working"]:
                on_trade(o, i)                            # 3. this record's trade vs resting orders
        ctx._now, ctx._pos = ts[i], i
        strategy(ts[i], rec, ctx)                         # 4. strategy sees this record only

    ctx.pending.clear()                                   # never arrived / still resting at the end
    if ctx.position != 0 and len(ts):
        o = Order(-int(np.sign(ctx.position)), abs(ctx.position), ts[-1], ts[-1], len(ts) - 1, "end_flatten")
        do_fill(o, len(ts) - 1, book_px(o.side, len(ts) - 1, len(ts) - 1), "taker", end=True)
    f = pd.DataFrame(fills, columns=["submit_ts", "arrival_ts", "fill_ts", "side", "qty", "price", "fee",
                                     "tag", "end_flatten", "kind", "liquidity"])
    return Result(f, round_trips(f, costs), pd.DataFrame(ctx.rejected), costs, n_cancelled)


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
