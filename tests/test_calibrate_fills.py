from datetime import date

import numpy as np
import pandas as pd

from scripts.calibrate_fills import probe_times, summarise


def test_probe_schedule_covers_rth_every_5_minutes():
    t = probe_times(date(2024, 3, 5))
    assert len(t) == 77 and t[0] == pd.Timestamp("2024-03-05 14:35", tz="UTC")
    assert t[-1] == pd.Timestamp("2024-03-05 20:55", tz="UTC")


def test_markout_sign_is_in_our_favour():
    idx = pd.DatetimeIndex(["2024-03-05 14:35:00", "2024-03-05 14:36:30"], tz="UTC")
    l1 = pd.DataFrame({"bid_px": [5000.0, 5001.0], "ask_px": [5000.25, 5001.25]}, index=idx)
    df = pd.DataFrame({"side": [1, -1], "filled": [True, True], "maker": [True, True], "price": [5000.0, 5000.25],
                       "fill_ts": [idx[0], idx[0]], "submit_ts": [idx[0], idx[0]]})
    s = summarise(df, l1)
    # mid after 60 s = 5001.125: buy at 5000 gains 4.5 ticks, sell at 5000.25 loses 3.5 ticks
    assert s["fill_rate"] == 1.0 and np.isclose(s["markout60_ticks_mean"], 0.5)
