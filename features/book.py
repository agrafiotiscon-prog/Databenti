"""MBO order book with Databento/CME semantics, record annotation, heatmaps (feature 5).

Semantics (vault/01-databento/mbo-book-building.md):
  A  add at the BACK of its price level            T/F/N  no book change
  C  reduce size by `size`; remove at 0             R      clear the whole book
  M  unknown id -> add; price change or size INCREASE -> back of queue;
     size decrease -> keep priority
Book state is only consistent right after a record with F_LAST.

`annotate_mbo` replays the book once and labels every record, most importantly
separating TRUE cancels from fill-driven removals (CME removes filled resting
orders with later C/M records in the same event) and tagging snapshot records
(F_SNAPSHOT, e.g. Databento's 00:00 UTC snapshot) so activity features can
exclude them. Rows with `warmup=True` (data.loader.with_book_warmup) are replayed to
rebuild the resting book and then dropped from the output. The fill/cancel split is [inferred] from the docs and must be
reconciled on real data (scripts/verify_data.py).
"""
from __future__ import annotations

import math
from collections import OrderedDict

import numpy as np
import pandas as pd

from data.flags import F_LAST, F_SNAPSHOT

BID, ASK = "B", "A"


class OrderBook:
    """Full-depth FIFO book: per side, price -> OrderedDict(order_id -> size)."""

    def __init__(self):
        self.orders: dict[int, list] = {}            # oid -> [side, price, size]
        self.levels = {BID: {}, ASK: {}}
        self.anomalies = 0                            # unknown ids, duplicate adds, ...

    # ---------------------------------------------------------------- mutations
    def apply(self, action: str, side: str, price: float, size: int, oid: int) -> tuple[int, int]:
        """Apply one record; return (size_before, size_after) of the order (0 if n/a)."""
        if action == "A":
            if oid in self.orders:
                self.anomalies += 1
                self._remove(oid)
            self._insert(oid, side, price, size)
            return 0, size
        if action == "C":
            o = self.orders.get(oid)
            if o is None:
                self.anomalies += 1
                return 0, 0
            before = o[2]
            after = max(before - size, 0)
            if after == 0:
                self._remove(oid)
            else:
                o[2] = after
                self.levels[o[0]][o[1]][oid] = after
            return before, after
        if action == "M":
            o = self.orders.get(oid)
            if o is None:
                self._insert(oid, side, price, size)
                return 0, size
            before = o[2]
            if o[1] != price or size > before:        # loses priority
                self._remove(oid)
                self._insert(oid, side, price, size)
            else:                                     # size decrease keeps priority
                o[2] = size
                self.levels[o[0]][o[1]][oid] = size
            return before, size
        if action == "R":
            self.orders.clear()
            self.levels = {BID: {}, ASK: {}}
        return 0, 0

    def _insert(self, oid, side, price, size):
        self.orders[oid] = [side, price, size]
        self.levels[side].setdefault(price, OrderedDict())[oid] = size

    def _remove(self, oid):
        side, price, _ = self.orders.pop(oid)
        lvl = self.levels[side][price]
        del lvl[oid]
        if not lvl:
            del self.levels[side][price]

    # ---------------------------------------------------------------- queries
    def best_bid(self) -> float:
        return max(self.levels[BID]) if self.levels[BID] else math.nan

    def best_ask(self) -> float:
        return min(self.levels[ASK]) if self.levels[ASK] else math.nan

    def level_size(self, side: str, price: float) -> int:
        return sum(self.levels[side].get(price, {}).values())

    def depth(self, side: str, n: int | None = None) -> list[tuple[float, int, int]]:
        """[(price, total size, order count)] best first."""
        prices = sorted(self.levels[side], reverse=(side == BID))
        if n is not None:
            prices = prices[:n]
        return [(p, sum(self.levels[side][p].values()), len(self.levels[side][p])) for p in prices]

    def queue_ahead(self, oid: int) -> int | None:
        o = self.orders.get(oid)
        if o is None:
            return None
        ahead = 0
        for other, sz in self.levels[o[0]][o[1]].items():
            if other == oid:
                return ahead
            ahead += sz
        return None


def _arrays(mbo: pd.DataFrame):
    return (mbo["action"].astype(str).to_numpy(), mbo["side"].astype(str).to_numpy(),
            mbo["price"].to_numpy(dtype=float), mbo["size"].to_numpy(dtype=np.int64),
            mbo["order_id"].to_numpy(dtype=np.uint64), mbo["flags"].to_numpy(dtype=np.int64))


def annotate_mbo(mbo: pd.DataFrame) -> pd.DataFrame:
    """Replay the book and label each record.

    Added columns:
      event_id      increments after every F_LAST record
      kind          snapshot | clear | add | cancel | fill_removal | partial_fill_cancel |
                    modify_price | modify_price_fill | aggressor_removal | modify_up | modify_down | modify_down_fill | refill |
                    trade | fill | none | unknown_order
      prev_size / new_size   the order's size before / after the record
      orig_size     size the order had when added (for removal rows; the clip size)
      exceeds_display  (fill rows) unexplained fills on the order > its displayed size
      fill_explained   fill quantity this record accounts for (removals/reductions/refills)
      fill_hidden      on the record that takes an order out of the book: fills on it that no
                       size reduction explained = quantity executed beyond the displayed size
                       (native iceberg reserve)
      fill_aggressor   fills of an order modified into the market (aggressor volume, not resting
                       fills): on the F row when it fills away from its resting price (then its
                       old entry is removed as `aggressor_removal` or moved as
                       `modify_price_fill`), else on the modify_price_fill row
      Real data (2024-03-05, vault/results/mbo-fill-reconciliation-2024-03-05.md):
      explained + hidden + aggressor == resting fill volume.
      best_bid / best_ask    touch as of the last COMPLETED event before this record

    Fill accounting: F records do not change the book, so each order keeps an
    "unexplained fill" balance (fills not yet reflected by a size reduction).
      C of q        : balance >= q -> fill_removal; 0 < balance < q -> partial_fill_cancel; else cancel
      M same price  : with balance b, expected size = prev - b;
                      new > expected -> refill (iceberg replenishment), == -> modify_down_fill,
                      <  -> partial_fill_cancel; with no balance: up -> modify_up, else modify_down
    """
    act, side, px, sz, oid, flg = _arrays(mbo)
    n = len(mbo)
    book = OrderBook()
    kind = np.empty(n, dtype=object)
    prev = np.zeros(n, np.int64)
    new = np.zeros(n, np.int64)
    orig = np.zeros(n, np.int64)
    exceeds = np.zeros(n, bool)
    explained = np.zeros(n, np.int64)
    hidden = np.zeros(n, np.int64)
    aggressor = np.zeros(n, np.int64)
    fill_rows: dict[int, list[int]] = {}    # oid -> F rows of the current event (for exceeds_display)
    aggr_event: dict[int, int] = {}         # oid -> event in which it took liquidity as aggressor
    bb = np.full(n, np.nan)
    ba = np.full(n, np.nan)
    event = np.zeros(n, np.int64)
    unexplained: dict[int, int] = {}        # oid -> fills not yet reflected in the book
    orig_size: dict[int, int] = {}
    cur_bb, cur_ba, ev = math.nan, math.nan, 0

    for i in range(n):
        a, s, p, q, o, f = act[i], side[i], px[i], int(sz[i]), int(oid[i]), int(flg[i])
        bb[i], ba[i], event[i] = cur_bb, cur_ba, ev
        if f & F_SNAPSHOT:
            book.apply(a, s, p, q, o)
            if a in ("A", "M"):
                orig_size[o] = q
            kind[i] = "snapshot"
        elif a == "T":
            kind[i] = "trade"
        elif a == "F":
            kind[i] = "fill"
            if o in book.orders and book.orders[o][1] != p:
                # filled at a price other than where it rests: the order was modified into the
                # market and took liquidity (its M or C follows in this event). Aggressor volume.
                aggressor[i] = q
                aggr_event[o] = ev
            elif o in book.orders:
                unexplained[o] = unexplained.get(o, 0) + q
                exceeds[i] = unexplained[o] > book.orders[o][2]
                fill_rows.setdefault(o, []).append(i)
        elif a == "N":
            kind[i] = "none"
        elif a == "R":
            book.apply(a, s, p, q, o)
            unexplained.clear()
            kind[i] = "clear"
        elif a == "A":
            prev[i], new[i] = book.apply(a, s, p, q, o)
            orig_size[o] = q
            unexplained.pop(o, None)
            kind[i] = "add"
        elif a == "C":
            if o not in book.orders:
                kind[i] = "unknown_order"
            else:
                orig[i] = orig_size.get(o, 0)
                prev[i], new[i] = book.apply(a, s, p, q, o)
                bal = unexplained.get(o, 0)
                if aggr_event.get(o) == ev and bal == 0:
                    kind[i] = "aggressor_removal"       # old resting entry of a filled aggressor
                elif bal >= q > 0:
                    kind[i] = "fill_removal"
                    unexplained[o] = bal - q
                    explained[i] = q
                elif bal > 0:
                    kind[i] = "partial_fill_cancel"
                    unexplained[o] = 0
                    explained[i] = bal
                else:
                    kind[i] = "cancel"
        elif a == "M":
            o_state = book.orders.get(o)
            old_price = o_state[1] if o_state is not None else None
            orig[i] = orig_size.get(o, 0)
            prev[i], new[i] = book.apply(a, s, p, q, o)
            bal = unexplained.get(o, 0)
            if o_state is None:
                kind[i] = "add"
                orig_size[o] = q
            elif old_price != p:
                if aggr_event.get(o) == ev and bal == 0:
                    kind[i] = "modify_price_fill"        # aggressor volume already on its F rows
                elif bal > 0:                          # re-priced into the market: aggressor fills
                    kind[i] = "modify_price_fill"
                    aggressor[i] = bal
                    for j in fill_rows.get(o, ()):
                        if event[j] == ev:           # same event: not evidence of hidden size
                            exceeds[j] = False
                else:
                    kind[i] = "modify_price"
                unexplained[o] = 0
            elif bal > 0:
                expected = prev[i] - bal
                kind[i] = ("refill" if new[i] > expected else
                           "modify_down_fill" if new[i] == expected else "partial_fill_cancel")
                unexplained[o] = 0
                explained[i] = bal
            else:
                kind[i] = "modify_up" if new[i] > prev[i] else "modify_down"
        else:
            kind[i] = "none"
        if o not in book.orders:
            left = unexplained.pop(o, 0)
            if left > 0 and a in ("C", "M"):
                hidden[i] = left
        if f & F_LAST:
            cur_bb, cur_ba = book.best_bid(), book.best_ask()
            ev += 1
            fill_rows.clear()
            aggr_event.clear()

    out = mbo.copy()
    out["event_id"], out["kind"], out["prev_size"], out["new_size"] = event, kind, prev, new
    out["orig_size"], out["exceeds_display"], out["best_bid"], out["best_ask"] = orig, exceeds, bb, ba
    out["fill_explained"], out["fill_hidden"], out["fill_aggressor"] = explained, hidden, aggressor
    out.attrs["unexplained_fill_open"] = int(sum(unexplained.values()))
    out.attrs["book_anomalies"] = book.anomalies
    if "warmup" in out.columns:                    # book rebuilt; keep only the session itself
        out = out[~out["warmup"].to_numpy(bool)]
    return out


def mbo_heatmap(mbo: pd.DataFrame, freq: str = "1s", n_levels: int | None = 50) -> pd.DataFrame:
    """Full-depth book (aggregated by price) as of each bucket end, from MBO.

    The state recorded for bucket end e is the book after the last record with
    ts_recv < e (never a later one). If that record did not carry F_LAST (a
    bucket boundary fell inside an event) the row is flagged consistent=False
    instead of peeking ahead to the event's end.
    Returns long frame: known_at, side, price, size, orders, consistent.
    """
    cols = ["known_at", "side", "price", "size", "orders", "consistent"]
    act, side, px, sz, oid, flg = _arrays(mbo)
    ts = mbo.index
    if len(ts) == 0:
        return pd.DataFrame(columns=cols)
    step = pd.Timedelta(freq)
    next_end = ts[0].floor(freq) + step
    book, rows = OrderBook(), []
    seen_last, consistent = False, False
    for i in range(len(ts)):
        if ts[i] >= next_end:                          # close buckets ending at/before this record
            depth = {BID: book.depth(BID, n_levels), ASK: book.depth(ASK, n_levels)} if seen_last else None
            while ts[i] >= next_end:
                if depth is not None:
                    for sd in (BID, ASK):
                        rows += [(next_end, sd, p, size, cnt, consistent) for p, size, cnt in depth[sd]]
                next_end += step
        book.apply(act[i], side[i], px[i], int(sz[i]), int(oid[i]))
        consistent = bool(flg[i] & F_LAST)
        seen_last |= consistent
    out = pd.DataFrame(rows, columns=cols)
    if "warmup" in mbo.columns and (~mbo["warmup"].to_numpy(bool)).any():
        out = out[out["known_at"] > ts[~mbo["warmup"].to_numpy(bool)][0]]
    return out.reset_index(drop=True)


def mbp10_heatmap(mbp10: pd.DataFrame, freq: str = "1s") -> pd.DataFrame:
    """10-level book as of each bucket end from MBP-10 (uses only F_LAST records).

    Buckets with no update carry the previous state forward (the book persists).
    Returns long frame: known_at, side, level, price, size, orders.
    """
    m = mbp10[(mbp10["flags"].astype(np.int64) & F_LAST) != 0]
    if m.empty:
        return pd.DataFrame(columns=["known_at", "side", "level", "price", "size", "orders"])
    last = m.groupby(m.index.floor(freq)).last()
    full_idx = pd.date_range(last.index[0], last.index[-1], freq=freq)
    last = last.reindex(full_idx).ffill()
    known_at = last.index + pd.Timedelta(freq)
    parts = []
    for lvl in range(10):
        for sd, pre in ((BID, "bid"), (ASK, "ask")):
            col = f"{pre}_px_{lvl:02d}"
            if col not in last.columns:
                continue
            parts.append(pd.DataFrame({"known_at": known_at, "side": sd, "level": lvl,
                                       "price": last[col].to_numpy(),
                                       "size": last[f"{pre}_sz_{lvl:02d}"].to_numpy(),
                                       "orders": last[f"{pre}_ct_{lvl:02d}"].to_numpy()}))
    out = pd.concat(parts, ignore_index=True)
    return out.dropna(subset=["price"]).sort_values(["known_at", "side", "level"]).reset_index(drop=True)
