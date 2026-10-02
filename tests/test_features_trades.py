import numpy as np
import pandas as pd
import pytest

from features.absorption import absorption_events
from features.common import ohlcv_bars
from features.footprint import bar_delta, delta_divergence, footprint, trade_cum_delta
from features.imbalance import diagonal_imbalances, stacked_imbalances
from features.profile import developing_profile, session_levels, value_area, vwap, vwap_bars
from tests.causality import assert_causal
from tests.synth import T0, random_trades, trades_df

M = pd.Timedelta("1min")


# ----------------------------------------------------------------------- footprint / delta
def small_tape():
    return trades_df([
        (0.5, 5000.25, 3, "B"),   # buyer lifts ask -> ask_vol
        (10, 5000.00, 2, "A"),    # seller hits bid -> bid_vol
        (20, 5000.00, 1, "N"),    # auction/implied -> unknown, never assigned
        (65, 5000.25, 4, "A"),
    ])


def test_footprint_hand_example():
    fp = footprint(small_tape())
    b0 = fp[fp["bar_start"] == T0].set_index("price")
    assert b0.loc[5000.00, ["ask_vol", "bid_vol", "unk_vol", "n_trades"]].tolist() == [0, 2, 1, 2]
    assert b0.loc[5000.25, ["ask_vol", "bid_vol", "unk_vol"]].tolist() == [3, 0, 0]
    b1 = fp[fp["bar_start"] == T0 + M]
    assert b1[["price", "bid_vol"]].values.tolist() == [[5000.25, 4]]
    assert (fp["known_at"] == fp["bar_start"] + M).all()


def test_bar_delta_and_cum_delta():
    bd = bar_delta(footprint(small_tape()))
    assert bd["delta"].tolist() == [1, -4]
    assert bd["cum_delta"].tolist() == [1, -3]
    assert bd["volume"].tolist() == [6, 4]
    assert bd["unk_vol"].tolist() == [1, 0]


def test_trade_cum_delta_ignores_unknown_side():
    assert trade_cum_delta(small_tape())["cum_delta"].tolist() == [3, 1, 1, -3]


def test_delta_divergence():
    idx = pd.date_range(T0, periods=4, freq="1min")
    bars = pd.DataFrame({"high": [10, 11, 12, 13], "low": [9, 9, 9, 8],
                         "cum_delta": [100, 120, 150, 140], "known_at": idx + M}, index=idx)
    d = delta_divergence(bars, lookback=2)
    # bar 3: new high (13 > 12) but cum_delta 140 <= max(120, 150) -> bearish divergence
    assert d["bearish_div"].tolist() == [False, False, False, True]
    # bar 3: new low (8 < 9) and cum_delta 140 >= min(120,150) -> bullish too (both flags allowed)
    assert d["bullish_div"].tolist() == [False, False, False, True]


# ----------------------------------------------------------------------- profile / vwap
def test_value_area_cbot_method():
    v = pd.Series({100.0: 10, 101.0: 20, 102.0: 50, 103.0: 15, 104.0: 5})
    # POC 102 (50). Need 70: below pair (100,101)=30 > above pair (103,104)=20 -> add below -> 80
    assert value_area(v, 0.70) == (102.0, 100.0, 102.0)


def test_value_area_poc_tiebreak_and_edges():
    # equal max at 100 and 102; vw-mean is 101 -> equidistant -> lower price wins
    assert value_area(pd.Series({100.0: 30, 101.0: 10, 102.0: 30}))[0] == 100.0
    # tie broken by closeness to volume-weighted mean (pulled toward 103 by its volume)
    assert value_area(pd.Series({100.0: 30, 102.0: 30, 103.0: 25}))[0] == 102.0
    assert value_area(pd.Series({5000.0: 7})) == (5000.0, 5000.0, 5000.0)
    assert np.isnan(value_area(pd.Series(dtype=float))[0])


def test_developing_profile_uses_only_past_bars():
    tape = trades_df([(1, 5000.0, 10, "B"), (2, 5000.25, 5, "A"), (61, 5001.0, 40, "B")])
    dp = developing_profile(tape)
    assert dp.loc[T0, "poc"] == 5000.0             # second bar not yet included
    assert dp.loc[T0 + M, "poc"] == 5001.0
    assert (dp["known_at"] == dp.index + M).all()


def test_vwap_and_bands():
    vw = vwap(trades_df([(1, 100.0, 1, "B"), (2, 102.0, 1, "A")]))
    assert vw["vwap"].tolist() == [100.0, 101.0]
    assert vw["sd"].tolist() == [0.0, 1.0]
    assert vw["upper_2"].iloc[-1] == 103.0 and vw["lower_1"].iloc[-1] == 100.0


def test_session_levels():
    lv = session_levels(trades_df([(1, 5000.0, 10, "B"), (2, 5000.25, 1, "A"), (3, 4999.75, 1, "A")]))
    assert lv["poc"] == 5000.0 and lv["high"] == 5000.25 and lv["low"] == 4999.75


# ----------------------------------------------------------------------- imbalances
def imbalance_bar():
    rows, s = [], 1
    for price, bid, ask in [(5000.00, 5, 2), (5000.25, 1, 30), (5000.50, 2, 40),
                            (5000.75, 3, 50), (5001.00, 20, 1)]:
        rows += [(s, price, bid, "A"), (s + 1, price, ask, "B")]
        s += 2
    return trades_df(rows)


def test_diagonal_imbalances_hand_example():
    imb = diagonal_imbalances(footprint(imbalance_bar()), ratio=3.0, min_vol=10).set_index("price")
    assert imb["buy_imb"].to_dict() == {5000.00: False, 5000.25: True, 5000.50: True,
                                        5000.75: True, 5001.00: False}
    # 5001.00: bid 20 >= 10 and >= 3 * ask(5001.25)=0 -> sell imbalance
    assert imb["sell_imb"].to_dict() == {5000.00: False, 5000.25: False, 5000.50: False,
                                         5000.75: False, 5001.00: True}


def test_stacked_imbalances():
    z = stacked_imbalances(diagonal_imbalances(footprint(imbalance_bar())), n_stack=3)
    assert z[["side", "low", "high", "count"]].values.tolist() == [["buy", 5000.25, 5000.75, 3]]
    assert stacked_imbalances(diagonal_imbalances(footprint(imbalance_bar())), n_stack=4).empty


# ----------------------------------------------------------------------- absorption
def test_sell_absorption_fires_once_and_rearms_after_break():
    rows = [(i * 2, 5000.0, 30, "A") for i in range(10)]           # 300 sold into 5000.00 in 20 s
    rows += [(25, 4999.75, 1, "A")]                                 # price goes through -> re-arm
    rows += [(30 + i, 5000.0, 30, "A") for i in range(10)]          # but window still holds 4999.75...
    rows += [(70 + i, 5000.0, 30, "A") for i in range(8)]           # ...until it rolls out of 30 s
    ev = absorption_events(trades_df(rows), window="30s", min_vol=200)
    assert ev["side"].tolist() == ["sell_absorbed", "sell_absorbed"]
    assert ev["known_at"].iloc[0] == T0 + pd.Timedelta(seconds=12)  # 7th print: 210 >= 200
    assert ev["known_at"].iloc[1] > T0 + pd.Timedelta(seconds=55)   # only after 4999.75 left window


def test_no_absorption_if_price_went_through():
    rows = [(i, 5000.0, 50, "A") for i in range(5)] + [(5.5, 4999.75, 1, "A"), (6, 5000.0, 50, "A")]
    assert absorption_events(trades_df(rows), window="30s", min_vol=200).iloc[:1]["known_at"].tolist() == \
        [T0 + pd.Timedelta(seconds=3)]   # fires at 200 before the break, not after it


def test_buy_absorption_mirror():
    rows = [(i, 5000.0, 50, "B") for i in range(5)]
    ev = absorption_events(trades_df(rows), window="30s", min_vol=200)
    assert ev[["side", "level", "vol_at_level"]].values.tolist() == [["buy_absorbed", 5000.0, 200]]


# ----------------------------------------------------------------------- no lookahead
@pytest.mark.parametrize("feature", [
    lambda d: footprint(d).set_index(["bar_start", "price"]),
    lambda d: bar_delta(footprint(d)),
    lambda d: ohlcv_bars(d),
    lambda d: developing_profile(d),
    lambda d: vwap(d),
    lambda d: vwap_bars(d),
    lambda d: trade_cum_delta(d),
    lambda d: stacked_imbalances(diagonal_imbalances(footprint(d), min_vol=5)),
    lambda d: absorption_events(d, window="20s", min_vol=60),
    lambda d: delta_divergence(ohlcv_bars(d).join(bar_delta(footprint(d))[["cum_delta"]]), 5),
], ids=["footprint", "bar_delta", "ohlcv", "dev_profile", "vwap", "vwap_bars", "cum_delta",
        "stacked_imb", "absorption", "divergence"])
def test_no_lookahead(feature):
    assert_causal(feature, random_trades())


# ----------------------------------------------------------------------- negative controls
def _leaky_completed_poc(d):
    """Uses TODAY's completed profile on every bar -- classic lookahead."""
    bars = ohlcv_bars(d)
    bars["poc"] = session_levels(d)["poc"]
    return bars


def _leaky_centered_vwap(d):
    vw = vwap(d)
    vw["vwap"] = vw["vwap"].rolling(21, center=True, min_periods=1).mean()
    return vw


@pytest.mark.parametrize("leaky", [_leaky_completed_poc, _leaky_centered_vwap], ids=["completed_poc", "centered"])
def test_causality_checker_catches_lookahead(leaky):
    with pytest.raises(AssertionError):
        assert_causal(leaky, random_trades())
