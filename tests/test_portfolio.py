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


def test_cross_sectional_ranks_within_sector_and_ignores_missing():
    from portfolio.signals import cross_sectional
    idx = [date(2020, 1, d) for d in (2, 3)]
    sc = {"ES": pd.Series([3.0, 1.0], index=idx), "NQ": pd.Series([2.0, np.nan], index=idx),
          "RTY": pd.Series([1.0, 2.0], index=idx), "YM": pd.Series([0.0, 3.0], index=idx),
          "CL": pd.Series([9.0, 9.0], index=idx)}            # alone in its sector -> always 0
    out = cross_sectional(sc, by_sector=True, frac=0.25, min_names=3)
    # day 1: 4 equity names, k = 1 -> ES long, YM short
    assert [out[r][idx[0]] for r in ("ES", "NQ", "RTY", "YM")] == [1.0, 0.0, 0.0, -1.0]
    # day 2: 3 valid names, k = floor(0.75) = 0 -> nobody positioned
    assert all(out[r][idx[1]] == 0.0 for r in ("ES", "NQ", "RTY", "YM"))
    assert (out["CL"] == 0).all()


def test_momentum_score_is_causal():
    from portfolio.signals import momentum_score
    p = prepare(make_root())
    s = momentum_score(p, 20, skip=5)
    r2 = p.r.copy()
    r2.iloc[300:] = 0.05                                     # change the future
    p2 = prepare(make_root())
    p2.r = r2
    s2 = momentum_score(p2, 20, skip=5)
    assert np.allclose(s.iloc[:300].fillna(0), s2.iloc[:300].fillna(0))


def test_carry_value_sign_and_annualisation():
    from portfolio.signals import carry_value, expiry_spacing_years
    rd = make_root(jump=40.0)                                 # far 40 points above near -> contango, negative carry
    c = carry_value(rd)
    sp = expiry_spacing_years(rd)
    d = rd.dates[10]
    assert c[d] < 0
    assert np.isclose(c[d], np.log(rd.closes[1][d] / rd.closes[2][d]) / sp)


def test_h024_builder_returns_all_registered_variants():
    from portfolio.signals import BUILDERS
    preps = [prepare(make_root(root=r, seed=i, jump=5.0 * (i - 2))) for i, r in enumerate(("ES", "NQ", "RTY", "YM"))]
    out = BUILDERS["H-024"](preps)
    assert set(out) == {"xsc_sector", "xsc_global", "xsc_sector_smooth", "xsc_global_smooth"}
    d = preps[0].dates[100]
    # 4 equity names, k = 1: largest carry (most backwardated: negative jump) long, most contango short
    assert out["xsc_sector"]["ES"][d] == 1.0 and out["xsc_sector"]["YM"][d] == -1.0


def test_h025_builder_ranks_winners_long():
    from portfolio.signals import BUILDERS
    drifts = (0.006, 0.002, -0.002, -0.006)                 # gaps far above the 1%/day noise over 252 days
    preps = [prepare(make_root(root=r, seed=i, drift=dr)) for i, (r, dr) in enumerate(zip(("ES", "NQ", "RTY", "YM"), drifts))]
    out = BUILDERS["H-025"](preps)
    assert set(out) == {"xsm126_sector", "xsm252_sector", "xsm126_global", "xsm252_global"}
    d = preps[0].dates[-1]
    assert out["xsm252_sector"]["ES"][d] == 1.0 and out["xsm252_sector"]["YM"][d] == -1.0
    assert out["xsm252_sector"]["ES"].iloc[:200].eq(0).all()        # warm-up: 80% of 252 + 21 skip


def test_basis_momentum_sign_and_commodity_only():
    from portfolio.signals import BUILDERS, basis_momentum
    # make the far (instrument 2) lag the near: scale its moves down -> near outperforms in an uptrend
    rd = make_root(root="CL", drift=0.003)
    rd.closes[2] = rd.closes[1] ** 0.8 * rd.closes[1].iloc[0] ** 0.2
    bm = basis_momentum(rd, 126)
    assert bm.iloc[150] > 0
    preps = [prepare(rd), prepare(make_root(root="ES"))]
    out = BUILDERS["H-026"](preps)
    assert set(out) == {"tsbm126", "tsbm252", "xsbm126", "xsbm252"}
    assert (out["tsbm126"]["ES"] == 0).all() and out["tsbm126"]["CL"].iloc[150] == 1.0
