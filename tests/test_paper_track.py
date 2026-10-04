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
    assert set(m["sleeve"]) <= {"trend252", "h030"} and len(m) == len(snap)
