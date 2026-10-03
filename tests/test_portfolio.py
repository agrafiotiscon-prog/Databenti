from datetime import date

import numpy as np
import pandas as pd

from portfolio.data import RootData, carry_sign, chain_returns
from portfolio.engine import prepare, simulate


def make_root(root="ES", n=400, roll_at=200, drift=0.0005, seed=0, jump=10.0):
    """Two instruments: 1 is held before roll_at, 2 after; 2 trades `jump` points above 1 (contango)."""
    rng = np.random.default_rng(seed)
    days = [d.date() for d in pd.bdate_range("2015-01-02", periods=n)]
    px1 = 4000 * np.cumprod(1 + drift + rng.normal(0, 0.01, n))
    c1 = pd.Series(px1, index=days)
    c2 = c1 + jump
    held = pd.Series([1 if i < roll_at else 2 for i in range(n)], index=days)
    nxt = pd.Series([2 if i < roll_at else 1 for i in range(n)], index=days)
    return RootData(root, days, held, nxt, {1: c1, 2: c2}, {1: (date(2015, 1, 1),), 2: (date(2016, 1, 1),)})


def test_chain_returns_stay_on_one_instrument_across_the_roll():
    rd = make_root()
    r = chain_returns(rd)
    d = rd.dates
    # day 200: held at 199 is instrument 1 -> its return, not the 10-point jump into instrument 2
    assert np.isclose(r[d[200]], rd.closes[1][d[200]] / rd.closes[1][d[199]] - 1)
    assert np.isclose(r[d[201]], rd.closes[2][d[201]] / rd.closes[2][d[200]] - 1)


def test_carry_uses_expiry_order_not_volume_rank():
    rd = make_root()
    c = carry_sign(rd)
    # far (instrument 2) is 10 points higher -> contango -> carry -1, before and after the volume roll
    assert (c.iloc[1:] == -1).all()


def test_positions_are_causal_and_lagged():
    rd = make_root()
    preps = [prepare(rd)]
    base = simulate(preps, "trend126", 1e6, 1.0, 2.26, detail=True)
    rd2 = make_root()
    j = 330
    for i in (1, 2):                                    # change the future after day j
        s = rd2.closes[i].copy()
        s.iloc[j + 1:] = s.iloc[j + 1:] * 0.5
        rd2.closes[i] = s
    alt = simulate([prepare(rd2)], "trend126", 1e6, 1.0, 2.26, detail=True)
    # P&L and trades up to day j+1 can only depend on data up to day j
    a, b = base.iloc[: j + 1], alt.iloc[: j + 1]
    assert np.allclose(a["contracts"], b["contracts"]) and np.allclose(a["gross"], b["gross"])


def test_roll_pays_both_legs():
    rd = make_root(drift=0.002)                          # strong uptrend -> long and steady
    df = simulate([prepare(rd)], "trend126", 1e6, 1.0, 2.26, detail=True).set_index("date")
    d = rd.dates
    pos_before = df["contracts"].iloc[150:199]
    roll = df.loc[d[200], "contracts"]
    assert roll >= 2 * 1 and roll > pos_before.median()  # closing old + opening new, not just the change
    assert (df["costs"] >= 0).all()
