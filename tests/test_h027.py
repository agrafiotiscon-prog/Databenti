import numpy as np

from scripts.run_h027 import day_pnl, pooled
from tests.test_portfolio import make_root


def test_day_pnl_uses_previous_close_and_charges_round_trip():
    rd = make_root(root="NQ", jump=0.0)
    d = day_pnl(rd, 1.0, 2.26)
    j = 50
    prev, day = rd.dates[j - 1], rd.dates[j]
    px = rd.closes[1][prev]
    n = max(1, round((1e6 / 3) / (px * 20)))
    gross = n * (rd.closes[1][day] / px - 1) * px * 20
    assert np.isclose(d[day], gross - n * 2 * (1.0 * 5.0 + 2.26))


def test_pooled_sums_markets_and_skips_missing():
    a, b = make_root(root="NQ"), make_root(root="YM", seed=1)
    da, db = day_pnl(a, 1.0, 2.26), day_pnl(b, 1.0, 2.26)
    days = [a.dates[10], a.dates[20]]
    p = pooled([da, db.drop(days[1])], days)
    assert np.isclose(p[days[0]], da[days[0]] + db[days[0]]) and np.isclose(p[days[1]], da[days[1]])
