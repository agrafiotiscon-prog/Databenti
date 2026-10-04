import numpy as np
import pandas as pd

from research.placebo import random_timing_nets


def test_random_timing_keeps_sides_durations_and_bounds():
    t0 = pd.Timestamp("2025-03-04 14:30", tz="UTC")
    trades = pd.DataFrame({"entry_ts": [t0, t0 + pd.Timedelta(hours=1)],
                           "exit_ts": [t0 + pd.Timedelta(minutes=30), t0 + pd.Timedelta(hours=1, minutes=15)],
                           "side": [1, -1], "trading_date": ["d1", "d1"]})
    lo, hi = t0.value, (t0 + pd.Timedelta(hours=6)).value
    seen = []

    def sim(day, t, side, t_exit):
        seen.append((t, side, t_exit))
        return float(side)

    nets = random_timing_nets(trades, ["d1"], lambda d: None, lambda d: (lo, hi), sim, n_draws=50, seed=1)
    assert np.allclose(nets, 0.0)                         # +1 and -1 per draw
    durs = sorted({e - t for t, _, e in seen})
    assert durs == [15 * 60 * 10**9, 30 * 60 * 10**9]
    assert all(lo <= t and e <= hi for t, _, e in seen)
    assert len({t for t, _, _ in seen}) > 50              # timing really is redrawn
