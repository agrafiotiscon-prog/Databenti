"""Large-order / spoof-like behaviour from annotated MBO (feature 8).

A spoof-like event is a LARGE resting order that
  * was added at least `min_dist_ticks` away from its own side's touch
    (bid orders below the best bid, ask orders above the best ask),
  * was TRULY cancelled in full (not removed by fills -- see annotate_mbo),
  * within `max_lifetime` of being added, never traded, and
  * price never came within `near_ticks` of it while it rested.
It is known at the CANCEL time (using it at add time would be lookahead).
This labels behaviour, not intent. Base rate (vault/results/mbo-calibration-2024-03-05-rth.md):
~45% of ALL far adds (1-50 lots) are pulled untouched within 10 s, and >= 50-lot orders are
pulled LESS often (17-27%), so the label is descriptive only (D-018). Orders whose price is modified, that trade,
or that are wiped by a non-snapshot book clear are dropped from tracking.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .common import TICK

COLUMNS = ["known_at", "order_id", "side", "price", "size", "lifetime_s", "dist_at_add_ticks",
           "min_dist_ticks", "mid_move_ticks"]


def spoof_like_events(ann: pd.DataFrame, min_size: int = 50, min_dist_ticks: float = 4,
                      near_ticks: float = 2, max_lifetime: str = "10s", tick: float = TICK) -> pd.DataFrame:
    kind = ann["kind"].to_numpy()
    ts = ann.index
    oid = ann["order_id"].to_numpy(dtype=np.uint64)
    side, price = ann["side"].astype(str).to_numpy(), ann["price"].to_numpy(float)
    new = ann["new_size"].to_numpy(np.int64)
    bb, ba = ann["best_bid"].to_numpy(float), ann["best_ask"].to_numpy(float)
    mid = (bb + ba) / 2
    max_life = pd.Timedelta(max_lifetime)

    relevant = {"add", "cancel", "fill", "fill_removal", "partial_fill_cancel", "modify_down_fill",
                "modify_price", "modify_price_fill", "modify_up", "refill", "clear"}
    live: dict[int, dict] = {}
    out = []
    for i in np.flatnonzero(np.isin(kind, list(relevant))):
        k, o = kind[i], int(oid[i])
        if k == "clear":
            live.clear()
            continue
        if k == "add":
            if new[i] < min_size:
                continue
            dist = (bb[i] - price[i]) / tick if side[i] == "B" else (price[i] - ba[i]) / tick
            if np.isfinite(dist) and dist >= min_dist_ticks:
                live[o] = {"pos": int(i), "size": int(new[i]), "dist": float(dist)}
            continue
        st = live.get(o)
        if st is None:
            continue
        if k in ("fill", "fill_removal", "partial_fill_cancel", "modify_down_fill", "refill", "modify_price",
                 "modify_price_fill"):
            live.pop(o)                                   # traded or moved -> not a clean pull
            continue
        if k == "cancel" and new[i] == 0:
            live.pop(o)
            a = st["pos"]
            lifetime = ts[i] - ts[a]
            if lifetime > max_life:
                continue
            seg = slice(a, i + 1)
            if side[i] == "B":
                min_dist = (np.nanmin(bb[seg]) - price[i]) / tick
            else:
                min_dist = (price[i] - np.nanmax(ba[seg])) / tick
            if min_dist >= near_ticks:
                out.append((ts[i], o, side[i], float(price[i]), st["size"], lifetime.total_seconds(),
                            st["dist"], float(min_dist), float((mid[i] - mid[a]) / tick)))
    return pd.DataFrame(out, columns=COLUMNS)
