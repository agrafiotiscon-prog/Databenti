"""CME Globex session handling for equity index futures (ES/NQ).

All session logic is done in US/Central (America/Chicago), which handles
DST automatically.

Globex schedule (equity index futures):
  * Trading:     Sun-Fri 17:00 CT  ->  next day 16:00 CT
  * Maintenance: 16:00-17:00 CT daily (no trading)
  * RTH:         08:30-15:00 CT   (cash equity session; futures settle ~15:00 CT)
  * ETH:         everything else inside the Globex session

Trading-date convention: a timestamp at/after 17:00 CT belongs to the NEXT
trading date (Sunday evening -> Monday, Friday evening never trades).

Known limitations (documented in README): exchange holidays and early-close
days (e.g. 12:00 CT close) are not modelled from a calendar -- they simply
show up as missing/short sessions in the data.
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import pandas as pd

CT = ZoneInfo("America/Chicago")
UTC = ZoneInfo("UTC")

GLOBEX_OPEN = time(17, 0)
GLOBEX_CLOSE = time(16, 0)
RTH_OPEN = time(8, 30)
RTH_CLOSE = time(15, 0)


def session_bounds(trading_date: date, rth_only: bool = False) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Return [start, end) UTC timestamps for a trading date's session."""
    if rth_only:
        start = datetime.combine(trading_date, RTH_OPEN, tzinfo=CT)
        end = datetime.combine(trading_date, RTH_CLOSE, tzinfo=CT)
    else:
        # Session opens at 17:00 CT the previous calendar day
        # (Monday's session opens Sunday evening).
        prev = trading_date - timedelta(days=1)
        start = datetime.combine(prev, GLOBEX_OPEN, tzinfo=CT)
        end = datetime.combine(trading_date, GLOBEX_CLOSE, tzinfo=CT)
    return pd.Timestamp(start).tz_convert(UTC), pd.Timestamp(end).tz_convert(UTC)


def utc_days_for_session(trading_date: date, rth_only: bool = False) -> list[date]:
    """UTC calendar days that must be cached to cover a trading session."""
    start, end = session_bounds(trading_date, rth_only)
    last = (end - pd.Timedelta(nanoseconds=1)).date()
    days, d = [], start.date()
    while d <= last:
        days.append(d)
        d += timedelta(days=1)
    return days


def trading_dates(start: date, end: date) -> list[date]:
    """Weekdays in [start, end] (holidays are not removed; see module docs)."""
    out, d = [], start
    while d <= end:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


def tag_sessions(index: pd.DatetimeIndex) -> pd.DataFrame:
    """Vectorised session tags for a UTC (or tz-aware) DatetimeIndex.

    Returns columns:
      ts_ct         -- timestamp in US/Central
      trading_date  -- date the record belongs to (17:00 CT rollover)
      session       -- 'RTH', 'ETH' or 'CLOSED' (maintenance break / weekend)
    """
    if index.tz is None:
        index = index.tz_localize(UTC)
    ct = index.tz_convert(CT)
    minutes = ct.hour * 60 + ct.minute
    after_open = minutes >= GLOBEX_OPEN.hour * 60
    in_break = (minutes >= GLOBEX_CLOSE.hour * 60) & ~after_open
    rth = (minutes >= RTH_OPEN.hour * 60 + RTH_OPEN.minute) & (minutes < RTH_CLOSE.hour * 60)

    local_date = ct.normalize().tz_localize(None)
    tdate = local_date + pd.to_timedelta(after_open.astype(int), unit="D")
    # Saturday (from Fri evening) never trades; Sunday-evening rolls into Monday.
    weekday = ct.weekday
    weekend_closed = (weekday == 5) | ((weekday == 4) & after_open) | ((weekday == 6) & ~after_open)

    session = pd.Series("ETH", index=index)
    session[rth] = "RTH"
    session[in_break | weekend_closed] = "CLOSED"

    return pd.DataFrame(
        {"ts_ct": ct, "trading_date": tdate.date, "session": session.values},
        index=index,
    )


def filter_session(df: pd.DataFrame, which: str = "RTH") -> pd.DataFrame:
    """Keep only rows in the given session ('RTH', 'ETH' or 'ALL' = RTH+ETH)."""
    tags = tag_sessions(df.index)
    if which == "ALL":
        mask = tags["session"] != "CLOSED"
    else:
        mask = tags["session"] == which
    return df[mask.values]
