import json

import pytest
import yaml

from research import registry, trials

H = {"id": "H-900", "title": "test hypothesis", "direction": "fade", "horizon": "2-30 min",
     "mechanism": "Late aggressive buyers pay: after absorption at value-area high they are trapped and exit.",
     "features": ["absorption", "profile"], "space": {"stop": [4, 8], "target": [4, 8, 12]},
     "trial_budget": 4, "registered": "2026-10-03", "status": "open"}


@pytest.fixture
def env(tmp_path):
    d = tmp_path / "hyp"
    d.mkdir()
    (d / "H-900.yaml").write_text(yaml.safe_dump(H))
    return tmp_path / "trials.jsonl", d


def rec(params, hyp="H-900"):
    return {"family": "test", "hypothesis": hyp, "params": params, "data": "synthetic",
            "fill_mode": "trade_through", "results": {"net": -1.0}}


def test_registry_validates_mechanism_space_and_budget():
    h = registry.parse(H)
    assert h.space_size == 6 and len(list(h.grid())) == 6
    assert h.in_space({"stop": 4, "target": 12}) and not h.in_space({"stop": 5, "target": 12})
    for bad in ({**H, "mechanism": "it works"}, {**H, "trial_budget": 7}, {**H, "space": {"stop": []}},
                {k: v for k, v in H.items() if k != "mechanism"}, {**H, "direction": "up"}):
        with pytest.raises(registry.RegistryError):
            registry.parse(bad)


def test_append_enforces_space_and_budget(env):
    path, d = env
    for p in ({"stop": 4, "target": 4}, {"stop": 4, "target": 8}, {"stop": 8, "target": 4}, {"stop": 8, "target": 8}):
        trials.append(rec(p), path, d)
    with pytest.raises(trials.TrialError, match="budget"):
        trials.append(rec({"stop": 8, "target": 12}), path, d)
    with pytest.raises(trials.TrialError, match="outside"):
        trials.append(rec({"stop": 5, "target": 4}), path, d)
    with pytest.raises(registry.RegistryError):
        trials.append(rec({"stop": 4, "target": 4}, hyp="H-999"), path, d)       # unregistered
    assert trials.count(path, hypothesis="H-900") == 4 and trials.verify(path) == 4


def test_tampering_with_an_earlier_line_is_detected(env):
    path, d = env
    trials.append(rec({"stop": 4, "target": 4}), path, d)
    trials.append(rec({"stop": 4, "target": 8}), path, d)
    lines = path.read_text().splitlines()
    first = json.loads(lines[0]); first["results"]["net"] = 999.0             # make a loser look good
    path.write_text(json.dumps(first, sort_keys=True) + "\n" + lines[1] + "\n")
    with pytest.raises(trials.TrialError, match="broken"):
        trials.verify(path)
    path.write_text(lines[1] + "\n")                                           # delete the first line
    with pytest.raises(trials.TrialError):
        trials.verify(path)


def test_legacy_unchained_prefix_is_accepted_and_chain_continues(env):
    path, d = env
    path.write_text(json.dumps({"family": "engine-sanity", "hypothesis": "none (null baseline)"}) + "\n")
    r = trials.append({**rec({}, hyp="none"), "family": "engine-sanity"}, path, d)
    assert r["n"] == 1 and trials.verify(path) == 2


def test_real_trial_log_is_intact():
    assert trials.verify() >= 2
