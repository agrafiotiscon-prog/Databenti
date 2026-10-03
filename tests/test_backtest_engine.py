import numpy as np
import pandas as pd
import pytest

from backtest.costs import CostModel, load_costs
from backtest.engine import l1_from_tbbo, run

T0 = pd.Timestamp("2024-03-05 14:30:00", tz="UTC")


def costs(latency_ms=100.0, fee=2.255, mult=1.0):
    return CostModel("ES", 0.25, 12.5, fee, latency_ms, mult)


def l1(rows):
    """rows: (ms_after_T0, bid, ask)."""
    idx = pd.DatetimeIndex([T0 + pd.Timedelta(milliseconds=r[0]) for r in rows], name="ts_recv")
    return pd.DataFrame({"bid_px": [r[1] for r in rows], "ask_px": [r[2] for r in rows],
                         "bid_sz": 10, "ask_sz": 10}, index=idx)


def scripted(actions):
    """Strategy that submits market orders at given record numbers: {record_no: side}."""
    seen = {"n": 0}

    def strat(ts, rec, ctx):
        side = actions.get(seen["n"])
        if side:
            ctx.market(side)
        seen["n"] += 1
    return strat


def test_costs_from_config():
    c = load_costs("ES")
    assert c.fee_per_side == pytest.approx(2.255) and c.tick_value == 12.5 and c.latency_ms == 100
    assert load_costs("ES", fee_multiplier=1.5).fee(2) == pytest.approx(2 * 2.255 * 1.5)


def test_round_trip_fee_arithmetic():
    # buy at the 5000.25 ask, sell at the 5001.25 bid: +4 ticks = $50 gross, minus 2 x $2.255
    data = l1([(0, 5000.00, 5000.25), (500, 5000.00, 5000.25), (1000, 5001.25, 5001.50),
               (1500, 5001.25, 5001.50)])
    res = run(data, scripted({0: 1, 2: -1}), costs(latency_ms=100))
    t = res.trades.iloc[0]
    assert (t.entry_px, t.exit_px, t.ticks) == (5000.25, 5001.25, 4.0)
    assert t.gross_pnl == pytest.approx(50.0) and t.net_pnl == pytest.approx(50.0 - 4.51)


def test_market_order_fills_at_book_after_latency_not_at_signal():
    # the ask jumps 2 ticks 50 ms after the signal; with 100 ms latency we pay the new ask
    data = l1([(0, 5000.00, 5000.25), (50, 5000.50, 5000.75), (200, 5000.50, 5000.75), (300, 5000.50, 5000.75)])
    slow = run(data, scripted({0: 1}), costs(latency_ms=100))
    assert slow.fills.iloc[0].price == 5000.75 and slow.fills.iloc[0].fill_ts == data.index[2]
    # negative control: zero latency fills on the very next record (still never at the signal record)
    fast = run(data, scripted({0: 1}), costs(latency_ms=0))
    assert fast.fills.iloc[0].fill_ts == data.index[1]


def test_book_at_arrival_takes_the_worse_side():
    # arrival (100 ms) falls between a record with ask 5000.75 and one with ask 5000.50:
    # the book at arrival is unknown in between, so a buy pays the higher ask
    data = l1([(0, 5000.00, 5000.25), (80, 5000.50, 5000.75), (150, 5000.25, 5000.50), (300, 5000.25, 5000.50)])
    res = run(data, scripted({0: 1}), costs(latency_ms=100))
    assert res.fills.iloc[0].price == 5000.75


def test_strategy_never_sees_future_records():
    data = l1([(k * 10, 5000.0 + k * 0.25, 5000.25 + k * 0.25) for k in range(50)])
    seen = []

    def spy(ts, rec, ctx):
        seen.append((ts, rec.bid_px))
    run(data, spy, costs())
    assert [s[0] for s in seen] == list(data.index)                # one record at a time, in order
    assert [s[1] for s in seen] == list(data["bid_px"])            # the record handed over is the current one


def test_position_limit_rejects_extra_orders():
    data = l1([(k * 200, 5000.00, 5000.25) for k in range(6)])
    res = run(data, scripted({0: 1, 1: 1, 3: -1, 4: -1}), costs(), max_position=1)
    assert list(res.fills.side) == [1, -1, -1, 1]                   # 2nd buy rejected; short allowed, flattened
    assert len(res.rejected) == 1 and res.rejected.iloc[0].reason == "position_limit"
    assert bool(res.fills.iloc[-1].end_flatten)


def test_open_position_is_flattened_conservatively_and_unarrived_orders_dropped():
    data = l1([(0, 5000.00, 5000.25), (500, 5001.00, 5001.25), (550, 5001.00, 5001.25)])
    res = run(data, scripted({0: 1, 2: -1}), costs(latency_ms=100))  # exit order never arrives
    assert len(res.fills) == 2 and res.fills.iloc[1].price == 5001.00 and res.fills.iloc[1].end_flatten
    # entry: arrival at 100 ms lies between asks 5000.25 and 5001.25 -> pays 5001.25 (worse side)
    assert res.trades.iloc[0].entry_px == 5001.25 and res.trades.iloc[0].ticks == -1.0


def test_l1_from_tbbo_renames_columns():
    tb = pd.DataFrame({"bid_px_00": [1.0], "ask_px_00": [1.25], "bid_sz_00": [3], "ask_sz_00": [4],
                       "price": [1.25], "size": [1], "side": ["A"], "other": [0]})
    assert list(l1_from_tbbo(tb).columns) == ["bid_px", "ask_px", "bid_sz", "ask_sz", "price", "size", "side"]
