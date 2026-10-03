from datetime import date

import numpy as np
import pandas as pd

import strategies.h002 as H
from backtest.bracket import Day
from backtest.costs import CostModel
from backtest.engine import l1_from_trades
from data.sessions import CT

C = CostModel("ES", 0.25, 12.5, 2.255, 100.0)


def day_trades_df(d, prices_at):
    """prices_at: list of (HH, MM, SS, price, side); 1 lot each."""
    idx = pd.DatetimeIndex([pd.Timestamp(d.isoformat(), tz=CT) + pd.Timedelta(hours=h, minutes=m, seconds=s)
                            for h, m, s, _, _ in prices_at]).tz_convert("UTC")
    return pd.DataFrame({"price": [r[3] for r in prices_at], "side": [r[4] for r in prices_at], "size": 1},
                        index=idx)


def test_signal_uses_only_data_before_decision_and_needs_same_contract_prev_close():
    st = {}
    d1, d2 = date(2025, 2, 3), date(2025, 2, 4)
    t1 = day_trades_df(d1, [(8, 30, 0, 6000.0, "B"), (14, 59, 0, 6000.0, "A")])
    assert H.prepare_day(t1, d1, st) is None and st["prev"][1] == 6000.0      # first day: no prev close
    t2 = day_trades_df(d2, [(8, 30, 0, 6001.0, "B"), (8, 59, 0, 6006.0, "B"), (9, 0, 0, 5000.0, "A"),
                            (14, 29, 0, 6012.0, "B"), (14, 30, 0, 1.0, "A"), (14, 31, 0, 6013.0, "B"),
                            (14, 59, 40, 6015.0, "B")])
    f = H.prepare_day(t2, d2, st)
    assert round(f["open30"]["ret_bp"], 3) == round((6006 / 6000 - 1) * 1e4, 3)   # 09:00 print excluded
    assert round(f["day"]["ret_bp"], 3) == round((6012 / 6000 - 1) * 1e4, 3)      # 14:30 print excluded
    assert f["open30"]["delta"] == 2 and f["day"]["delta"] == 2     # B,B | A(09:00),B


def test_filters_and_trade_direction():
    d = date(2025, 2, 4)
    tr = day_trades_df(d, [(14, 29, 59, 6000.0, "A"), (14, 30, 0, 6000.25, "B"), (14, 30, 1, 6000.0, "A"),
                           (14, 45, 0, 6003.0, "B"), (14, 59, 31, 6004.0, "A"), (14, 59, 32, 6004.25, "B"),
                           (14, 59, 50, 6004.0, "A")])
    day = Day.from_l1(l1_from_trades(tr))
    feat = {"prev_close": 5990.0, "open30": {"ret_bp": 5.0, "delta": -10.0}, "day": {"ret_bp": 16.7, "delta": 50.0}}
    base = {"signal": "day", "min_abs_bp": 10, "stop_ticks": 0, "delta_filter": True}
    t = H.day_trades(day, feat, base, d, C)
    assert len(t) == 1 and t[0]["side"] == 1 and t[0]["reason"] == "time"
    assert H.day_trades(day, feat, {**base, "signal": "open30"}, d, C) == []          # |5 bp| < 10
    assert H.day_trades(day, feat, {**base, "signal": "open30", "min_abs_bp": 0}, d, C) == []   # delta disagrees
    assert len(H.day_trades(day, feat, {**base, "signal": "open30", "min_abs_bp": 0, "delta_filter": False}, d, C)) == 1
    assert H.day_trades(day, None, base, d, C) == []
