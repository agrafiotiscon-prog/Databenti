import numpy as np

from research.daily_eval import Outright, window_pnl
from tests.test_portfolio import make_root


def test_window_pnl_exposure_costs_and_roll():
    rd = make_root(root="ZN", roll_at=200, jump=0.0)
    m = Outright(rd, 1000.0, 15.625)
    d = rd.dates
    net, cnt = window_pnl(m, [(d[10], d[13], 1)], notional=250_000, slip_ticks=1.0, fee_side=2.26)
    n = max(1, round(250_000 / (rd.closes[1][d[10]] * 1000)))
    gross = sum(n * (rd.closes[1][d[j]] - rd.closes[1][d[j - 1]]) * 1000 for j in (11, 12, 13))
    assert np.isclose(net.sum(), gross - 2 * n * (15.625 + 2.26))
    assert cnt[d[10]] == n and cnt[d[13]] == n and net[d[10]] == -n * (15.625 + 2.26)
    # a window spanning the v.0 change at day 200 pays an extra roll (2 sides)
    _, c2 = window_pnl(m, [(d[198], d[202], -1)], 250_000, 1.0, 2.26)
    assert c2.sum() == 4 * max(1, round(250_000 / (rd.closes[1][d[198]] * 1000)))


def test_spread_pnl_short_near_long_far():
    from data.universe import BY_ROOT
    from scripts.run_r9 import spread_pnl
    rd = make_root(root="CL", jump=2.0)
    d = rd.dates
    rd.closes[2] = rd.closes[2].copy()
    rd.closes[2].iloc[11:] += 1.0                        # far gains $1 vs near from day 11 on
    net, ent = spread_pnl(rd, BY_ROOT["CL"], [(d[10], d[14])], notional=83_333, slip=1.0, fee=2.26)
    n = max(1, round(83_333 / (rd.closes[1][d[10]] * 1000)))
    assert np.isclose(net.sum(), n * 1000 * 1.0 - 4 * n * (10.0 + 2.26)) and ent.sum() == 1
