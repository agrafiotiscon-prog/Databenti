import numpy as np
import pandas as pd

from scripts.paper_summary import daily_pnl, summarize


def test_daily_pnl_gross_costs_and_roll():
    led = pd.DataFrame([
        ["2026-10-05", "h030", "ZN", 2, 110.0, 1],
        ["2026-10-06", "h030", "ZN", 2, 110.5, 1],      # +0.5 * 2 * 1000 = +1000 gross, no trade
        ["2026-10-07", "h030", "ZN", 0, 110.25, 1],     # -0.25*2*1000 = -500, close 2 contracts
        ["2026-10-08", "h030", "ZN", 1, 111.0, 2],      # new instrument: no gross, open 1 contract
    ], columns=["asof", "sleeve", "root", "target", "close", "instrument_id"])
    d = daily_pnl(led).set_index("date")
    c = 15.625 + 2.26
    assert np.isclose(d.loc["2026-10-06", "gross"], 1000) and d.loc["2026-10-06", "costs"] == 0
    assert np.isclose(d.loc["2026-10-07", "net"], -500 - 2 * c)
    assert d.loc["2026-10-08", "gross"] == 0 and np.isclose(d.loc["2026-10-08", "costs"], 1 * c)


def test_book_uses_fixed_weights():
    led = pd.DataFrame([
        ["2026-10-05", "h030", "ZN", 1, 100.0, 1], ["2026-10-06", "h030", "ZN", 1, 101.0, 1],
        ["2026-10-05", "trend252", "ES", 1, 5000.0, 3], ["2026-10-06", "trend252", "ES", 1, 5010.0, 3],
    ], columns=["asof", "sleeve", "root", "target", "close", "instrument_id"])
    _, book = summarize(led, None)
    assert np.isclose(book["2026-10"], 6.49 * 1000 + 0.76 * 500)
