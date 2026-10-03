"""Load cached DBN chunks into pandas DataFrames.

  * Prices are converted to floats (index points).
  * Index is the record's `ts_recv` (or `ts_event` for OHLCV) in UTC.
  * Optionally converted to parquet next to the DBN file for faster reloads.
  * `load_session()` returns exactly one CME trading session from the
    contract chosen by the roll rule (data.contracts), tagged with
    `trading_date` / `session` and a `contract_segment` column that
    increments if the instrument changes (should never happen within a
    session; a value > 1 indicates a data/roll problem).
  * MBO is different: the book is state. A time slice drops every order that was
    resting before the cut, so `load_session(..., "mbo")` keeps the records from the
    start of the first chunk (Databento's 00:00 UTC snapshot) and marks them
    `warmup=True`. `features.book` replays them and then drops them.
  * Record order is preserved exactly as delivered by Databento.
"""
from __future__ import annotations

import warnings
from datetime import date
from pathlib import Path
from typing import Iterable

import pandas as pd

from . import cache, holdout
from .flags import F_SNAPSHOT
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
    """Concatenate UTC-day chunks of ONE symbol in date order.

    Records are NOT re-sorted: Databento's file order carries CME FIFO
    priority (messages for an instrument are never reordered), and snapshot
    records carry F_BAD_TS_RECV timestamps. Mixing symbols (e.g. ES.c.0 and
    ES.c.1) in one frame is refused to avoid stitching contracts together.
    """
    paths = sorted(Path(p) for p in paths)  # file names are ISO dates -> chronological
    symbols = {p.parent.name for p in paths}
    if len(symbols) > 1:
        raise ValueError(f"load_chunks got several symbols {sorted(symbols)}; load them separately")
    frames = [f for f in (load_chunk(p, use_parquet) for p in paths) if not f.empty]
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames)


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
    """Fetch (cost-checked, cached) and load one trading session (refuses holdout dates)."""
    holdout.check([trading_date], getattr(downloader, "splits_path", holdout.SPLITS_TOML))
    paths = downloader.fetch_sessions(schema, [trading_date], rth_only=rth_only, **fetch_kwargs)
    df = load_chunks(paths)
    if schema == "mbo":
        return with_book_warmup(df, trading_date, rth_only)
    return slice_session(df, trading_date, rth_only)


def load_rth_session(downloader, schema: str, trading_date: date, **kw) -> pd.DataFrame:
    """One RTH session from RTH-window chunks (Downloader.fetch_rth); refuses holdout dates."""
    paths = downloader.fetch_rth(schema, [trading_date], **kw)
    return slice_session(load_chunks(paths), trading_date, rth_only=True)


def with_book_warmup(mbo: pd.DataFrame, trading_date: date, rth_only: bool = False) -> pd.DataFrame:
    """One MBO session plus everything before it back to the opening snapshot.

    Rows before the session start get `warmup=True`; they exist only to rebuild the
    resting book. Measured on 2024-03-05: slicing first lost the whole resting book at
    the RTH open (vault/results/mbo-warmup-2024-03-05.md).
    """
    if mbo.empty:
        return mbo
    start, end = session_bounds(trading_date, rth_only)
    flags = mbo["flags"].to_numpy().astype("int64")
    if not flags[0] & F_SNAPSHOT:
        warnings.warn("MBO data does not start with a snapshot: the replayed book may miss resting orders")
    warm = mbo[mbo.index < start]
    sess = slice_session(mbo, trading_date, rth_only)
    warm = warm.assign(trading_date=pd.NaT, session="warmup").assign(warmup=True)
    sess = sess.assign(warmup=False)
    return pd.concat([warm, sess])
