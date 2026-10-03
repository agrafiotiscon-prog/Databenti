import math
from datetime import date

import numpy as np
import pandas as pd
import pytest

from backtest import metrics as M

UTC = "UTC"


def trades_df(rows):
    """rows: (exit_ts_utc, net_pnl, ticks)."""
    return pd.DataFrame({"exit_ts": pd.to_datetime([r[0] for r in rows], utc=True),
                         "net_pnl": [r[1] for r in rows], "ticks": [r[2] for r in rows],
                         "fees": [4.51] * len(rows)})


def test_trade_stats_hand_computed():
    t = trades_df([("2024-03-05 15:00", 100.0, 8), ("2024-03-05 16:00", -50.0, -4),
                   ("2024-03-05 17:00", 20.0, 2)])
    s = M.trade_stats(t)
    assert s["trades"] == 3 and s["flag_few_trades"]
    assert s["win_rate"] == pytest.approx(2 / 3) and s["profit_factor"] == pytest.approx(120 / 50)
    sd = np.std([100, -50, 20], ddof=1)
    assert s["t_stat"] == pytest.approx((70 / 3) / (sd / math.sqrt(3)))


def test_daily_pnl_includes_zero_days_and_uses_cme_trading_date():
    # 23:30 UTC on Mon 03-04 = 17:30 CT -> belongs to trading date Tue 03-05
    t = trades_df([("2024-03-04 23:30", 10.0, 1), ("2024-03-05 15:00", 5.0, 1)])
    d = M.daily_pnl(t, [date(2024, 3, 4), date(2024, 3, 5), date(2024, 3, 6)])
    assert d.to_dict() == {date(2024, 3, 4): 0.0, date(2024, 3, 5): 15.0, date(2024, 3, 6): 0.0}
    with pytest.raises(ValueError):
        M.daily_pnl(t, [date(2024, 3, 6)])


def test_sharpe_drawdown_concentration():
    daily = pd.Series([100.0, -50.0, -60.0, 30.0, 200.0, 0.0])
    assert M.sharpe(daily) == pytest.approx(daily.mean() / daily.std(ddof=1) * math.sqrt(252))
    dd = M.drawdown(daily)
    assert dd["max_drawdown"] == -110.0 and dd["max_dd_days"] == 3   # 100 -> -10 lasts 3 days
    c = M.concentration(daily)
    assert c["top5_days_share"] == pytest.approx((200 + 100 + 30 + 0 - 50) / 220)
    assert c["flag_concentrated"]                                     # without best 5 PnL <= 0


def test_lo_adjustment_reduces_sharpe_for_positive_autocorrelation():
    rng = np.random.default_rng(1)
    e = rng.normal(1, 10, 2000)
    ar = np.empty_like(e)
    ar[0] = e[0]
    for i in range(1, len(e)):
        ar[i] = 0.6 * ar[i - 1] + e[i]
    s = pd.Series(ar)
    assert M.lo_adjusted_sharpe(s) < M.sharpe(s)
    iid = pd.Series(rng.normal(1, 10, 2000))                          # negative control: ~unchanged
    assert M.lo_adjusted_sharpe(iid) == pytest.approx(M.sharpe(iid), rel=0.1)


def test_psr_is_a_probability_and_monotone():
    rng = np.random.default_rng(2)
    good = pd.Series(rng.normal(5, 10, 500))
    bad = pd.Series(rng.normal(-5, 10, 500))
    assert 0.99 < M.probabilistic_sharpe(good) <= 1 and M.probabilistic_sharpe(bad) < 0.01


def test_markouts_are_signed_mid_moves_after_our_fills():
    idx = pd.DatetimeIndex(["2024-03-05 14:30:00", "2024-03-05 14:30:01", "2024-03-05 14:30:10"], tz=UTC)
    l1 = pd.DataFrame({"bid_px": [5000.0, 5001.0, 4999.0], "ask_px": [5000.25, 5001.25, 4999.25]}, index=idx)
    fills = pd.DataFrame({"fill_ts": [idx[0]], "side": [1], "price": [5000.25], "end_flatten": [False]})
    mk = M.markouts(fills, l1, horizons=("1s", "10s", "60s"))
    assert mk.loc[0, "1s"] == pytest.approx(5001.125 - 5000.25)        # bought, mid went up
    assert mk.loc[0, "10s"] == pytest.approx(4999.125 - 5000.25)
    assert np.isnan(mk.loc[0, "60s"])                                  # beyond the data: unknown, not 0


def test_exposure():
    f = pd.DataFrame({"fill_ts": pd.to_datetime(["2024-03-05 14:30", "2024-03-05 14:45"], utc=True),
                      "side": [1, -1], "qty": [1, 1]})
    assert M.exposure(f, session_minutes=390) == pytest.approx(15 / 390)
