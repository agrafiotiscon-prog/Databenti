"""Databento MBO -> hftbacktest event array (Phase 3, R3.4: tier-B `l3_fifo` reference).

Why our own converter instead of `hftbacktest.data.utils.databento.convert`:
  * it raises on action 'N' (CME sends ~1,200 per RTH day; they carry no book change), and
  * it loops in Python over every record (10M+ per day).
Semantics are kept identical otherwise: the start-of-day snapshot (records flagged
F_SNAPSHOT after an `R` clear) gets exch_ts = local_ts = the clear's ts_recv, so price-time
priority is preserved without timestamps from the past; then hftbacktest's own
`correct_local_timestamp`, `correct_event_order` and `validate_event_order` are applied.

Input: a raw MBO frame as loaded by `data.loader` (index ts_recv; columns ts_event, action,
side, price, size, order_id, flags), starting at a snapshot (use `with_book_warmup` and
drop the `warmup` column only after conversion if needed - the book must start full).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from data.flags import F_SNAPSHOT


def to_hft_events(mbo: pd.DataFrame, base_latency_ns: int = 0) -> np.ndarray:
    from hftbacktest import (ADD_ORDER_EVENT, BUY_EVENT, CANCEL_ORDER_EVENT, DEPTH_CLEAR_EVENT, FILL_EVENT,
                             MODIFY_ORDER_EVENT, SELL_EVENT, TRADE_EVENT, event_dtype)
    from hftbacktest.data.validation import correct_event_order, correct_local_timestamp, validate_event_order

    m = mbo[mbo["action"].astype(str) != "N"]
    act = m["action"].astype(str).to_numpy()
    codes = {"A": ADD_ORDER_EVENT, "C": CANCEL_ORDER_EVENT, "M": MODIFY_ORDER_EVENT,
             "R": DEPTH_CLEAR_EVENT, "T": TRADE_EVENT, "F": FILL_EVENT}
    unknown = set(np.unique(act)) - set(codes)
    if unknown:
        raise ValueError(f"unexpected MBO actions {sorted(unknown)}")
    ev = np.vectorize(codes.get, otypes=[np.uint64])(act)
    side = m["side"].astype(str).to_numpy()
    ev = ev | np.where(side == "B", BUY_EVENT, np.where(side == "A", SELL_EVENT, 0)).astype(np.uint64)

    local = pd.DatetimeIndex(m.index).as_unit("ns").asi8.astype(np.int64)
    exch = pd.DatetimeIndex(m["ts_event"]).as_unit("ns").asi8.astype(np.int64)
    snap = (m["flags"].to_numpy().astype(np.int64) & F_SNAPSHOT) != 0
    if snap.any():
        # each snapshot block starts with its clear; give the whole block the clear's ts_recv
        block_start = np.where(snap & (act == "R"), local, 0)
        block_ts = np.maximum.accumulate(np.where(snap & (act == "R"), block_start, 0))
        exch = np.where(snap, block_ts, exch)
        local = np.where(snap, block_ts, local)

    out = np.empty(len(m), event_dtype)
    out["ev"], out["exch_ts"], out["local_ts"] = ev, exch, local
    out["px"] = m["price"].to_numpy(float)
    out["qty"] = m["size"].to_numpy(float)
    out["order_id"] = m["order_id"].to_numpy(np.uint64)
    out["ival"], out["fval"] = 0, 0.0
    out = correct_local_timestamp(out, base_latency_ns)
    out = correct_event_order(out, np.argsort(out["exch_ts"], kind="mergesort"),
                              np.argsort(out["local_ts"], kind="mergesort"))
    validate_event_order(out)
    return out


def hft_touch_series(events: np.ndarray, step_ns: int, tick: float = 0.25) -> pd.DataFrame:
    """Replay `events` in hftbacktest (L3 FIFO) and sample best bid/ask every `step_ns` of local time."""
    from hftbacktest import BacktestAsset, HashMapMarketDepthBacktest

    asset = (BacktestAsset().data([events]).linear_asset(1.0).constant_order_latency(0, 0)
             .l3_fifo_queue_model().no_partial_fill_exchange().trading_value_fee_model(0.0, 0.0)
             .tick_size(tick).lot_size(1.0).last_trades_capacity(0))
    hbt = HashMapMarketDepthBacktest([asset])
    t0 = int(events["local_ts"][0])
    rows = []
    while hbt.elapse(step_ns) == 0:
        d = hbt.depth(0)
        rows.append((hbt.current_timestamp, d.best_bid, d.best_ask))
    hbt.close()
    df = pd.DataFrame(rows, columns=["local_ts", "best_bid", "best_ask"])
    df.index = pd.to_datetime(df.pop("local_ts"), utc=True)
    return df[df.index.asi8 > t0]
