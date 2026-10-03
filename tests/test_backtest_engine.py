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


# ----------------------------------------------------------------------- R3.2 limit / stop / cancel
def l1t(rows):
    """rows: (ms, bid, ask, bid_sz, ask_sz, trade_px, trade_sz)."""
    idx = pd.DatetimeIndex([T0 + pd.Timedelta(milliseconds=r[0]) for r in rows], name="ts_recv")
    return pd.DataFrame({"bid_px": [r[1] for r in rows], "ask_px": [r[2] for r in rows],
                         "bid_sz": [r[3] for r in rows], "ask_sz": [r[4] for r in rows],
                         "price": [r[5] for r in rows], "size": [r[6] for r in rows]}, index=idx)


def once(action):
    """Run `action(ctx)` on the first record only."""
    done = {"x": False}

    def strat(ts, rec, ctx):
        if not done["x"]:
            done["x"] = True
            action(ctx)
    return strat


# buy limit at 5000.00 (the bid, 10 lots displayed)
BOOK = [(0, 5000.00, 5000.25, 10, 10, 5000.25, 1),
        (200, 5000.00, 5000.25, 10, 10, 5000.00, 4),     # 4 trade AT our price
        (300, 5000.00, 5000.25, 6, 10, 5000.00, 7),      # 7 more at our price -> queue of 10 consumed
        (400, 4999.75, 5000.00, 10, 3, 4999.75, 2),      # trade THROUGH our price
        (500, 4999.75, 5000.00, 10, 3, 5000.00, 1)]


def test_trade_through_needs_a_print_strictly_through_the_limit():
    res = run(l1t(BOOK), once(lambda c: c.limit(1, 5000.00)), costs(), fill_mode="trade_through")
    f = res.fills.iloc[0]
    assert f.fill_ts == T0 + pd.Timedelta(milliseconds=400) and f.price == 5000.00 and f.liquidity == "maker"


def test_queue_l1_fills_after_the_queue_ahead_trades():
    res = run(l1t(BOOK), once(lambda c: c.limit(1, 5000.00)), costs(), fill_mode="queue_l1")
    # queue ahead = 10 displayed at arrival; 4 + 7 = 11 traded at our price -> filled at 300 ms
    assert res.fills.iloc[0].fill_ts == T0 + pd.Timedelta(milliseconds=300)
    assert res.fills.iloc[0].price == 5000.00


def test_marketable_limit_fills_as_taker_within_the_limit_only():
    ok = run(l1t(BOOK), once(lambda c: c.limit(1, 5000.25)), costs())
    assert ok.fills.iloc[0].liquidity == "taker" and ok.fills.iloc[0].price == 5000.25
    # negative control: optimistic touch fills are not offered at all
    with pytest.raises(ValueError):
        run(l1t(BOOK), once(lambda c: c.limit(1, 5000.00)), costs(), fill_mode="optimistic")


def test_stop_triggers_on_trade_and_fills_at_worse_book():
    rows = [(0, 5000.00, 5000.25, 10, 10, 5000.25, 1),
            (200, 5000.25, 5000.50, 10, 10, 5000.50, 1),   # trade at 5000.50 = buy stop price -> trigger
            (210, 5000.50, 5000.75, 10, 10, 5000.75, 1),
            (300, 5000.50, 5000.75, 10, 10, 5000.75, 1)]
    res = run(l1t(rows), once(lambda c: c.stop(1, 5000.50)), costs())
    f = res.fills.iloc[0]
    assert f.kind == "stop" and f.price == 5000.75                  # worse of 5000.50 / 5000.75 ask
    # a stop that is never touched does not fill
    assert len(run(l1t(rows), once(lambda c: c.stop(1, 5001.00)), costs()).fills) == 0


def test_order_can_fill_while_its_cancel_is_in_flight():
    # cancel sent at 300 ms arrives at 400 ms, the instant of the through-trade: the fill wins
    res = run(l1t(BOOK), _cancel_strat(), costs(latency_ms=100), fill_mode="trade_through")
    assert len(res.fills) == 2 and res.fills.iloc[0].fill_ts == T0 + pd.Timedelta(milliseconds=400)
    # negative control: with a 50 ms latency the cancel lands at 350 ms, before the through-trade
    res2 = run(l1t(BOOK), _cancel_strat(), costs(latency_ms=50), fill_mode="trade_through")
    assert len(res2.fills) == 0 and res2.cancelled == 1


def _cancel_strat():
    st = {"o": None, "n": 0}

    def strat(ts, rec, ctx):
        if st["n"] == 0:
            st["o"] = ctx.limit(1, 5000.00)
        elif st["n"] == 2:
            ctx.cancel(st["o"])
        st["n"] += 1
    return strat


def test_bracket_orders_fit_the_position_limit():
    st = {"n": 0}

    def strat(ts, rec, ctx):
        if st["n"] == 0:
            ctx.market(1)
        elif st["n"] == 1 and ctx.position == 1:
            assert ctx.stop(-1, 4999.00) is not None and ctx.limit(-1, 5001.00) is not None
            assert ctx.market(1) is None                  # would make the worst case 2 long
        st["n"] += 1
    run(l1t(BOOK), strat, costs(latency_ms=100))


def test_l1_from_trades_rebuilds_quotes_from_aggressor_prints():
    from backtest.engine import l1_from_trades
    idx = pd.DatetimeIndex([T0 + pd.Timedelta(milliseconds=k) for k in range(5)])
    tr = pd.DataFrame({"price": [5000.25, 5000.00, 5000.25, 5000.50, 5000.25],
                       "side": ["B", "A", "B", "B", "A"], "size": [1] * 5}, index=idx)
    q = l1_from_trades(tr)
    # quote at each trade uses only EARLIER prints (no lookahead)
    assert np.isnan(q.ask_px.iloc[0]) and np.isnan(q.bid_px.iloc[0])
    assert (q.bid_px.iloc[2], q.ask_px.iloc[2]) == (5000.00, 5000.25)
    assert (q.bid_px.iloc[4], q.ask_px.iloc[4]) == (5000.00, 5000.50)
    tr2 = tr.copy(); tr2.loc[idx[3], "price"] = 5000.00            # lift at 5000.00 after a sell at 5000.00
    q2 = l1_from_trades(tr2)
    assert q2.ask_px.iloc[4] > q2.bid_px.iloc[4]                     # never crossed/locked
