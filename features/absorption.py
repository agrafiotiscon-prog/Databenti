"""Absorption (feature 6) -- a falsifiable, causal definition.

Sell absorption at bid level L, evaluated at each sell-aggressor print at L (time t):
  * aggressive SELL volume printed at L within (t - window, t] >= min_vol, and
  * no trade printed BELOW L within (t - window, t]  (price failed to go through), and
  * (optional, tbbo input) the print hit the bid: bid_px_00 == L.
Buy absorption at ask L is the mirror image (buy-aggressor volume, nothing above L).

Rolling windows end at the current row (positionally), so a row never sees
later rows -- even ones sharing its timestamp.

The event is known at t (the print that completes the condition). What price
does AFTER t is the research label, never part of the feature.
An episode at (side, L) fires once and re-arms only after a trade prints
through L (below it for sell absorption, above it for buy absorption) or after
`rearm` time has passed since the last firing.

An MBO refinement (passive fills at L exceeding displayed size -> replenishment)
comes from features.book.annotate_mbo and is kept separate on purpose.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .common import BUY_AGGRESSOR, SELL_AGGRESSOR, TICK, clean_trades

COLUMNS = ["known_at", "side", "level", "vol_at_level"]


def absorption_events(trades: pd.DataFrame, window: str = "30s", min_vol: int = 200,
                      rearm: str = "5min", tick: float = TICK) -> pd.DataFrame:
    """Return events with columns known_at, side ('sell_absorbed'/'buy_absorbed'), level, vol_at_level."""
    t = clean_trades(trades, tick)
    if t.empty:
        return pd.DataFrame(columns=COLUMNS)
    prices = t["price"].to_numpy()
    roll_min = t["price"].rolling(window).min().to_numpy()
    roll_max = t["price"].rolling(window).max().to_numpy()
    touch = None
    if "bid_px_00" in trades.columns:
        touch = {SELL_AGGRESSOR: np.round(trades["bid_px_00"].to_numpy(float) / tick) * tick,
                 BUY_AGGRESSOR: np.round(trades["ask_px_00"].to_numpy(float) / tick) * tick}

    events: list[dict] = []
    for side, kind, extreme in ((SELL_AGGRESSOR, "sell_absorbed", roll_min),
                                (BUY_AGGRESSOR, "buy_absorbed", roll_max)):
        pos = np.flatnonzero(t["side"].to_numpy() == side)
        if pos.size == 0:
            continue
        s = t.iloc[pos]
        vol_at = np.empty(len(s))
        for _, idx in s.groupby("price").indices.items():      # idx: positions within s
            vol_at[idx] = s["size"].iloc[idx].rolling(window).sum().to_numpy()
        held = extreme[pos] == prices[pos]                      # nothing printed through L
        if touch is not None:
            held &= touch[side][pos] == prices[pos]
        hit = np.flatnonzero(held & (vol_at >= min_vol))
        events += _dedupe(t.index, prices, pos[hit], vol_at[hit], kind, side, pd.Timedelta(rearm))
    if not events:
        return pd.DataFrame(columns=COLUMNS)
    return pd.DataFrame(events, columns=COLUMNS).sort_values("known_at", kind="stable").reset_index(drop=True)


def _dedupe(index, prices, cand_pos, cand_vol, kind, side, rearm) -> list[dict]:
    out, last = [], {}
    for p, vol in zip(cand_pos, cand_vol):
        L, ts = prices[p], index[p]
        if L in last:
            prev_p = last[L]
            between = prices[prev_p + 1: p + 1]
            through = (between < L).any() if side == SELL_AGGRESSOR else (between > L).any()
            if not through and ts - index[prev_p] < rearm:
                continue
        last[L] = p
        out.append({"known_at": ts, "side": kind, "level": float(L), "vol_at_level": int(vol)})
    return out
