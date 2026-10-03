"""Promotion gates G1-G12 (vault/05-anti-overfitting/methodology.md section 8; Phase 4, R4.4).

`evaluate(evidence)` returns one row per gate. Missing evidence is a FAIL, never a pass:
a candidate is promoted only when every gate was measured and passed.
"""
from __future__ import annotations

import pandas as pd

GATES = [
    ("G1", ">= 200 OOS trades", lambda e: e["oos_trades"] >= 200, ["oos_trades"]),
    ("G2", "OOS net > 0 at 1.5x fees and 250 ms", lambda e: e["oos_net_stress"] > 0, ["oos_net_stress"]),
    ("G3", "DSR >= 0.95 (raw N) and OOS mean-trade t >= 2", lambda e: e["dsr_raw"] >= 0.95 and e["oos_t"] >= 2,
     ["dsr_raw", "oos_t"]),
    ("G4", "PBO <= 0.10", lambda e: e["pbo"] <= 0.10, ["pbo"]),
    ("G5", "+-20% plateau test", lambda e: bool(e["plateau_pass"]), ["plateau_pass"]),
    ("G6", "not concentrated (red flags clear)", lambda e: not e["concentrated"], ["concentrated"]),
    ("G7", "positive in >= 60% of OOS years (>= 2 years)",
     lambda e: e["n_years"] >= 2 and e["years_positive_share"] >= 0.60, ["years_positive_share", "n_years"]),
    ("G8", "tier-B fill check does not flip the sign", lambda e: bool(e["tier_b_same_sign"]), ["tier_b_same_sign"]),
    ("G9", "MC 5th pct net > 0 and P(loss) <= 10% at 1.5x fees",
     lambda e: e["mc_net_p5"] > 0 and e["mc_p_loss"] <= 0.10, ["mc_net_p5", "mc_p_loss"]),
    ("G10", "cluster medoid; >= 70% of its cluster profitable; not an island",
     lambda e: bool(e["is_medoid"]) and e["cluster_share_profitable"] >= 0.70 and not e["island"],
     ["is_medoid", "cluster_share_profitable", "island"]),
    ("G11", "DSR >= 0.95 with cluster-based effective K", lambda e: e["dsr_k"] >= 0.95, ["dsr_k"]),
    # added session 6 (D-032, stricter only): long-only or calendar rules must beat random timing
    ("G12", "beats a placebo / random-timing benchmark (one-sided p <= 0.05)", lambda e: e["placebo_p"] <= 0.05,
     ["placebo_p"]),
]


def evaluate(evidence: dict) -> pd.DataFrame:
    rows = []
    for gid, desc, rule, keys in GATES:
        missing = [k for k in keys if evidence.get(k) is None]
        if missing:
            rows.append((gid, desc, "FAIL", f"not measured: {', '.join(missing)}"))
            continue
        ok = bool(rule(evidence))
        rows.append((gid, desc, "PASS" if ok else "FAIL", ", ".join(f"{k}={evidence[k]}" for k in keys)))
    return pd.DataFrame(rows, columns=["gate", "requirement", "result", "evidence"]).set_index("gate")


def promoted(table: pd.DataFrame) -> bool:
    return bool((table["result"] == "PASS").all())


def verdict(table: pd.DataFrame, evidence: dict) -> str:
    if promoted(table):
        return "promising (all gates passed on development data; next: one holdout test with the user's OK)"
    if (evidence.get("oos_trades") or 0) < 200 or (evidence.get("n_years") or 0) < 2:
        return "insufficient data"
    return "not promising"
