from datetime import date
from pathlib import Path

import pytest

from data.cost_guard import CostLimitExceeded
from data.download import Downloader
from tests.conftest import FakeClient


def make(tmp_path, client, limit=5.0):
    return Downloader(client=client, cache_dir=tmp_path, max_cost_usd=limit)


def test_cost_is_checked_before_download(tmp_path, fake_client):
    dl = make(tmp_path, fake_client)
    dl.fetch_days("trades", [date(2024, 3, 5)])
    assert len(fake_client.cost_calls) == 1
    assert len(fake_client.download_calls) == 1
    req = fake_client.cost_calls[0]
    assert req["dataset"] == "GLBX.MDP3"
    assert req["symbols"] == "ES.c.0"
    assert req["stype_in"] == "continuous"


def test_cost_printed(tmp_path, fake_client, capsys):
    make(tmp_path, fake_client).fetch_days("trades", [date(2024, 3, 5)])
    out = capsys.readouterr().out
    assert "$0.1000" in out and "TOTAL" in out


def test_cache_prevents_second_download(tmp_path, fake_client):
    dl = make(tmp_path, fake_client)
    dl.fetch_days("trades", [date(2024, 3, 5)])
    dl.fetch_days("trades", [date(2024, 3, 5)])
    assert len(fake_client.download_calls) == 1
    assert len(fake_client.cost_calls) == 1  # cached chunk is not even priced


def test_partial_cache_only_fetches_missing(tmp_path, fake_client):
    dl = make(tmp_path, fake_client)
    dl.fetch_days("trades", [date(2024, 3, 5)])
    dl.fetch_days("trades", [date(2024, 3, 5), date(2024, 3, 6)])
    assert [c["start"][:10] for c in fake_client.download_calls] == ["2024-03-05", "2024-03-06"]


def test_over_limit_blocks_all_downloads(tmp_path):
    client = FakeClient(cost_per_request=3.0)
    dl = make(tmp_path, client, limit=5.0)
    with pytest.raises(CostLimitExceeded):
        dl.fetch_days("mbo", [date(2024, 3, 5), date(2024, 3, 6)])  # $6 total
    assert client.download_calls == []
    assert not any(tmp_path.rglob("*.dbn.zst"))


def test_over_limit_allowed_explicitly(tmp_path):
    client = FakeClient(cost_per_request=3.0)
    make(tmp_path, client).fetch_days("mbo", [date(2024, 3, 5), date(2024, 3, 6)],
                                      allow_over_limit=True)
    assert len(client.download_calls) == 2


def test_failed_download_is_not_cached(tmp_path, fake_client):
    def boom(**kw):
        raise ConnectionError("network died")
    fake_client.timeseries.get_range = boom
    dl = make(tmp_path, fake_client)
    with pytest.raises(ConnectionError):
        dl.fetch_days("trades", [date(2024, 3, 5)])
    _, missing = dl.plan("trades", [date(2024, 3, 5)])
    assert len(missing) == 1


def test_spend_log_written(tmp_path, fake_client):
    make(tmp_path, fake_client).fetch_days("trades", [date(2024, 3, 5)])
    log = (tmp_path / "spend_log.csv").read_text()
    assert "estimated_cost_usd" in log and "trades" in log


def test_download_log_only_records_real_downloads(tmp_path, fake_client):
    dl = make(tmp_path, fake_client)
    dl.estimate("trades", [date(2024, 3, 5)])                  # dry run: estimate only
    assert not (tmp_path / "download_log.csv").exists()
    dl.fetch_days("trades", [date(2024, 3, 5)])
    dl.fetch_days("trades", [date(2024, 3, 5)])                # cached: no second entry
    rows = (tmp_path / "download_log.csv").read_text().strip().splitlines()
    assert len(rows) == 2 and "trades" in rows[1]
    assert rows[1].split(",")[6] != ""                          # carries the cost estimate


def test_session_fetch_covers_two_utc_days(tmp_path, fake_client):
    # Tue 2024-03-05 session: Mon 17:00 CT (23:00 UTC) -> Tue 16:00 CT (22:00 UTC)
    make(tmp_path, fake_client).fetch_sessions("trades", [date(2024, 3, 5)])
    days = sorted(c["start"][:10] for c in fake_client.download_calls)
    assert days == ["2024-03-04", "2024-03-05"]


def test_rth_only_needs_one_utc_day(tmp_path, fake_client):
    make(tmp_path, fake_client).fetch_sessions("trades", [date(2024, 3, 5)], rth_only=True)
    assert len(fake_client.download_calls) == 1


def test_unsupported_schema(tmp_path, fake_client):
    with pytest.raises(ValueError):
        make(tmp_path, fake_client).fetch_days("bogus", [date(2024, 3, 5)])


def test_retry_after_interrupted_download(tmp_path, fake_client):
    # the real client raises FileExistsError if the .part path exists, and a cut stream leaves one
    real_get_range = fake_client.timeseries.get_range

    def strict(path=None, **kw):
        if Path(path).exists():
            raise FileExistsError(path)
        return real_get_range(path=path, **kw)

    def cut(path=None, **kw):
        Path(path).write_bytes(b"half")
        raise ConnectionError("response ended prematurely")

    dl = make(tmp_path, fake_client)
    fake_client.timeseries.get_range = cut
    with pytest.raises(ConnectionError):
        dl.fetch_days("trades", [date(2024, 3, 5)])
    fake_client.timeseries.get_range = strict
    paths = dl.fetch_days("trades", [date(2024, 3, 5)])
    assert paths[0].read_bytes() == b"fake-dbn"
