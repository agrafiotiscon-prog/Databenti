"""H-040: confirmation of H-037 (FX month-end hedge rebalancing, rule k=5) on 6N and 6M. Single evaluation.

  python scripts/run_h040.py [--coverage-only]
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
from research import registry, trials                       # noqa: E402
from research.daily_eval import Outright, window_pnl        # noqa: E402
from scripts.run_h001 import md                             # noqa: E402
from scripts.run_r9 import by_month, load, month_end_index, random_month_anchors  # noqa: E402

HYP, K, NOTIONAL = "H-040", 5, 250_000.0
SPECS = {"6N": Spec("6N", "fx", 100_000, 0.00005), "6M": Spec("6M", "fx", 500_000, 0.00001)}


def events(es: Outright, k: int, anchors=None) -> list[tuple]:
    lr = pd.Series(np.log1p(es.r), index=es.dates)
    me = month_end_index(es)
    mes = [es.dates[i] for i in me]
    out = []
    for i in (anchors if anchors is not None else me):
        if i - k < 1:
            continue
        entry, exit_ = es.dates[i - k], es.dates[i]
        prev = [d for d in mes if d < entry]
        if not prev:
            continue
        eq = lr[(lr.index > prev[-1]) & (lr.index <= entry)].sum()
        if eq != 0 and not np.isnan(eq):
            out.append((entry, exit_, int(np.sign(eq))))
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
    es = Outright(load(dl, "ES"), BY_ROOT["ES"].point_value, BY_ROOT["ES"].tick_value)
    M = {}
    ev = events(es, K)
    cov = []
    for r, sp in SPECS.items():
        rd = load(dl, r)
        holdout_check(rd.dates)
        m = Outright(rd, sp.point_value, sp.tick_value)
        M[r] = m
        cov.append({"market": r, "first": m.dates[0], "last": m.dates[-1], "days": len(m.dates),
                    "events": sum(e[0] in m.pos_i and e[1] in m.pos_i for e in ev),
                    "returns_ok": round(float(np.isfinite(m.r[1:]).mean()), 4),
                    "median_close": round(float(np.nanmedian(m.px)), 5),
                    "contracts_at_median": max(1, round(NOTIONAL / (np.nanmedian(m.px) * sp.point_value)))})
    cov = pd.DataFrame(cov)
    print(cov.to_string(), flush=True)
    if a.coverage_only:
        return 0

    def run(evs, slip, fm):
        nets, wins = [], []
        for r, m in M.items():
            w = [e for e in evs if e[0] in m.pos_i and e[1] in m.pos_i]
            net, _ = window_pnl(m, w, NOTIONAL, slip, fee * fm)
            nets.append(net)
            wins += [(r, s, e, sd, float(net.iloc[m.pos_i[s]:m.pos_i[e] + 1].sum()),
                      float(np.nansum(m.r[m.pos_i[s] + 1:m.pos_i[e] + 1]))) for s, e, sd in w]
        return pd.concat(nets, axis=1).sum(axis=1), wins

    base, wins = run(ev, 1.0, 1.0)
    stress, _ = run(ev, 2.0, 1.5)
    W = pd.DataFrame(wins, columns=["market", "entry", "exit", "side", "pnl", "ret"])
    mean5 = {r: pd.Series(m.r).rolling(K).sum().mean() for r, m in M.items()}
    W["excess"] = W["side"] * (W["ret"] - W["market"].map(mean5))
    t_win = float(W["pnl"].mean() / W["pnl"].std() * np.sqrt(len(W)))
    t_ex = float(W["excess"].mean() / W["excess"].std() * np.sqrt(len(W)))
    rng = np.random.default_rng(40)
    sims = np.array([run(events(es, K, random_month_anchors(es, rng)), 1.0, 1.0)[0].sum() for _ in range(a.draws)])
    p = float((sims >= base.sum()).mean())
    crit = {"stress_net_pos": bool(stress.sum() > 0), "t_window_ge_2": t_win >= 2, "t_drift_neutral_ge_2": t_ex >= 2,
            "placebo_p_le_0.05": p <= 0.05}
    verdict = "CONFIRMS" if all(crit.values()) else "DOES NOT CONFIRM"
    W["year"] = [d.year for d in W["exit"]]
    yrs = W.groupby("year")["pnl"].sum().round(0)
    per = W.groupby("market").agg(windows=("pnl", "size"), net=("pnl", "sum"), win_rate=("pnl", lambda s: (s > 0).mean()),
                                  mean_excess_bp=("excess", lambda s: 1e4 * s.mean())).round(2)
    res = {"verdict": verdict, **crit, "windows": int(len(W)), "net": round(float(base.sum())),
           "net_stress": round(float(stress.sum())), "t_window": round(t_win, 3), "t_drift_neutral": round(t_ex, 3),
           "placebo_p": round(p, 4), "placebo_median": round(float(np.median(sims))),
           "years_positive": f"{int((yrs > 0).sum())}/{len(yrs)}"}
    trials.append({"family": HYP, "hypothesis": HYP, "params": {"variant": "fixed"},
                   "data": "6N/6M ohlcv-1d v.0/v.1 2010-06..2025-09 (first use) + ES signal", "fill_mode": "closes, 1 tick + fees",
                   "results": res})
    out = ROOT / "vault" / "results" / "h040-report.md"
    out.write_text("\n".join([
        "---", "type: result", f"date: {date.today().isoformat()}", "tags: [R11, H-040, H-037, confirmation]", "---",
        f"# H-040 confirmation of H-037 on 6N/6M (never used before): **{verdict}**", "",
        "Pre-registered (research/hypotheses/H-040.yaml, committed before the data was downloaded): CONFIRMS only if stress net > 0, "
        "per-window t >= 2, drift-neutral t >= 2 and placebo p <= 0.05. Rule: over the last 5 days of the month, long the "
        "foreign currency after a US equity rise month-to-date, short after a fall; $250k notional per market.", "",
        "## Coverage (before P&L)", md(cov, index=False), "", "## Result", "```", "\n".join(f"{k}: {v}" for k, v in res.items()), "```",
        "", "## Per market", md(per), "", "## By year (pooled $)", md(yrs.to_frame("net")), ""]) + "\n")
    print(res); print(per.to_string()); print(yrs.to_string()); print("saved", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
