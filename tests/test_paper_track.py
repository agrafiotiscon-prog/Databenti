from datetime import date

import pandas as pd

from portfolio.engine import prepare, target_contracts
from scripts.paper_track import append, h030_target, mark, snapshot
from tests.test_portfolio import make_root


def test_h030_target_is_long_for_the_k_closes_before_month_end():
    dates = [d.date() for d in pd.bdate_range("2025-03-01", "2025-04-30")]
    march = [d for d in dates if d.month == 3]
    flags = [h030_target(dates, d, k=3) for d in march]
    assert flags[-4:] == [1, 1, 1, 0] and sum(flags) == 3      # decided at closes T-3, T-2, T-1; flat at T


def test_future_days_follows_the_daily_bar_calendar():
    from scripts.paper_track import future_days
    days = set(future_days(date(2021, 12, 1), date(2022, 1, 5)))
    assert date(2021, 12, 24) not in days and date(2021, 12, 31) in days     # observed Christmas; 31 Dec trades
    assert date(2024, 3, 29) not in future_days(date(2024, 3, 1), date(2024, 3, 31))   # Good Friday
    assert date(2026, 10, 12) in future_days(date(2026, 10, 9), date(2026, 10, 30))    # Columbus Day has a bar
    assert future_days(date(2026, 10, 30), date(2026, 10, 30)) == []


def test_h030_target_forward_equals_replay_when_the_data_ends_early():
    # live: the data ends at (or a few days after) asof, never at the month-end (bug found 2026-10-11: the last
    # downloaded day was taken as the month-end, so h030 went long three weeks early)
    from scripts.paper_track import future_days
    dates = future_days(date(2024, 2, 29), date(2024, 4, 30))               # March 2024 ends on Thu 28 (Good Friday)
    full = [h030_target(dates, d) for d in dates]
    for lag in (0, 2):
        assert [h030_target(dates[:i + 1 + lag], d) for i, d in enumerate(dates)] == full
    assert [d for d, f in zip(dates, full) if f and d.month == 3] == [date(2024, 3, 25), date(2024, 3, 26),
                                                                      date(2024, 3, 27)]
    october = [d.date() for d in pd.bdate_range("2026-10-01", "2026-10-09")]
    assert [h030_target(october, d) for d in october] == [0] * len(october)


def test_h035_side_is_flat_mid_month_when_the_data_ends_early():
    from scripts.paper_track import cut, h035_side
    rds = {r: make_root(root=r, seed=i, drift=d) for i, (r, d) in enumerate((("ES", 0.004), ("ZN", -0.001)))}
    dates = rds["ES"].dates
    month = [d for d in dates if (d.year, d.month) == (dates[200].year, dates[200].month)]
    short = {r: cut(rd, month[5]) for r, rd in rds.items()}                 # data ends on the 6th trading day
    assert [h035_side(short, d) for d in month[:6]] == [0] * 6


def test_snapshot_targets_match_full_history_targets(tmp_path):
    rds = {r: make_root(root=r, seed=i, drift=0.001 * (i - 2)) for i, r in enumerate(("ES", "ZT", "ZF", "ZN", "ZB"))}
    asof = rds["ES"].dates[330]
    snap = snapshot(rds, asof)
    full = target_contracts([prepare(rd) for rd in rds.values()], "trend252", 1_000_000.0)
    t = snap[snap.sleeve == "trend252"].set_index("root")["target"]
    assert all(int(full[r][asof]) == int(t[r]) for r in t.index)   # no information after asof is used
    assert set(snap[snap.sleeve == "h030"]["root"]) == {"ZT", "ZF", "ZN", "ZB"}
    ledger = tmp_path / "l.csv"
    append(ledger, snap)
    append(ledger, snapshot(rds, rds["ES"].dates[331]))
    append(ledger, snapshot(rds, rds["ES"].dates[331]))             # re-run replaces, not duplicates
    assert len(pd.read_csv(ledger)) == 2 * len(snap)
    m = mark(ledger)
    assert set(m["sleeve"]) <= {"trend252", "h030", "h035_watch", "h044", "h045"} and len(m) == len(snap)


def test_h035_side_window_and_sign():
    from scripts.paper_track import h035_side
    rds = {r: make_root(root=r, seed=i, drift=d) for i, (r, d) in enumerate((("ES", 0.004), ("ZN", -0.001)))}
    dates = rds["ES"].dates
    month = [d for d in dates if (d.year, d.month) == (dates[200].year, dates[200].month)]
    flags = [h035_side(rds, d) for d in month]
    assert all(f == 0 for f in flags[:-6]) and flags[-1] == 0
    window = flags[-6:-1]
    assert len(set(window)) == 1 and window[0] in (-1, 1)        # one side for the whole window


def test_fomc_long_matches_the_backtest_windows():
    from scripts.paper_track import fomc_long
    from scripts.run_fomc_xasset import windows
    from research.daily_eval import Outright
    rd = make_root(root="ZN", seed=3)
    dates = rd.dates
    fomc = [dates[100], dates[160], dates[161 + 40]]
    m = Outright(rd, 1000, 15.625)
    for before, after in ((2, 1), (1, 0)):
        held = set()
        for s, e, _ in windows(m, fomc, before, after):
            held |= {d for d in dates if s <= d < e}             # decision closes with a position
        flags = {d for d in dates[90:220] if fomc_long(dates, d, before, after, fomc)}
        assert flags == {d for d in held if dates[90] <= d < dates[220]}


def test_fomc_long_forward_uses_business_days_beyond_the_data():
    from scripts.paper_track import fomc_long
    dates = [d.date() for d in pd.bdate_range("2026-10-01", "2026-10-23")]
    f = date(2026, 10, 28)                                        # Wednesday, after the data ends (Fri 23rd)
    assert [fomc_long(dates, d, 2, 1, [f]) for d in dates[-3:]] == [0, 0, 0]
    ext = dates + [date(2026, 10, 26)]                            # Monday = F-2 -> enter
    assert fomc_long(ext, date(2026, 10, 26), 2, 1, [f]) == 1
    assert fomc_long(ext, date(2026, 10, 26), 1, 0, [f]) == 0     # H-045 enters on Tuesday F-1


def test_loggable_holds_back_days_from_the_earliest_failed_fetch():
    from scripts.paper_track import loggable
    days = [date(2026, 10, 13), date(2026, 10, 14), date(2026, 10, 15), date(2026, 10, 16)]
    assert loggable(days, {}) == days
    assert loggable(days, {"6A.v.0": date(2026, 10, 14), "HG.v.1": date(2026, 10, 15)}) == [date(2026, 10, 13)]
    assert loggable(days, {"ES.v.0": date(2026, 10, 13)}) == []


def test_available_end_caps_and_caches():
    from types import SimpleNamespace
    import scripts.paper_track as pt
    calls = []

    class Meta:
        def get_dataset_range(self, dataset):
            calls.append(dataset)
            return {"schema": {"ohlcv-1d": {"end": "2026-10-05T00:00:00.000000000Z"}}}
    pt._avail.clear()
    dl = SimpleNamespace(client=SimpleNamespace(metadata=Meta()), dataset="GLBX.MDP3")
    assert pt.available_end(dl) == date(2026, 10, 5) and pt.available_end(dl) == date(2026, 10, 5)
    assert len(calls) == 1
    pt._avail.clear()
