import numpy as np
import pandas as pd

from portfolio.combine import combine, erc_weights


def sleeves(n=600, seed=0, vols=(0.01, 0.02, 0.04), corr=0.0):
    rng = np.random.default_rng(seed)
    k = len(vols)
    c = np.full((k, k), corr) + (1 - corr) * np.eye(k)
    z = rng.multivariate_normal(np.zeros(k), c, size=n)
    idx = pd.bdate_range("2015-01-01", periods=n)
    return pd.DataFrame(z * np.array(vols) * 1e6, index=idx, columns=[f"s{i}" for i in range(k)])


def test_erc_equalises_risk_contributions():
    cov = np.array([[0.04, 0.006, 0.0], [0.006, 0.01, 0.002], [0.0, 0.002, 0.0025]])
    w = erc_weights(cov)
    rc = w * (cov @ w)
    assert np.isclose(w.sum(), 1) and np.allclose(rc, rc.mean(), rtol=1e-4)


def test_inverse_vol_weights_are_proportional_to_one_over_sigma():
    s = sleeves()
    out = combine(s, 1e6, method="inverse_vol")
    w = out[["w_s0", "w_s1", "w_s2"]].iloc[-1].to_numpy()
    assert w[0] > w[1] > w[2] and np.isclose(w[0] / w[2], 4, rtol=0.25)


def test_weights_are_causal():
    s = sleeves()
    a = combine(s, 1e6)
    s2 = s.copy()
    s2.iloc[400:] *= 10                                   # change the future
    b = combine(s2, 1e6)
    cols = ["w_s0", "w_s1", "w_s2", "scale"]
    # weights on day 400 use rows < 400 only, so they cannot change
    assert np.allclose(a[cols].iloc[:401].fillna(0), b[cols].iloc[:401].fillna(0))


def test_book_hits_target_vol_and_warmup_is_flat():
    s = sleeves(n=1500)
    out = combine(s, 1e6, target_vol=0.10)
    assert (out["net"].iloc[:126] == 0).all()
    realised = out["net"].iloc[300:].std() * np.sqrt(252) / 1e6
    assert abs(realised - 0.10) < 0.02
