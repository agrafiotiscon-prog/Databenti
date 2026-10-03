"""The fast bracket path must agree with the reference event engine."""
import numpy as np
import pandas as pd
import pytest

from backtest.bracket import Day, simulate
from backtest.costs import CostModel
from backtest.engine import run

T0 = pd.Timestamp("2024-03-05 14:30:00", tz="UTC")
COSTS = CostModel("ES", 0.25, 12.5, 2.255, 100.0)


def random_l1(n=3000, seed=0):
    rng = np.random.default_rng(seed)
    mid = 5000 + np.cumsum(rng.choice([-0.25, 0, 0.25], n, p=[0.3, 0.4, 0.3]))
    bid = np.round(mid / 0.25) * 0.25
    ask = bid + 0.25 * rng.choice([1, 2], n, p=[0.9, 0.1])
    side = rng.choice([1, -1], n)
    px = np.where(side > 0, ask, bid)
    t = T0 + pd.to_timedelta(np.cumsum(rng.exponential(250, n)).astype(int), unit="ms")
    return pd.DataFrame({"bid_px": bid, "ask_px": ask, "bid_sz": 0.0, "ask_sz": 0.0, "price": px,
                         "size": 1.0}, index=pd.DatetimeIndex(t))


@pytest.mark.parametrize("seed", range(6))
def test_fast_path_matches_engine_entry_and_exit(seed):
    l1 = random_l1(seed=seed)
    day = Day.from_l1(l1)
    rng = np.random.default_rng(100 + seed)
    for _ in range(5):
        i = int(rng.integers(50, 1500))
        known = l1.index[i]
        side = int(rng.choice([1, -1]))
        exit_at = known + pd.Timedelta("120s")
        fast = simulate(day, known.value, side, 6, 6, exit_at.value, COSTS)
        # reference: replay the engine with the entry price taken from the engine's own fill
        res = _engine_reference(l1, known, side, 6, 6, exit_at)
        assert fast is not None and res is not None
        assert fast["entry_px"] == res["entry_px"]
        assert fast["exit_px"] == res["exit_px"], (seed, i, fast, res)
        assert fast["reason"] == res["reason"]


def _engine_reference(l1, known, side, stop, target, exit_at):
    """Engine run with the bracket placed from the actual engine fill price."""
    st = {"phase": 0, "orders": [], "entry": None}

    def strat(ts, rec, ctx):
        if st["phase"] == 0 and ts >= known:
            ctx.market(side); st["phase"] = 1
        elif st["phase"] == 1 and ctx.position == side:
            entry = st["entry"]
            st["orders"] = [ctx.stop(-side, entry - side * stop * 0.25, tag="stop"),
                            ctx.limit(-side, entry + side * target * 0.25, tag="target")]
            st["phase"] = 2
        elif st["phase"] == 2 and ctx.position == 0:
            ctx.pending.clear(); st["phase"] = 3
        elif st["phase"] == 2 and ts >= exit_at:
            st["phase"] = 4
            st["time_order"] = ctx.market(-side, tag="time")
        elif st["phase"] == 4 and ctx.position == 0:
            ctx.pending.clear(); st["phase"] = 3

    # first pass: learn the entry price the engine gives
    def entry_only(ts, rec, ctx):
        if st["phase"] == 0 and ts >= known:
            ctx.market(side); st["phase"] = 1
    r0 = run(l1, entry_only, COSTS, max_position=2)
    st["entry"] = float(r0.fills.iloc[0].price)
    st["phase"] = 0
    r = run(l1, strat, COSTS, max_position=2)
    f = r.fills
    exit_row = f.iloc[1]
    reason = {"stop": "stop", "target": "target", "time": "time", "end_flatten": "time"}[exit_row.tag]
    return {"entry_px": float(f.iloc[0].price), "exit_px": float(exit_row.price), "reason": reason}


def test_equivalence_covers_all_exit_reasons():
    reasons = set()
    for seed in range(6):
        l1 = random_l1(seed=seed)
        day = Day.from_l1(l1)
        rng = np.random.default_rng(100 + seed)
        for _ in range(5):
            known = l1.index[int(rng.integers(50, 1500))]
            side = int(rng.choice([1, -1]))
            for stop, target, secs in ((6, 6, 120), (40, 40, 20)):
                fast = simulate(day, known.value, side, stop, target, (known + pd.Timedelta(seconds=secs)).value, COSTS)
                ref = _engine_reference(l1, known, side, stop, target, known + pd.Timedelta(seconds=secs))
                assert (fast["entry_px"], fast["exit_px"], fast["reason"]) == \
                       (ref["entry_px"], ref["exit_px"], ref["reason"])
                reasons.add(fast["reason"])
    assert reasons == {"stop", "target", "time"}
