"""Evaluate a registered BAR-based hypothesis once (protocol D-023/D-026) on 15 years of hourly bars.

  python scripts/run_bars_hypothesis.py H-005

Strategy module strategies/<id>.py provides KEYS and
  trades(P, dates, p, adverse_ticks, fee_rt, point_value) -> DataFrame
    [trading_date (exit date), side, gross_pnl, fees, net_pnl, ticks]
where P = {"ES.c.0": daily table, "ES.c.1": daily table}; each table is indexed by trading date with
columns p0900..p1500 (closes of the CT hourly bars ending at that time).
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

from backtest.costs import load_costs                               # noqa: E402
from backtest.metrics import concentration, trade_stats             # noqa: E402
from data.holdout import check as holdout_check                     # noqa: E402
from data.sessions import CT                                        # noqa: E402
from research import clusters, gates, registry, stats, trials       # noqa: E402
from research.walkforward import walk_forward                       # noqa: E402
from scripts.run_h001 import md                                     # noqa: E402
from scripts.run_h003 import daily, fetch_hourly                    # noqa: E402

TICK = 0.25


def hourly_table(bars: pd.DataFrame) -> pd.DataFrame:
    b = bars.copy()
    start_ct = pd.DatetimeIndex(b.index).tz_convert(CT)
    b["d"], b["h"] = start_ct.date, start_ct.hour
    b = b[b["h"].between(8, 14)]
    t = b.pivot_table(index="d", columns="h", values="close", aggfunc="last")
    t.columns = [f"p{h + 1:02d}00" for h in t.columns]
    return t


def main(argv=None) -> int:
    from data.download import Downloader
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("hyp")
    a = ap.parse_args(argv)
    hyp = registry.load(a.hyp)
    mod = importlib.import_module("strategies." + a.hyp.lower().replace("-", ""))
    if hyp.status != "open" or trials.count(hypothesis=a.hyp) + hyp.space_size > hyp.trial_budget:
        raise SystemExit(f"{a.hyp}: closed or already evaluated (single evaluation).")
    dl = Downloader()
    P = {s: hourly_table(fetch_hourly(dl, s)) for s in ("ES.c.0", "ES.c.1")}
    dates = sorted(set(P["ES.c.0"].index) | set(P["ES.c.1"].index))
    holdout_check(dates)
    c = load_costs()
    scen = {"base": (1.0, c.fee(1) * 2), "fees1.5": (1.0, c.fee(1) * 3), "stress": (2.0, c.fee(1) * 3),
            "plus1tick": (2.0, c.fee(1) * 2)}
    grid = list(hyp.grid())
    vid = lambda p: "_".join(f"{k}{p[k]}" for k in mod.KEYS)        # noqa: E731
    variants = [vid(p) for p in grid]
    T = {lab: {vid(p): mod.trades(P, dates, p, adv, fee, c.point_value) for p in grid} for lab, (adv, fee) in scen.items()}
    D = {lab: pd.DataFrame({v: daily(T[lab][v], dates) for v in variants}) for lab in scen}

    folds = walk_forward(dates, train_months=36, test_months=12, step_months=12, embargo_days=1)
    oos, chosen = {lab: [] for lab in scen}, []
    for f in folds:
        rows = [d for d in f.train if d in D["fees1.5"].index]
        sc = {v: stats.block_bootstrap(D["fees1.5"].loc[rows, v], n_sims=500, seed=f.k)["net_p5"] for v in variants}
        best = max(sc, key=sc.get)
        chosen.append({"fold": f.k, "test": f"{f.test[0]}..{f.test[-1]}", "variant": best, "train_net_p5": round(sc[best], 1)})
        for lab in scen:
            t = T[lab][best]
            oos[lab].append(t[t["trading_date"].isin(f.test)])
    oos_tr = {lab: pd.concat(v) for lab, v in oos.items()}
    oos_daily = daily(oos_tr["base"], [d for f in folds for d in f.test])
    srs = [stats.per_period_sharpe(D["base"][v]) for v in variants]
    n_global = trials.count() - trials.count(family="engine-sanity") + len(variants)
    full_net = np.array([D["base"][v].sum() for v in variants])
    if len(variants) >= 3:
        cl = clusters.cluster_trials(D["base"])
    else:
        cl = {"labels": np.zeros(len(variants), int), "k": 1, "medoids": {0: int(np.argmax(full_net))}}
    pbo = stats.pbo_cscv(D["base"], n_blocks=16)
    final = chosen[-1]["variant"]
    fi = variants.index(final)
    q = clusters.cluster_quality(cl["labels"], full_net)
    fc = int(cl["labels"][fi])
    nb = [full_net[j] for j, p in enumerate(grid) if j != fi and sum(p[k] != grid[fi][k] for k in p) == 1]
    yrs = oos_daily.groupby([d.year for d in oos_daily.index]).sum()
    ts_oos = trade_stats(oos_tr["base"])
    base_net = oos_tr["base"]["net_pnl"].sum()
    mc = (stats.execution_mc(oos_tr["base"]["net_pnl"].to_numpy(float), oos_tr["base"]["fees"].to_numpy(float), n_sims=1000)
          if len(oos_tr["base"]) else {"net_p5": None, "p_loss": None})
    evidence = {
        "oos_trades": ts_oos["trades"], "oos_net_stress": float(oos_tr["stress"]["net_pnl"].sum()),
        "dsr_raw": stats.dsr(oos_daily, srs, n_trials=n_global), "oos_t": ts_oos.get("t_stat"),
        "pbo": pbo["pbo"], "plateau_pass": stats.plateau_test(full_net[fi], nb)["pass"] if nb else None,
        "concentrated": concentration(oos_daily)["flag_concentrated"],
        "years_positive_share": float((yrs > 0).mean()), "n_years": int(len(yrs)),
        "tier_b_same_sign": bool(base_net > 0 and oos_tr["plus1tick"]["net_pnl"].sum() > 0),
        "mc_net_p5": mc["net_p5"], "mc_p_loss": mc["p_loss"],
        "is_medoid": bool(cl["medoids"].get(fc) == fi),
        "cluster_share_profitable": float(q.loc[fc, "share_profitable"]), "island": not bool(q.loc[fc, "credible"]),
        "dsr_k": stats.dsr(oos_daily, [srs[m] for m in cl["medoids"].values()], n_trials=max(cl["k"], 1)),
    }
    table = gates.evaluate(evidence)
    verdict = gates.verdict(table, evidence)
    dd = ROOT / "research" / "daily" / a.hyp
    dd.mkdir(parents=True, exist_ok=True)
    for p in grid:
        v = vid(p)
        D["base"][v].to_csv(dd / f"{v}.csv", header=["net_pnl"])
        s = trade_stats(T["base"][v])
        trials.append({"family": a.hyp, "hypothesis": a.hyp, "params": p, "data": f"ES ohlcv-1h {dates[0]}..{dates[-1]}",
                       "fill_mode": "bar closes, 1 tick adverse per side + fees",
                       "results": {k: (round(x, 4) if isinstance(x, float) else x) for k, x in s.items()},
                       "daily_pnl_path": str((dd / f"{v}.csv").relative_to(ROOT))})
    by_year = pd.DataFrame({"oos_net": yrs.round(1),
                            "oos_trades": oos_tr["base"].groupby([d.year for d in oos_tr["base"]["trading_date"]]).size()})
    fam = pd.DataFrame({"net": full_net.round(1), "trades": [len(T["base"][v]) for v in variants],
                        "avg_ticks": [round(T["base"][v]["ticks"].mean(), 3) if len(T["base"][v]) else None for v in variants]},
                       index=variants)
    stress = {lab: round(float(oos_tr[lab]["net_pnl"].sum()), 1) for lab in scen}
    out = ROOT / "vault" / "results" / f"{a.hyp.lower().replace('-', '')}-report.md"
    out.write_text("\n".join([
        "---", "type: result", f"date: {date.today().isoformat()}", f"tags: [phase-5, {a.hyp}, gates]", "---",
        f"# {a.hyp} evaluation (D-023/D-026): gate verdict **{verdict}**", "",
        f"{hyp.title}. {len(dates)} dates {dates[0]}..{dates[-1]}; {len(folds)} folds (3 y / 1 y). DSR N = {n_global}. "
        "Costs: 1 tick adverse per side + fees (stress 2 ticks + fees x1.5).", "",
        "## Gates", md(table), "", "## Out-of-sample", "```",
        json.dumps({k: (round(v, 4) if isinstance(v, float) else v) for k, v in ts_oos.items()}, indent=1), "```",
        f"Net by scenario: {stress}", "", "### By year (OOS)", md(by_year), "",
        "## Variant chosen per fold", md(pd.DataFrame(chosen), index=False), "",
        f"## Family: PBO = {pbo['pbo']:.3f}, K = {cl['k']}", "", md(fam), ""]) + "\n")
    print(table.to_string())
    print("verdict:", verdict, "| OOS:", {k: ts_oos.get(k) for k in ("trades", "net_pnl", "avg_ticks", "t_stat")},
          "| variants net>0:", int((full_net > 0).sum()), "/", len(variants))
    print(by_year.to_string())
    print("saved", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
