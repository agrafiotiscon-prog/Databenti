import numpy as np
import pandas as pd

from research import clusters as C
from research import gates as G


def test_clusters_recover_three_families_and_medoids():
    rng = np.random.default_rng(0)
    base = rng.normal(0, 1, (300, 3))
    cols = [base[:, f] + rng.normal(0, 0.3, 300) for f in (0, 0, 0, 0, 1, 1, 1, 2, 2, 2, 2, 2)]
    pnl = pd.DataFrame(np.column_stack(cols))
    res = C.cluster_trials(pnl)
    assert res["k"] == 3                                          # 12 variants, 3 independent ideas
    lab = res["labels"]
    assert len(set(lab[:4])) == 1 and len(set(lab[4:7])) == 1 and len(set(lab[7:])) == 1
    for c, m in res["medoids"].items():
        assert lab[m] == c


def test_independent_noise_trials_do_not_collapse():
    rng = np.random.default_rng(1)
    res = C.cluster_trials(pd.DataFrame(rng.normal(0, 1, (300, 6))))
    assert res["k"] >= 2                                          # no fake redundancy


def test_cluster_quality_flags_islands():
    labels = np.array([0, 0, 0, 1, 1, 1])
    q = C.cluster_quality(labels, np.array([5, 3, 1, 9, -4, -6.0]))
    assert bool(q.loc[0, "credible"]) and not bool(q.loc[1, "credible"])


GOOD = {"oos_trades": 350, "oos_net_stress": 1200.0, "dsr_raw": 0.97, "oos_t": 3.1, "pbo": 0.05,
        "plateau_pass": True, "concentrated": False, "years_positive_share": 0.75, "n_years": 4,
        "tier_b_same_sign": True, "mc_net_p5": 300.0, "mc_p_loss": 0.04, "is_medoid": True,
        "cluster_share_profitable": 0.8, "island": False, "dsr_k": 0.96}


def test_all_gates_pass_only_with_complete_evidence():
    t = G.evaluate(GOOD)
    assert G.promoted(t) and G.verdict(t, GOOD).startswith("promising")
    missing = {k: v for k, v in GOOD.items() if k != "tier_b_same_sign"}
    t2 = G.evaluate(missing)
    assert not G.promoted(t2) and t2.loc["G8", "result"] == "FAIL" and "not measured" in t2.loc["G8", "evidence"]


def test_one_year_of_data_is_insufficient_not_promising():
    e = {**GOOD, "n_years": 1, "years_positive_share": 1.0}
    t = G.evaluate(e)
    assert t.loc["G7", "result"] == "FAIL" and G.verdict(t, e) == "insufficient data"
    bad = {**GOOD, "pbo": 0.4}
    assert G.verdict(G.evaluate(bad), bad) == "not promising"
