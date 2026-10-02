from datetime import date

import pandas as pd

from data.loader import slice_session
from data.sessions import session_bounds, tag_sessions, trading_dates


def ts(s):
    return pd.Timestamp(s, tz="America/Chicago").tz_convert("UTC")


def test_rth_bounds_winter_and_summer():
    # CST (UTC-6) in January, CDT (UTC-5) in July
    s, e = session_bounds(date(2024, 1, 10), rth_only=True)
    assert s == pd.Timestamp("2024-01-10 14:30", tz="UTC")
    assert e == pd.Timestamp("2024-01-10 21:00", tz="UTC")
    s, e = session_bounds(date(2024, 7, 10), rth_only=True)
    assert s == pd.Timestamp("2024-07-10 13:30", tz="UTC")


def test_monday_session_opens_sunday_evening():
    s, e = session_bounds(date(2024, 3, 4))  # Monday
    assert s == ts("2024-03-03 17:00")
    assert e == ts("2024-03-04 16:00")


def test_dst_transition_week():
    # US DST started Sun 2024-03-10. Monday's session opens Sunday 17:00 CDT = 22:00 UTC.
    s, _ = session_bounds(date(2024, 3, 11))
    assert s == pd.Timestamp("2024-03-10 22:00", tz="UTC")


def test_tags():
    idx = pd.DatetimeIndex([
        ts("2024-03-05 08:29:59"),  # ETH
        ts("2024-03-05 08:30:00"),  # RTH open
        ts("2024-03-05 14:59:59"),  # RTH
        ts("2024-03-05 15:00:00"),  # ETH (post-close)
        ts("2024-03-05 16:30:00"),  # maintenance break
        ts("2024-03-05 17:00:00"),  # ETH, next trading date
        ts("2024-03-08 17:30:00"),  # Friday evening: closed
        ts("2024-03-09 12:00:00"),  # Saturday: closed
        ts("2024-03-10 18:00:00"),  # Sunday evening: Monday's ETH
    ])
    t = tag_sessions(idx)
    assert list(t["session"]) == ["ETH", "RTH", "RTH", "ETH", "CLOSED", "ETH", "CLOSED", "CLOSED", "ETH"]
    assert t["trading_date"].iloc[0] == date(2024, 3, 5)
    assert t["trading_date"].iloc[5] == date(2024, 3, 6)
    assert t["trading_date"].iloc[8] == date(2024, 3, 11)


def test_trading_dates_skip_weekends():
    assert trading_dates(date(2024, 3, 8), date(2024, 3, 11)) == [date(2024, 3, 8), date(2024, 3, 11)]


def test_slice_session_and_contract_segments():
    idx = pd.DatetimeIndex([
        ts("2024-03-04 16:59"),  # previous session's break -> excluded
        ts("2024-03-04 17:00"),
        ts("2024-03-05 09:00"),
        ts("2024-03-05 10:00"),
        ts("2024-03-05 16:00"),  # session end (exclusive)
    ])
    df = pd.DataFrame({"price": [1, 2, 3, 4, 5], "instrument_id": [1, 1, 1, 2, 2]}, index=idx)
    out = slice_session(df, date(2024, 3, 5))
    assert list(out["price"]) == [2, 3, 4]
    assert list(out["session"]) == ["ETH", "RTH", "RTH"]
    assert list(out["contract_segment"]) == [1, 1, 2]
    rth = slice_session(df, date(2024, 3, 5), rth_only=True)
    assert list(rth["price"]) == [3, 4]
