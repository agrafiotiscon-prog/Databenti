"""Load cached DBN chunks into pandas DataFrames.

  * Prices are converted to floats (index points).
  * Index is the record's `ts_recv` (or `ts_event` for OHLCV) in UTC.
  * Optionally converted to parquet next to the DBN file for faster reloads.
  * `load_session()` returns exactly one CME trading session, tagged with
    `trading_date` / `session` and a `contract_segment` column that
    increments at contract rolls.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Iterable

import pandas as pd

from . import cache
from .rolls import contract_segments
from .sessions import session_bounds, tag_sessions


def load_chunk(path: Path, use_parquet: bool = True) -> pd.DataFrame:
    pq = cache.parquet_path(path)
    if use_parquet and pq.exists():
        return pd.read_parquet(pq)
    import databento as db

    store = db.DBNStore.from_file(path)
    df = store.to_df(price_type="float", pretty_ts=True, map_symbols=True)
    if use_parquet:
        df.to_parquet(pq)
    return df


def load_chunks(paths: Iterable[Path], use_parquet: bool = True) -> pd.DataFrame:
    frames = [f for f in (load_chunk(p, use_parquet) for p in paths) if not f.empty]
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames).sort_index(kind="stable")
    return df


def slice_session(df: pd.DataFrame, trading_date: date, rth_only: bool = False) -> pd.DataFrame:
    """Cut a combined frame down to one trading session and add session tags."""
    if df.empty:
        return df
    start, end = session_bounds(trading_date, rth_only)
    out = df[(df.index >= start) & (df.index < end)].copy()
    tags = tag_sessions(out.index)
    out["trading_date"] = tags["trading_date"].values
    out["session"] = tags["session"].values
    if "instrument_id" in out.columns:
        out["contract_segment"] = contract_segments(out).values
    return out


def load_session(downloader, schema: str, trading_date: date, rth_only: bool = False,
                 **fetch_kwargs) -> pd.DataFrame:
    """Fetch (cost-checked, cached) and load one trading session."""
    paths = downloader.fetch_sessions(schema, [trading_date], rth_only=rth_only, **fetch_kwargs)
    return slice_session(load_chunks(paths), trading_date, rth_only)
