import numpy as np
import pandas as pd
import pytest

from research import stats as S


def test_expected_max_sharpe_grows_with_trials_and_dsr_falls():
    assert S.expected_max_sharpe(0.01, 1) == 0.0
    assert S.expected_max_sharpe(0.01, 10) < S.expected_max_sharpe(0.01, 100) < S.expected_max_sharpe(0.01, 1000)
    rng = np.random.default_rng(0)
    daily = pd.Series(rng.normal(30, 300, 500))           # per-day SR ~ 0.1
    trial_srs = rng.normal(0, 0.05, 200)
    few, many = S.dsr(daily, trial_srs[:5]), S.dsr(daily, trial_srs, n_trials=10_000)
    assert 0 <= many < few <= 1


def test_dsr_of_the_best_of_many_noise_trials_is_low():
    # negative control: pick the best of 200 pure-noise strategies -> no evidence after deflation
    rng = np.random.default_rng(1)
    m = rng.normal(0, 100, (500, 200))
    srs = [S.per_period_sharpe(m[:, j]) for j in range(200)]
    best = int(np.argmax(srs))
    from backtest.metrics import probabilistic_sharpe
    assert probabilistic_sharpe(pd.Series(m[:, best])) > 0.9          # looks great undeflated
    assert S.dsr(pd.Series(m[:, best]), srs) < 0.5                    # deflated: nothing


def test_pbo_noise_is_about_half_and_real_edge_is_low():
    rng = np.random.default_rng(2)
    noise = pd.DataFrame(rng.normal(0, 1, (480, 20)))
    p_noise = S.pbo_cscv(noise, n_blocks=8)["pbo"]
    assert 0.25 < p_noise < 0.75
    edge = noise.copy()
    edge[0] = edge[0] + 0.5                                          # one trial really is better
    res = S.pbo_cscv(edge, n_blocks=8)
    assert res["pbo"] < 0.05 and res["n_combinations"] == 70


def test_plateau_test():
    assert S.plateau_test(100.0, [80, 90, 60, 120])["pass"]
    assert not S.plateau_test(100.0, [10, 20, 30, 40])["pass"]       # sharp peak
    assert not S.plateau_test(100.0, [80, 90, -5, 120])["pass"]      # a neighbour flips sign
    assert not S.plateau_test(-10.0, [-5, -8])["pass"]


def test_block_bootstrap_summary():
    rng = np.random.default_rng(3)
    good = pd.Series(rng.normal(50, 200, 400))
    bad = pd.Series(rng.normal(-50, 200, 400))
    g, b = S.block_bootstrap(good, n_sims=300), S.block_bootstrap(bad, n_sims=300)
    assert g["p_loss"] < 0.05 and g["net_p5"] > 0 and g["max_dd_p95"] <= 0
    assert b["p_loss"] > 0.95


def test_execution_mc_is_harsher_than_the_backtest():
    rng = np.random.default_rng(4)
    net = rng.normal(5, 40, 400)
    fees = np.full(400, 4.51)
    r = S.execution_mc(net, fees, n_sims=500)
    assert r["net_median"] < net.sum()                                # higher fees + missed trades
    r2 = S.execution_mc(net, fees, n_sims=500, slippage_usd=[0.0, 12.5])
    assert r2["net_median"] < r["net_median"]


def test_shuffle_keeps_total_but_varies_drawdown():
    net = np.array([10, -5, -5, -5, 20, -3, 8] * 20, float)
    r = S.shuffle_drawdown(net, n_sims=300)
    assert r["max_dd_p95"] < 0 and r["losing_streak_p95"] >= 3
