"""H-032: confirmation of H-030 (long into month-end) on TN and UB, never used before. Single evaluation.

  python scripts/run_h032.py [--coverage-only]
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
from data.universe import Spec                              # noqa: E402
from portfolio.data import build, load_bars                 # noqa: E402
from research import registry, trials                       # noqa: E402
from research.daily_eval import Outright, window_pnl        # noqa: E402
from scripts.fetch_futures_daily import path_for            # noqa: E402
from scripts.run_h001 import md                             # noqa: E402
from scripts.run_r9 import by_month                         # noqa: E402

HYP, K, NOTIONAL = "H-032", 3, 250_000.0
SPECS = {"TN": Spec("TN", "rates", 1000, 1 / 64), "UB": Spec("UB", "rates", 1000, 1 / 32)}
# registry: "TN from its 2016 listing" - the 2010-2012 bars under the TN root are a different, illiquid product
# (median daily volume 9-1,392 contracts vs 50k+ from 2016)
FIRST = {"TN": date(2016, 1, 11), "UB": date(2010, 6, 7)}


def pre_windows(m: Outright, anchors) -> list[tuple]:
    out = []
    for a in anchors:
        i = m.pos_i.get(a)
        if i is not None and i - K >= 0:
            out.append((m.dates[i - K], a, 1))
    return out


def window_returns(m: Outright, windows) -> np.ndarray:
    return np.array([np.nansum(m.r[m.pos_i[s] + 1:m.pos_i[e] + 1]) for s, e, _ in windows])


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
    M, ME = {}, {}
    cov = []
    for r, spec in SPECS.items():
        v0, v1 = (load_bars(path_for(dl, f"{r}.v.{k}")) for k in (0, 1))
        v0, v1 = v0[v0.index >= FIRST[r]], v1[v1.index >= FIRST[r]]
        rd = build(r, v0, v1)
        holdout_check(rd.dates)
        m = Outright(rd, spec.point_value, spec.tick_value)
        months = by_month(rd.dates)
        me = sorted(ds[-1] for ds in months.values())
        M[r], ME[r] = m, me
        cov.append({"market": r, "first": rd.dates[0], "last": rd.dates[-1], "days": len(rd.dates),
                    "month_ends": len(me), "windows": len(pre_windows(m, me)),
                    "returns_ok": round(float(np.isfinite(m.r[1:]).mean()), 4),
                    "median_close": round(float(np.nanmedian(m.px)), 3)})
    cov = pd.DataFrame(cov)
    print(cov.to_string(), flush=True)
    if a.coverage_only:
        return 0

    def pooled(anchors_by_mkt, slip, fm):
        return pd.concat([window_pnl(M[r], pre_windows(M[r], anchors_by_mkt[r]), NOTIONAL, slip, fee * fm)[0]
                          for r in SPECS], axis=1).sum(axis=1, min_count=1).fillna(0.0)

    base, stress = pooled(ME, 1.0, 1.0), pooled(ME, 2.0, 1.5)
    # per-window P&L (pooled over markets) and drift-neutral excess returns
    win_pnl, excess, rows = [], [], []
    for r in SPECS:
        m = M[r]
        w = pre_windows(m, ME[r])
        net, _ = window_pnl(m, w, NOTIONAL, 1.0, fee)
        rr = window_returns(m, w)
        all3 = pd.Series(m.r).rolling(K).sum().dropna().to_numpy()
        ex = rr - all3.mean()
        excess += list(ex)
        for (s, e, _), x in zip(w, rr):
            pnl = float(net.iloc[m.pos_i[s]:m.pos_i[e] + 1].sum())
            win_pnl.append(pnl)
            rows.append({"market": r, "month_end": e, "ret_bp": x * 1e4, "pnl": pnl})
    win_pnl, excess = np.array(win_pnl), np.array(excess)
    t_win = float(win_pnl.mean() / win_pnl.std() * np.sqrt(len(win_pnl)))
    t_ex = float(excess.mean() / excess.std() * np.sqrt(len(excess)))
    rng = np.random.default_rng(32)
    sims = []
    for _ in range(a.draws):
        anchors = {r: [ds[int(rng.integers(5, len(ds) - 6))] for ds in by_month(M[r].dates).values() if len(ds) >= 14]
                   for r in SPECS}
        sims.append(float(pooled(anchors, 1.0, 1.0).sum()))
    sims = np.array(sims)
    p = float((sims >= base.sum()).mean())
    crit = {"stress_net_pos": bool(stress.sum() > 0), "t_window_ge_2": t_win >= 2, "t_drift_neutral_ge_2": t_ex >= 2,
            "placebo_p_le_0.05": p <= 0.05}
    verdict = "CONFIRMS" if all(crit.values()) else "DOES NOT CONFIRM"
    W = pd.DataFrame(rows)
    W["year"] = [d.year for d in W["month_end"]]
    W["roll_month"] = [d.month in (2, 5, 8, 11) for d in W["month_end"]]
    per = W.groupby("market").agg(windows=("pnl", "size"), net=("pnl", "sum"), mean_bp=("ret_bp", "mean"),
                                  win_rate=("pnl", lambda s: (s > 0).mean())).round(2)
    yrs = W.groupby("year")["pnl"].sum().round(0)
    roll = W.groupby(["market", "roll_month"])["ret_bp"].agg(["size", "mean"]).round(2)
    res = {"verdict": verdict, **crit, "windows": int(len(win_pnl)), "net": round(float(base.sum())),
           "net_stress": round(float(stress.sum())), "t_window": round(t_win, 3), "t_drift_neutral": round(t_ex, 3),
           "placebo_p": round(p, 4), "placebo_median": round(float(np.median(sims))),
           "years_positive": f"{int((yrs > 0).sum())}/{len(yrs)}"}
    trials.append({"family": HYP, "hypothesis": HYP, "params": {"variant": "fixed"},
                   "data": "TN/UB ohlcv-1d v.0/v.1 2010-06..2025-09 (first use)", "fill_mode": "closes, 1 tick + fees per side",
                   "results": res})
    out = ROOT / "vault" / "results" / "h032-report.md"
    out.write_text("\n".join([
        "---", "type: result", f"date: {date.today().isoformat()}", "tags: [R9, H-032, H-030, confirmation]", "---",
        f"# H-032 confirmation of H-030 on TN/UB (never used before): **{verdict}**", "",
        "Pre-registered (research/hypotheses/H-032.yaml, committed before the data was downloaded): CONFIRMS only if stress net > 0, "
        "per-window t >= 2, drift-neutral t >= 2 and random-window placebo p <= 0.05. Rule: long 3 trading days into month-end, "
        "$250k notional per market.", "", "## Coverage (before P&L)", md(cov, index=False), "",
        "## Result", "```", "\n".join(f"{k}: {v}" for k, v in res.items()), "```", "",
        "## Per market", md(per), "", "## By year (pooled $)", md(yrs.to_frame("net")), "",
        "## Roll months (Feb/May/Aug/Nov) vs others: mean window return, bp", md(roll), ""]) + "\n")
    print(res); print(per.to_string()); print(yrs.to_string()); print(roll.to_string()); print("saved", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
