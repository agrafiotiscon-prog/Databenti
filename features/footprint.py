"""Footprint, delta, cumulative delta, delta divergence (features 1-2).

Side convention (Databento trades/tbbo): side 'B' = buyer aggressor (lifted
the ask) -> ask_vol; side 'A' = seller aggressor (hit the bid) -> bid_vol;
side 'N' (auction uncross, implied) -> unk_vol, never assigned to a side.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .common import BUY_AGGRESSOR, SELL_AGGRESSOR, TICK, bar_start, clean_trades


def footprint(trades: pd.DataFrame, freq: str = "1min", tick: float = TICK) -> pd.DataFrame:
    """Volume per (bar, price) split by aggressor.

    Returns long frame: bar_start, price, ask_vol, bid_vol, unk_vol, n_trades, known_at.
    """
    t = clean_trades(trades, tick)
    t["bar_start"] = bar_start(t.index, freq)
    t["ask_vol"] = np.where(t["side"] == BUY_AGGRESSOR, t["size"], 0)
    t["bid_vol"] = np.where(t["side"] == SELL_AGGRESSOR, t["size"], 0)
    t["unk_vol"] = np.where(~t["side"].isin([BUY_AGGRESSOR, SELL_AGGRESSOR]), t["size"], 0)
    fp = (t.groupby(["bar_start", "price"], sort=True)
            .agg(ask_vol=("ask_vol", "sum"), bid_vol=("bid_vol", "sum"),
                 unk_vol=("unk_vol", "sum"), n_trades=("size", "size"))
            .reset_index())
    fp["known_at"] = fp["bar_start"] + pd.Timedelta(freq)
    return fp


def bar_delta(fp: pd.DataFrame) -> pd.DataFrame:
    """Per-bar delta and session cumulative delta from a footprint.

    The input should be one session of one contract (cum_delta resets per call).
    """
    b = fp.groupby("bar_start").agg(ask_vol=("ask_vol", "sum"), bid_vol=("bid_vol", "sum"),
                                    unk_vol=("unk_vol", "sum"), known_at=("known_at", "first"))
    b["delta"] = b["ask_vol"] - b["bid_vol"]
    b["volume"] = b["ask_vol"] + b["bid_vol"] + b["unk_vol"]
    b["cum_delta"] = b["delta"].cumsum()
    return b


def trade_cum_delta(trades: pd.DataFrame) -> pd.DataFrame:
    """Tick-resolution cumulative delta; known_at = the trade's ts_recv."""
    t = clean_trades(trades)
    signed = np.where(t["side"] == BUY_AGGRESSOR, t["size"],
                      np.where(t["side"] == SELL_AGGRESSOR, -t["size"], 0))
    out = pd.DataFrame({"price": t["price"], "cum_delta": np.cumsum(signed)}, index=t.index)
    out["known_at"] = out.index
    return out


def delta_divergence(bars: pd.DataFrame, lookback: int = 10) -> pd.DataFrame:
    """Price/cum-delta divergence on COMPLETED bars.

    bars needs columns high, low, cum_delta, known_at (e.g. ohlcv_bars joined with bar_delta).
      bearish: high > max(high of previous `lookback` bars) and cum_delta <= max(previous cum_delta)
      bullish: low  < min(low  of previous `lookback` bars) and cum_delta >= min(previous cum_delta)
    Uses only bars up to and including the current one -> known at the current bar's end.
    """
    prev_high = bars["high"].shift(1).rolling(lookback, min_periods=lookback).max()
    prev_low = bars["low"].shift(1).rolling(lookback, min_periods=lookback).min()
    prev_cd_max = bars["cum_delta"].shift(1).rolling(lookback, min_periods=lookback).max()
    prev_cd_min = bars["cum_delta"].shift(1).rolling(lookback, min_periods=lookback).min()
    out = pd.DataFrame(index=bars.index)
    out["bearish_div"] = (bars["high"] > prev_high) & (bars["cum_delta"] <= prev_cd_max)
    out["bullish_div"] = (bars["low"] < prev_low) & (bars["cum_delta"] >= prev_cd_min)
    out["known_at"] = bars["known_at"]
    return out
