from datetime import date

import pandas as pd
import pytest

from data import config
from data.rolls import back_adjust, detect_rolls, roll_calendar


def test_detect_rolls():
    idx = pd.date_range("2024-03-14", periods=5, freq="D", tz="UTC")
    df = pd.DataFrame({"instrument_id": [10, 10, 20, 20, 20]}, index=idx)
    r = detect_rolls(df)
    assert len(r) == 1
    assert r.loc[0, "ts"] == idx[2]
    assert (r.loc[0, "old_id"], r.loc[0, "new_id"]) == (10, 20)


def test_detect_rolls_empty_and_none():
    assert detect_rolls(pd.DataFrame({"instrument_id": []})).empty
    idx = pd.date_range("2024-01-01", periods=3, freq="D", tz="UTC")
    assert detect_rolls(pd.DataFrame({"instrument_id": [1, 1, 1]}, index=idx)).empty


def test_back_adjust_only_shifts_prior_prices():
    idx = pd.date_range("2024-03-14", periods=4, freq="D", tz="UTC")
    prices = pd.Series([5000.0, 5010.0, 5060.0, 5070.0], index=idx)
    rolls = pd.DataFrame({"ts": [idx[2]], "gap": [45.0]})
    adj = back_adjust(prices, rolls)
    assert list(adj) == [5045.0, 5055.0, 5060.0, 5070.0]
    assert list(prices) == [5000.0, 5010.0, 5060.0, 5070.0]  # input untouched


def test_roll_calendar_parse():
    res = {"result": {"ES.c.0": [
        {"d0": "2024-03-01", "d1": "2024-03-15", "s": "4916"},
        {"d0": "2024-03-15", "d1": "2024-03-20", "s": "118"},
    ]}}
    cal = roll_calendar(res, "ES.c.0")
    assert list(cal["instrument_id"]) == [4916, 118]
    assert cal.loc[1, "d0"] == date(2024, 3, 15)


def test_missing_api_key_raises(monkeypatch, tmp_path):
    monkeypatch.delenv("DATABENTO_API_KEY", raising=False)
    monkeypatch.setattr(config, "PROJECT_ROOT", tmp_path)  # no .env there
    with pytest.raises(RuntimeError, match="DATABENTO_API_KEY is not set"):
        config.get_api_key()


def test_api_key_not_in_error_or_repr(monkeypatch, tmp_path):
    secret = "db-SUPERSECRET123"
    monkeypatch.setenv("DATABENTO_API_KEY", secret)
    monkeypatch.setattr(config, "PROJECT_ROOT", tmp_path)
    assert config.get_api_key() == secret
    assert secret not in repr(config.load_settings())


def test_env_is_gitignored():
    gi = (config.PROJECT_ROOT / ".gitignore").read_text().splitlines()
    assert ".env" in gi and "cache/" in gi
