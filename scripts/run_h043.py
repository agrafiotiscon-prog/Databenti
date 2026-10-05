"""H-043: mid-month coupon reinvestment in Treasury futures (long T-1..T+1 around the 15th). Single evaluation.

  python scripts/run_h043.py [--coverage-only]
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backtest.costs import load_costs                      # noqa: E402
from data.holdout import check as holdout_check             # noqa: E402
from data.universe import BY_ROOT, Spec                     # noqa: E402
from portfolio.data import build, load_bars                 # noqa: E402
from research import registry, trials                       # noqa: E402
from research.daily_eval import Outright, window_pnl        # noqa: E402
from scripts.fetch_futures_daily import path_for            # noqa: E402
from scripts.run_h001 import md                             # noqa: E402
from scripts.run_r9 import by_month                         # noqa: E402

HYP, NOTIONAL = "H-043", 250_000.0
SPECS = {**{r: BY_ROOT[r] for r in ("ZT", "ZF", "ZN", "ZB")},
         "TN": Spec("TN", "rates", 1000, 1 / 64), "UB": Spec("UB", "rates", 1000, 1 / 32)}
FIRST = {"TN": date(2016, 1, 11)}


def anchors(m: Outright) -> list[int]:
    """Position of T = first trading day on/after the 15th, per month (needs room for T-2 and T+1)."""
    out = []
    for ds in by_month(m.dates).values():
        t = [d for d in ds if d.day >= 15]
        if t:
            i = m.pos_i[t[0]]
            if i - 2 >= 0 and i + 1 < len(m.dates):
                out.append(i)
    return out


def windows(m: Outright, idx) -> list[tuple]:
    return [(m.dates[i - 2], m.dates[i + 1], 1) for i in idx]


def placebo_anchors(m: Outright, rng) -> list[int]:
    out = []
    for ds in by_month(m.dates).values():
        t = [k for k, d in enumerate(ds) if d.day >= 15]
        if not t or len(ds) < 14:
            continue
        a = t[0]
        ok = [k for k in range(2, len(ds) - 1) if abs(k - a) >= 4 and (len(ds) - 1 - k) >= 4]
        if ok:
            out.append(m.pos_i[ds[int(rng.choice(ok))]])
    return out


def main(argv=None) -> int:
    from data.download import Downloader
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--coverage-only", action="store_true")
    ap.add_argument("--draws", type=int, default=1000)
    a = ap.parse_args(argv)
    hyp = registry.load(HYP)
    if not a.coverage_only and (hyp.status != "open" or trials.count(hypothesis=HYP) >= hyp.trial_budget):
        raise SystemExit(f"{HYP}: closed or already evaluated (single evaluation).")
    dl = Downloader()
    fee = load_costs().fee(1)
    M = {}
    cov = []
    for r, sp in SPECS.items():
        v0, v1 = (load_bars(path_for(dl, f"{r}.v.{k}")) for k in (0, 1))
        if r in FIRST:
            v0, v1 = v0[v0.index >= FIRST[r]], v1[v1.index >= FIRST[r]]
        rd = build(r, v0, v1)
        holdout_check(rd.dates)
        m = Outright(rd, sp.point_value, sp.tick_value)
        M[r] = m
        idx = anchors(m)
        cov.append({"market": r, "first": m.dates[0], "last": m.dates[-1], "months": len(by_month(m.dates)),
                    "windows": len(idx), "anchor_day_mean": round(float(np.mean([m.dates[i].day for i in idx])), 2)})
    cov = pd.DataFrame(cov)
    print(cov.to_string(), flush=True)
    if a.coverage_only:
        return 0

    def run(idx_by, slip, fm):
        return pd.concat([window_pnl(M[r], windows(M[r], idx_by[r]), NOTIONAL, slip, fee * fm)[0] for r in M],
                         axis=1).sum(axis=1, min_count=1).fillna(0.0)

    A = {r: anchors(m) for r, m in M.items()}
    base, stress = run(A, 1.0, 1.0), run(A, 2.0, 1.5)
    rows = []
    for r, m in M.items():
        net, _ = window_pnl(m, windows(m, A[r]), NOTIONAL, 1.0, fee)
        mean3 = pd.Series(m.r).rolling(3).sum().mean()
        for i in A[r]:
            ret = float(np.nansum(m.r[i - 1:i + 2]))
            rows.append({"market": r, "date": m.dates[i], "pnl": float(net.iloc[i - 2:i + 2].sum()),
                         "ret_bp": 1e4 * ret, "excess": ret - mean3})
    W = pd.DataFrame(rows)
    t_win = float(W["pnl"].mean() / W["pnl"].std() * np.sqrt(len(W)))
    t_ex = float(W["excess"].mean() / W["excess"].std() * np.sqrt(len(W)))
    rng = np.random.default_rng(43)
    sims = np.array([run({r: placebo_anchors(m, rng) for r, m in M.items()}, 1.0, 1.0).sum() for _ in range(a.draws)])
    p = float((sims >= base.sum()).mean())
    crit = {"stress_net_pos": bool(stress.sum() > 0), "t_window_ge_2": t_win >= 2, "t_drift_neutral_ge_2": t_ex >= 2,
            "placebo_p_le_0.05": p <= 0.05}
    verdict = "CONFIRMS" if all(crit.values()) else "DOES NOT CONFIRM"
    W["year"] = [d.year for d in W["date"]]
    yrs = W.groupby("year")["pnl"].sum().round(0)
    per = W.groupby("market").agg(windows=("pnl", "size"), net=("pnl", "sum"), mean_bp=("ret_bp", "mean"),
                                  win_rate=("pnl", lambda s: (s > 0).mean())).round(2)
    res = {"verdict": verdict, **crit, "windows": int(len(W)), "net": round(float(base.sum())),
           "net_stress": round(float(stress.sum())), "t_window": round(t_win, 3), "t_drift_neutral": round(t_ex, 3),
           "placebo_p": round(p, 4), "placebo_median": round(float(np.median(sims))),
           "years_positive": f"{int((yrs > 0).sum())}/{len(yrs)}"}
    trials.append({"family": HYP, "hypothesis": HYP, "params": {"variant": "fixed"},
                   "data": "ZT/ZF/ZN/ZB/TN/UB ohlcv-1d v.0/v.1 2010-06..2025-09", "fill_mode": "closes, 1 tick + fees",
                   "results": res})
    out = ROOT / "vault" / "results" / "h043-report.md"
    out.write_text("\n".join([
        "---", "type: result", f"date: {date.today().isoformat()}", "tags: [R13, H-043, rates, mid-month]", "---",
        f"# H-043 mid-month coupon reinvestment (long T-1..T+1 around the 15th): **{verdict}**", "",
        "Pre-registered (research/hypotheses/H-043.yaml, committed before the run): CONFIRMS only if stress net > 0, per-window "
        "t >= 2, drift-neutral t >= 2 and placebo p <= 0.05. $250k notional per market, 6 Treasury futures.", "",
        "## Coverage (before P&L)", md(cov, index=False), "", "## Result", "```", "\n".join(f"{k}: {v}" for k, v in res.items()),
        "```", "", "## Per market", md(per), "", "## By year (pooled $)", md(yrs.to_frame("net")), ""]) + "\n")
    print(res); print(per.to_string()); print(yrs.to_string()); print("saved", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
