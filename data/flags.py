"""Databento record flags (bit field) and helpers.

Always test bits with `&`, never with equality (a record can carry several
flags at once). See vault/01-databento/schemas-and-fields.md.
"""
from __future__ import annotations

import pandas as pd

F_LAST = 1 << 7            # last record of an event for this instrument_id
F_TOB = 1 << 6             # top-of-book message (not used in GLBX MBO)
F_SNAPSHOT = 1 << 5        # synthetic/replayed snapshot record (e.g. 00:00 UTC MBO snapshot)
F_MBP = 1 << 4             # aggregated price-level message
F_BAD_TS_RECV = 1 << 3     # ts_recv inaccurate
F_MAYBE_BAD_BOOK = 1 << 2  # unrecoverable gap: book state suspect until next clear/snapshot


def has_flag(flags: pd.Series, flag: int) -> pd.Series:
    return (flags.astype("int64") & flag) != 0


def drop_snapshot(df: pd.DataFrame) -> pd.DataFrame:
    """Remove snapshot records -- required before counting adds/cancels/order sizes."""
    return df[~has_flag(df["flags"], F_SNAPSHOT).values]


def event_end_mask(df: pd.DataFrame) -> pd.Series:
    """Rows after which the book is in a consistent state (F_LAST set)."""
    return has_flag(df["flags"], F_LAST)
