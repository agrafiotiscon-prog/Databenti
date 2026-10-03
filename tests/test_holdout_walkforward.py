from datetime import date, timedelta

import pytest

from data import holdout
from research.walkforward import from_config, walk_forward

TODAY = date(2026, 10, 3)


@pytest.fixture
def splits(tmp_path):
    (tmp_path / "config").mkdir()
    p = tmp_path / "config" / "splits.toml"
    p.write_text('holdout_months = 12\nholdout_start = ""          # frozen ISO date\n'
                 'unlock_file = "research/HOLDOUT_UNLOCK"\n\n'
                 '[walk_forward]\ntrain_months = 12\ntest_months = 3\nstep_months = 3\nembargo_days = 1\n')
    return p


def weekdays(a: date, b: date) -> list[date]:
    out, d = [], a
    while d <= b:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


def test_provisional_holdout_blocks_recent_dates(splits):
    start, frozen = holdout.holdout_start(splits, TODAY)
    assert start == date(2025, 10, 3) and not frozen
    holdout.check([date(2025, 10, 2)], splits, TODAY, root=splits.parent.parent)       # dev date: fine
    with pytest.raises(holdout.HoldoutLocked):
        holdout.check([date(2025, 10, 3)], splits, TODAY, root=splits.parent.parent)


def test_unlock_file_opens_the_holdout(splits):
    root = splits.parent.parent
    (root / "research").mkdir()
    (root / "research" / "HOLDOUT_UNLOCK").write_text("user")
    holdout.check([date(2026, 1, 5)], splits, TODAY, root=root)


def test_freeze_once_at_first_multi_month_tier_a_pull_and_never_moves(splits):
    days = weekdays(date(2024, 1, 2), date(2024, 1, 31))
    assert holdout.maybe_freeze("trades", days, splits, TODAY) is None              # < 60 days: no
    long = weekdays(date(2024, 1, 2), date(2024, 6, 28))
    assert holdout.maybe_freeze("ohlcv-1d", long, splits, TODAY) is None            # not tier A: no
    assert holdout.maybe_freeze("tbbo", long, splits, TODAY) == date(2025, 10, 3)
    assert holdout.holdout_start(splits, date(2027, 6, 1)) == (date(2025, 10, 3), True)   # frozen
    assert holdout.maybe_freeze("tbbo", long, splits, date(2027, 6, 1)) is None     # never moves


def test_downloader_refuses_holdout_dates(tmp_path, fake_client, splits):
    from data.download import Downloader
    dl = Downloader(client=fake_client, cache_dir=tmp_path / "cache", max_cost_usd=5.0)
    dl.splits_path = splits
    with pytest.raises(holdout.HoldoutLocked):
        dl.fetch_sessions("trades", [date.today()])
    assert fake_client.cost_calls == [] and fake_client.download_calls == []         # nothing priced or fetched


def test_walk_forward_folds_embargo_and_no_holdout(splits):
    dates = weekdays(date(2022, 1, 3), date(2026, 9, 30))
    folds = from_config(dates, splits, TODAY)
    assert len(folds) >= 8
    for f in folds:
        assert max(f.train) < min(f.test)                                          # test after train
        gap = [d for d in dates if max(f.train) < d < min(f.test)]
        assert len(gap) == 1                                                       # 1 trading day embargo
        assert max(f.test) < date(2025, 10, 3)                                     # never in the holdout
    tests = [d for f in folds for d in f.test]
    assert len(tests) == len(set(tests))                                           # test windows disjoint
    assert folds[0].train[0] == date(2022, 1, 3) and folds[0].test[0] == date(2023, 1, 3)


def test_walk_forward_without_enough_history_is_empty(splits):
    assert walk_forward(weekdays(date(2025, 1, 2), date(2025, 6, 30)), splits_path=splits, today=TODAY) == []
