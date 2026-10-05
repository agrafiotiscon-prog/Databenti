from datetime import date

import numpy as np
import pandas as pd

from data.cot import hedger_change
from scripts.run_h046 import sides_from


def test_hedger_change_is_net_change_over_previous_open_interest():
    cot = pd.DataFrame({"asof": [date(2020, 1, 7), date(2020, 1, 14), date(2020, 2, 11)], "root": "CL",
                        "oi": [1000, 2000, 2000], "comm_long": [100, 300, 300], "comm_short": [500, 500, 400]})
    h = hedger_change(cot)
    assert np.isclose(h.loc[date(2020, 1, 14), "CL"], ((300 - 500) - (100 - 500)) / 1000)
    assert date(2020, 2, 11) not in h.index                     # 4-week gap: no week-on-week change


def test_sides_rank_top_and_bottom_halves_skipping_missing():
    sig = pd.DataFrame([[0.3, -0.1, np.nan, 0.0, 0.2]], columns=list("ABCDE"))
    s = sides_from(sig).iloc[0]
    assert s.to_dict() == {"A": 1, "B": -1, "C": 0, "D": -1, "E": 1}
