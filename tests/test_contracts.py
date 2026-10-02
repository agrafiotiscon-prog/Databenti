from datetime import date

import pandas as pd
import pytest

from data.contracts import (active_contract, continuous_rank, continuous_symbol, front_expiry,
                            roll_date, third_friday)
from data.download import Downloader
from data.flags import F_LAST, F_SNAPSHOT, drop_snapshot, event_end_mask, has_flag


@pytest.mark.parametrize("y,m,expected", [
    (2023, 3, date(2023, 3, 17)),   # ESH3 expiry (matches Databento ES.c.0 mapping ending 2023-03-19)
    (2025, 3, date(2025, 3, 21)),
    (2024, 6, date(2024, 6, 21)),
    (2024, 3, date(2024, 3, 15)),   # month starts on a Friday
])
def test_third_friday(y, m, expected):
    assert third_friday(y, m) == expected
    assert expected.weekday() == 4


def test_roll_date_is_thursday_eight_days_before():
    exp = third_friday(2024, 3)
    assert roll_date(exp) == date(2024, 3, 7)
    assert roll_date(exp).weekday() == 3


def test_rank_switches_on_roll_thursday_and_back_after_expiry():
    assert continuous_rank(date(2024, 3, 6)) == 0
    assert continuous_rank(date(2024, 3, 7)) == 1   # roll Thursday
    assert continuous_rank(date(2024, 3, 15)) == 1  # expiry Friday: still on next contract
    assert continuous_rank(date(2024, 3, 18)) == 0  # Monday after expiry: new front month
    assert continuous_symbol(date(2024, 3, 7), "NQ") == "NQ.c.1"


def test_roll_offset_is_configurable():
    # e.g. if real data shows liquidity crosses later in expiry week
    assert continuous_rank(date(2025, 3, 17), days_before=4) == 1
    assert continuous_rank(date(2025, 3, 14), days_before=4) == 0


def test_active_contract_labels():
    assert active_contract(date(2024, 3, 6)) == ("H", 2024)
    assert active_contract(date(2024, 3, 7)) == ("M", 2024)
    assert active_contract(date(2024, 12, 20)) == ("H", 2025)   # year rollover in roll window
    assert front_expiry(date(2024, 12, 23)) == date(2025, 3, 21)


def test_fetch_sessions_across_roll_uses_next_contract(tmp_path, fake_client, capsys):
    dl = Downloader(client=fake_client, cache_dir=tmp_path, max_cost_usd=5.0)
    dl.fetch_sessions("trades", [date(2024, 3, 6), date(2024, 3, 7)])
    got = sorted((c["symbols"], c["start"][:10]) for c in fake_client.download_calls)
    assert got == [("ES.c.0", "2024-03-05"), ("ES.c.0", "2024-03-06"),
                   ("ES.c.1", "2024-03-06"), ("ES.c.1", "2024-03-07")]
    # priced once, as one combined total, before any download
    assert len(fake_client.cost_calls) == 4
    assert capsys.readouterr().out.count("TOTAL") == 1


def test_fetch_sessions_forced_symbol(tmp_path, fake_client):
    dl = Downloader(client=fake_client, cache_dir=tmp_path, max_cost_usd=5.0)
    dl.fetch_sessions("trades", [date(2024, 3, 7)], symbol="ES.v.0")
    assert {c["symbols"] for c in fake_client.download_calls} == {"ES.v.0"}


def test_flag_helpers():
    df = pd.DataFrame({"flags": [F_SNAPSHOT | 8, F_LAST | F_SNAPSHOT | 8, F_LAST, 0, 130]})
    assert list(has_flag(df["flags"], F_LAST)) == [False, True, True, False, True]
    assert len(drop_snapshot(df)) == 3
    assert event_end_mask(df).sum() == 3
