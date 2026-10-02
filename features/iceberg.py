"""Iceberg detection from annotated MBO (feature 7). Input: features.book.annotate_mbo output.

Native (exchange-held) icebergs keep their order_id when the displayed clip refills
(and go to the back of the queue). Evidence, per order_id:
  * fill_exceeds_display: fills within one event exceed the order's displayed size;
  * refill_after_fill: a same-price modify leaving MORE size than displayed-minus-filled
    (annotate_mbo kind 'refill'), or a size increase after earlier fills.
Synthetic (platform-held) icebergs use a NEW order per clip. Heuristic link: an order
fully removed by fills is followed within `dt` by a new add with the same side,
price and size as the removed order's original clip.

Detections are emitted at the record that reveals them (known_at). Snapshot
records are never treated as adds/refills (annotate_mbo labels them 'snapshot').
Reference: Zotikov & Antonov (2019), CME Iceberg Order Detection and Prediction.
"""
from __future__ import annotations

import bisect

import numpy as np
import pandas as pd

_TRACKED = {"add", "fill", "modify_up", "refill", "cancel", "fill_removal", "partial_fill_cancel",
            "modify_down_fill", "modify_price", "modify_down", "clear"}


def native_icebergs(ann: pd.DataFrame) -> pd.DataFrame:
    """One row per detected native iceberg: known_at, order_id, side, price, evidence, peak_size."""
    cols = ["known_at", "order_id", "side", "price", "evidence", "peak_size"]
    kind = ann["kind"].to_numpy()
    pos = np.flatnonzero(np.isin(kind, list(_TRACKED)))
    ts, oid = ann.index, ann["order_id"].to_numpy(dtype=np.uint64)
    side, price = ann["side"].astype(str).to_numpy(), ann["price"].to_numpy(float)
    size, new = ann["size"].to_numpy(np.int64), ann["new_size"].to_numpy(np.int64)
    exceeds = ann["exceeds_display"].to_numpy(bool)
    state: dict[int, dict] = {}
    out = []
    for i in pos:
        k, o = kind[i], int(oid[i])
        if k == "clear":
            state.clear()
            continue
        if k == "add":
            state[o] = {"peak": int(new[i]), "filled": 0, "detected": False, "price": price[i]}
            continue
        st = state.get(o)
        if st is None:
            continue
        evidence = None
        if k == "fill":
            st["filled"] += int(size[i])
            if exceeds[i]:
                evidence = "fill_exceeds_display"
        elif k == "refill" or (k == "modify_up" and st["filled"] > 0 and price[i] == st["price"]):
            st["peak"] = max(st["peak"], int(new[i]))
            evidence = "refill_after_fill"
        elif k == "modify_price":
            st["price"] = price[i]
        if evidence and not st["detected"]:
            st["detected"] = True
            out.append((ts[i], o, side[i], float(st["price"]), evidence, st["peak"]))
        if k in ("cancel", "fill_removal", "partial_fill_cancel", "modify_down_fill") and new[i] == 0:
            state.pop(o, None)
    return pd.DataFrame(out, columns=cols)


def synthetic_icebergs(ann: pd.DataFrame, dt: str = "5ms", min_clips: int = 3) -> pd.DataFrame:
    """Chains of same-size clips re-added within `dt` after the previous clip filled.

    Returns one row per chain reaching `min_clips`: known_at, side, price, clip_size, clips, order_ids.
    """
    cols = ["known_at", "side", "price", "clip_size", "clips", "order_ids"]
    kind = ann["kind"].to_numpy()
    ts = ann.index
    side, price = ann["side"].astype(str).to_numpy(), ann["price"].to_numpy(float)
    oid = ann["order_id"].to_numpy(dtype=np.uint64)
    new, orig = ann["new_size"].to_numpy(np.int64), ann["orig_size"].to_numpy(np.int64)
    window = pd.Timedelta(dt)

    adds: dict[tuple, list[int]] = {}
    for i in np.flatnonzero(kind == "add"):
        adds.setdefault((side[i], price[i], int(new[i])), []).append(int(i))
    ends = np.flatnonzero(np.isin(kind, ["fill_removal", "modify_down_fill"]) & (new == 0))

    chain_of: dict[int, int] = {}        # order_id -> chain index
    chains: list[dict] = []
    used: set[int] = set()
    out = []
    for e in ends:
        key = (side[e], price[e], int(orig[e]))
        cand = adds.get(key)
        if not cand or orig[e] <= 0:
            continue
        j = bisect.bisect_right(cand, int(e))
        while j < len(cand) and cand[j] in used:
            j += 1
        if j == len(cand) or ts[cand[j]] - ts[e] > window:
            continue
        a = cand[j]
        used.add(a)
        prev_o, next_o = int(oid[e]), int(oid[a])
        c = chain_of.get(prev_o)
        if c is None:
            c = len(chains)
            chains.append({"ids": [prev_o], "reported": False})
            chain_of[prev_o] = c
        chains[c]["ids"].append(next_o)
        chain_of[next_o] = c
        if len(chains[c]["ids"]) >= min_clips and not chains[c]["reported"]:
            chains[c]["reported"] = True
            out.append((ts[a], side[a], float(price[a]), int(new[a]), len(chains[c]["ids"]),
                        list(chains[c]["ids"])))
    return pd.DataFrame(out, columns=cols)
