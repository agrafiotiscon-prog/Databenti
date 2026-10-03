from datetime import date

import pandas as pd

import strategies.h004 as H
from backtest.bracket import Day
from backtest.costs import CostModel
from backtest.engine import l1_from_trades
from data.sessions import CT

C = CostModel("ES", 0.25, 12.5, 2.255, 100.0)
D = date(2025, 2, 4)


def trades(rows):
    """rows: (seconds after 10:00 CT, price, side, size)."""
    base = pd.Timestamp(D.isoformat(), tz=CT) + pd.Timedelta(hours=10)
    idx = pd.DatetimeIndex([base + pd.Timedelta(seconds=r[0]) for r in rows]).tz_convert("UTC")
    return pd.DataFrame({"price": [r[1] for r in rows], "side": [r[2] for r in rows], "size": [r[3] for r in rows]},
                        index=idx)


def test_sweep_detection_and_entry_after_the_sweep():
    tr = trades([(0, 6000.00, "A", 1), (1, 6000.25, "B", 1),
                 (5, 6000.25, "B", 60), (5, 6000.50, "B", 50), (5, 6000.75, "B", 40),   # 150 lots, 3 levels
                 (5.05, 6000.75, "A", 1), (5.3, 6001.00, "B", 1), (10, 6005.00, "B", 1), (12, 6005.25, "A", 1)])
    ev = H.prepare_day(tr, D, {})
    big = ev[(ev["size"] >= 100) & (ev["levels"] >= 3)]
    assert len(big) == 1 and big.iloc[0]["dir"] == 1 and big.iloc[0]["size"] == 150
    t = H.day_trades(Day.from_l1(l1_from_trades(tr)), ev, {"min_size": 100, "min_levels": 3, "stop_ticks": 6,
                                                            "target_ticks": 8}, D, C)
    assert len(t) == 1 and t[0]["side"] == 1
    assert t[0]["entry_ts"] > big.iloc[0]["t"]                       # never filled at the sweep itself
    assert H.day_trades(Day.from_l1(l1_from_trades(tr)), ev, {"min_size": 200, "min_levels": 3, "stop_ticks": 6,
                                                               "target_ticks": 8}, D, C) == []
