"""Evaluate a registered hypothesis ONCE with the D-020 protocol and write its gate report.

  python scripts/run_hypothesis.py H-002 [--start 2024-11-01] [--end 2025-09-30] [--dry]

The strategy lives in strategies/<id lowercase without dash>.py (e.g. strategies/h002.py) and
provides KEYS, prepare_day(trades, date, state) and day_trades(day, feat, params, date, costs).
Uses only cached RTH trade chunks. Refuses to run if the hypothesis's trial budget has no room
for its whole grid (single evaluation). Logs every variant via research.trials.append after the
evaluation completes; report -> vault/results/<id>-report.md.
"""
from __future__ import annotations

import argparse
import importlib
import json
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backtest.bracket import Day                                    # noqa: E402
from backtest.costs import load_costs                               # noqa: E402
from backtest.engine import l1_from_trades                          # noqa: E402
from backtest.metrics import concentration, trade_stats             # noqa: E402
from data.loader import load_chunks, slice_session                  # noqa: E402
from research import clusters, gates, registry, stats, trials       # noqa: E402
from research.walkforward import walk_forward                       # noqa: E402
from scripts.run_h001 import cached_days, daily, md                 # noqa: E402

COLS = ["entry_ts", "exit_ts", "side", "entry_px", "exit_px", "reason", "gross_pnl", "fees", "net_pnl", "ticks",
        "trading_date"]


def neighbours(p: dict, space: dict) -> list[dict]:
    out = []
    for k, vals in space.items():
        i = vals.index(p[k])
        for j in (i - 1, i + 1):
            if 0 <= j < len(vals):
                out.append({**p, k: vals[j]})
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("hyp")
    ap.add_argument("--start", type=date.fromisoformat, default=date(2024, 11, 1))
    ap.add_argument("--end", type=date.fromisoformat, default=date(2025, 9, 30))
    ap.add_argument("--dry", action="store_true", help="pipeline test: no trial logging, report to --out")
    ap.add_argument("--schema-dir", default="trades-rth")
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args(argv)
    hyp = registry.load(a.hyp)
    mod = importlib.import_module("strategies." + a.hyp.lower().replace("-", ""))
    out_path = a.out or ROOT / "vault" / "results" / f"{a.hyp.lower()}-report.md"
    if not a.dry:
        if hyp.status != "open":
            raise SystemExit(f"{a.hyp} is {hyp.status}")
        used = trials.count(hypothesis=a.hyp)
        if used + hyp.space_size > hyp.trial_budget:
            raise SystemExit(f"{a.hyp}: {used} trials logged; no room for {hyp.space_size} more (single evaluation).")

    days = cached_days(a.start, a.end, a.schema_dir)
    dates = [d for d, _ in days]
    print(f"{a.hyp}: {len(days)} cached RTH days {dates[0]}..{dates[-1]}", flush=True)
    costs_map = {"base": load_costs(), "fees1.5": load_costs(fee_multiplier=1.5),
                 "fees1.5_lat250": load_costs(fee_multiplier=1.5, latency_ms=250),
                 "fees2_lat500": load_costs(fee_multiplier=2.0, latency_ms=500)}
    grid = list(hyp.grid())
    vid = lambda p: "_".join(f"{k}{p[k]}" for k in mod.KEYS)          # noqa: E731
    variants = [vid(p) for p in grid]
    res = {lab: {v: [] for v in variants} for lab in costs_map}
    state: dict = {}
    for k, (d, path) in enumerate(days):
        tr = slice_session(load_chunks([path]), d, rth_only=True)
        if tr.empty:
            continue
        feat = mod.prepare_day(tr, d, state)
        day = Day.from_l1(l1_from_trades(tr))
        for p in grid:
            for lab, c in costs_map.items():
                res[lab][vid(p)] += mod.day_trades(day, feat, p, d, c)
        if k % 40 == 0:
            print(f"  {k + 1}/{len(days)} days", flush=True)
    allres = {lab: {v: pd.DataFrame(t, columns=COLS) for v, t in r.items()} for lab, r in res.items()}
    D = {lab: pd.DataFrame({v: daily(allres[lab][v], dates) for v in variants}) for lab in costs_map}

    folds = walk_forward(dates, train_months=6, test_months=1, step_months=1, embargo_days=1)
    oos, chosen = {lab: [] for lab in costs_map}, []
    for f in folds:
        rows = [d for d in f.train if d in D["fees1.5"].index]
        scores = {v: stats.block_bootstrap(D["fees1.5"].loc[rows, v], n_sims=500, seed=f.k)["net_p5"] for v in variants}
        best = max(scores, key=scores.get)
        chosen.append({"fold": f.k, "test_from": str(f.test[0]), "test_to": str(f.test[-1]), "variant": best,
                       "train_net_p5": round(scores[best], 2)})
        for lab in costs_map:
            t = allres[lab][best]
            oos[lab].append(t[t["trading_date"].isin(f.test)])
    oos_tr = {lab: (pd.concat(v) if v else pd.DataFrame(columns=COLS)) for lab, v in oos.items()}
    oos_daily = daily(oos_tr["base"], [d for f in folds for d in f.test])

    srs = [stats.per_period_sharpe(D["base"][v]) for v in variants]
    n_global = trials.count() - trials.count(family="engine-sanity") + (0 if a.dry else len(variants))
    cl = clusters.cluster_trials(D["base"])
    k_srs = [srs[m] for m in cl["medoids"].values()]
    pbo = stats.pbo_cscv(D["base"], n_blocks=8) if len(dates) >= 16 else {"pbo": None}
    full_net = np.array([D["base"][v].sum() for v in variants])
    final = chosen[-1]["variant"] if chosen else None
    fi = variants.index(final) if final else None
    q = clusters.cluster_quality(cl["labels"], full_net)
    fc = int(cl["labels"][fi]) if final else None
    nb = [D["base"][vid(x)].sum() for x in neighbours(grid[fi], hyp.space)] if final else []
    yrs = oos_daily.groupby([d.year for d in oos_daily.index]).sum() if len(oos_daily) else pd.Series(dtype=float)
    ts_oos = trade_stats(oos_tr["base"])
    ok = len(oos_daily) > 2
    evidence = {
        "oos_trades": ts_oos["trades"],
        "oos_net_stress": float(oos_tr["fees1.5_lat250"]["net_pnl"].sum()) if len(oos_tr["fees1.5_lat250"]) else 0.0,
        "dsr_raw": stats.dsr(oos_daily, srs, n_trials=max(len(variants), n_global)) if ok else None,
        "oos_t": ts_oos.get("t_stat"), "pbo": pbo["pbo"],
        "plateau_pass": stats.plateau_test(full_net[fi], nb)["pass"] if final else None,
        "concentrated": concentration(oos_daily)["flag_concentrated"] if ok else None,
        "years_positive_share": float((yrs > 0).mean()) if len(yrs) else None, "n_years": int(len(yrs)),
        "tier_b_same_sign": None, "mc_net_p5": None, "mc_p_loss": None,
        "is_medoid": bool(final and cl["medoids"].get(fc) == fi),
        "cluster_share_profitable": float(q.loc[fc, "share_profitable"]) if final else None,
        "island": (not bool(q.loc[fc, "credible"])) if final else None,
        "dsr_k": stats.dsr(oos_daily, k_srs, n_trials=cl["k"]) if ok else None,
    }
    if len(oos_tr["base"]):
        mc = stats.execution_mc(oos_tr["base"]["net_pnl"].to_numpy(float), oos_tr["base"]["fees"].to_numpy(float),
                                n_sims=1000)
        evidence["mc_net_p5"], evidence["mc_p_loss"] = mc["net_p5"], mc["p_loss"]
    table = gates.evaluate(evidence)
    verdict = gates.verdict(table, evidence)

    daily_dir = ROOT / "research" / "daily" / a.hyp
    if not a.dry:
        daily_dir.mkdir(parents=True, exist_ok=True)
        for p in grid:
            v = vid(p)
            D["base"][v].to_csv(daily_dir / f"{v}.csv", header=["net_pnl"])
            s = trade_stats(allres["base"][v])
            trials.append({"family": a.hyp, "hypothesis": a.hyp, "params": p,
                           "data": f"ES RTH trades {dates[0]}..{dates[-1]} ({len(dates)} days)",
                           "fill_mode": "market entry/exit, stop at worse book; quotes from trades",
                           "results": {k: (round(x, 4) if isinstance(x, float) else x) for k, x in s.items()},
                           "daily_pnl_path": str((daily_dir / f"{v}.csv").relative_to(ROOT))})

    stress = {lab: round(float(oos_tr[lab]["net_pnl"].sum()), 2) if len(oos_tr[lab]) else 0.0 for lab in costs_map}
    months = (oos_tr["base"].groupby(pd.to_datetime(oos_tr["base"]["trading_date"]).dt.strftime("%Y-%m"))["net_pnl"]
              .agg(["size", "sum"]) if len(oos_tr["base"]) else pd.DataFrame())
    fam = pd.DataFrame({"net": full_net, "trades": [len(allres["base"][v]) for v in variants],
                        "avg_ticks": [allres["base"][v]["ticks"].mean() for v in variants]}, index=variants)
    lines = ["---", "type: result", f"date: {date.today().isoformat()}", f"tags: [phase-5, {a.hyp}, gates]", "---",
             f"# {a.hyp} evaluation (D-020 protocol): gate verdict **{verdict}**", "",
             f"{hyp.title}. Data: {len(dates)} RTH days {dates[0]}..{dates[-1]} (quotes rebuilt from trades). "
             f"{len(variants)} variants; {len(folds)} walk-forward folds (6 m / 1 m, 1-day embargo). "
             f"DSR uses N = {max(len(variants), n_global)} (all hypothesis trials so far).", "",
             "## Gates", md(table), "", "## Out-of-sample (concatenated test months)",
             "```", json.dumps({k: (round(v, 4) if isinstance(v, float) else v) for k, v in ts_oos.items()}, indent=1), "```",
             f"Net PnL by cost scenario: {stress}", "", "### Per month", md(months) if len(months) else "none", "",
             "## Variant chosen per fold", md(pd.DataFrame(chosen), index=False) if chosen else "none", "",
             f"## Family: PBO = {pbo['pbo']}, clusters K = {cl['k']}, variants net > 0: "
             f"{int((full_net > 0).sum())}/{len(variants)}", "",
             "Full-period results of all variants (in-sample for selection; not evidence of an edge):", "",
             md(fam.sort_values("net", ascending=False).round(2)), ""]
    out_path.write_text("\n".join(lines) + "\n")
    print(table.to_string())
    print("verdict:", verdict, "| OOS:", {k: ts_oos.get(k) for k in ("trades", "net_pnl", "avg_ticks", "t_stat")},
          "| variants net>0:", int((full_net > 0).sum()), "/", len(variants))
    print("saved", out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
