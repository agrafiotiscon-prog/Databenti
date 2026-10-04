from datetime import date

import numpy as np
import pandas as pd

from data.sessions import CT
from features.common import BUY_AGGRESSOR, SELL_AGGRESSOR
from strategies.h028 import decision_times, imbalances


def frame(rows):
    idx = pd.DatetimeIndex([r[0] for r in rows]).tz_convert("UTC")
    df = pd.DataFrame({"side": [r[1] for r in rows], "size": [r[2] for r in rows], "price": 5000.0}, index=idx)
    return df.sort_index()                                    # trade data is time-ordered


def test_decision_times_span_0900_to_1400_ct():
    t = decision_times(date(2025, 3, 4))
    assert len(t) == 11 and t[0].tz_convert(CT).hour == 9 and t[-1].tz_convert(CT).hour == 14


def test_imbalance_uses_only_trades_strictly_before_t():
    t = pd.Timestamp("2025-03-04 10:00", tz=CT)
    rows = [(t - pd.Timedelta(minutes=3), BUY_AGGRESSOR, 30), (t - pd.Timedelta(minutes=1), SELL_AGGRESSOR, 10),
            (t - pd.Timedelta(minutes=10), SELL_AGGRESSOR, 50),          # outside 5 min, inside 15 min
            (t, SELL_AGGRESSOR, 1000)]                                    # at t: must be ignored
    imb = imbalances(frame(rows), [t])
    assert np.isclose(imb[(t, 5)], (30 - 10) / 40)
    assert np.isclose(imb[(t, 15)], (30 - 10 - 50) / 90)
