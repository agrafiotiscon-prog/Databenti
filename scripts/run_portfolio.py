"""Evaluate a portfolio hypothesis once (H-022 and later cross-market ones). Protocol: registry + D-023/D-048.

  python scripts/run_portfolio.py [--hypothesis H-0xx] [--coverage-only]

Signals come from portfolio.signals.BUILDERS[hypothesis] (default: the engine's built-in signals,
used by H-022). Coverage (D-042) is printed and written before any P&L is computed.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backtest.costs import load_costs                      # noqa: E402
from backtest.metrics import concentration, drawdown        # noqa: E402
from data.holdout import check as holdout_check             # noqa: E402
from data.universe import BY_ROOT, UNIVERSE                 # noqa: E402
from portfolio.data import build, load_bars                 # noqa: E402
from portfolio.engine import prepare, simulate              # noqa: E402
from portfolio.signals import BUILDERS, builtin             # noqa: E402
from research import clusters, gates, registry, stats, trials   # noqa: E402
from research.walkforward import walk_forward               # noqa: E402
from scripts.fetch_futures_daily import path_for            # noqa: E402
from scripts.run_h001 import md                             # noqa: E402

CAPITAL, SMALL = 1_000_000.0, 100_000.0


def load_all(dl):
    rds, cov = [], []
    for s in UNIVERSE:
        p0, p1 = path_for(dl, f"{s.root}.v.0"), path_for(dl, f"{s.root}.v.1")
        if not (p0.exists() and p1.exists()):
            cov.append({"root": s.root, "status": "MISSING"})
            continue
        v0, v1 = load_bars(p0), load_bars(p1)
        rd = build(s.root, v0, v1)
        pr = prepare(rd)
        cov.append({"root": s.root, "sector": s.sector, "first": rd.dates[0], "last": rd.dates[-1], "days": len(rd.dates),
                    "instruments": len(rd.closes), "returns_ok": round(float(pr.r.notna().mean()), 4),
                    "carry_known": round(float((pr.signals["carry"] != 0).mean()), 3),
                    "median_close": round(float(v0["close"].median()), 6)})
        rds.append(pr)
    return rds, pd.DataFrame(cov)


def oos_stats(daily: pd.Series, capital: float) -> dict:
    ann = daily.mean() * 252 / capital
    vol = daily.std() * np.sqrt(252) / capital
    dd = drawdown(daily)
    return {"ann_return_pct": round(100 * ann, 2), "ann_vol_pct": round(100 * vol, 2),
            "sharpe": round(float(ann / vol), 3) if vol > 0 else None,
            "max_dd_pct": round(100 * float(dd.get("max_drawdown", np.nan)) / capital, 2) if dd else None,
            "t_daily": round(float(daily.mean() / daily.std() * np.sqrt(len(daily))), 3) if daily.std() > 0 else None}


def main(argv=None) -> int:
    from data.download import Downloader
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--hypothesis", default="H-022")
    ap.add_argument("--coverage-only", action="store_true")
    ap.add_argument("--placebo-draws", type=int, default=300)
    a = ap.parse_args(argv)
    HYP = a.hypothesis
    hyp = registry.load(HYP)
    if not a.coverage_only and (hyp.status != "open" or trials.count(hypothesis=HYP) + hyp.space_size > hyp.trial_budget):
        raise SystemExit(f"{HYP}: closed or already evaluated (single evaluation).")
    dl = Downloader()
    preps, cov = load_all(dl)
    print(cov.to_string(), flush=True)
    out_cov = ROOT / "vault" / "results" / "futures-daily-check.md"
    out_cov.write_text("\n".join(["---", "type: result", f"date: {date.today().isoformat()}", "tags: [R7, coverage, D-042]",
                                  "---", "# R7 daily futures data: coverage before any P&L (D-042)", "",
                                  "returns_ok = share of days with a same-instrument close-to-close return; "
                                  "median_close checks quoted units against data/universe.py point values.", "",
                                  md(cov, index=False), ""]) + "\n")
    if a.coverage_only:
        return 0
    cal = sorted(set().union(*[p.dates for p in preps]))
    holdout_check(cal)
    built = BUILDERS.get(HYP, builtin)(preps)
    for p in preps:
        for v, by_root in built.items():
            p.signals[v] = by_root[p.root].reindex(p.dates).fillna(0.0)
    c = load_costs()
    fee = c.fee(1)
    scen = {"base": (1.0, fee), "fees1.5": (1.0, fee * 1.5), "stress": (2.0, fee * 1.5), "plus1tick": (2.0, fee)}
    grid = list(hyp.grid())
    variants = [g["variant"] for g in grid]
    missing = [v for v in variants if v not in built]
    if missing:
        raise SystemExit(f"{HYP}: no signal for variants {missing} (portfolio/signals.py)")
    S = {lab: {v: simulate(preps, v, CAPITAL, sl, fe) for v in variants} for lab, (sl, fe) in scen.items()}
    D = {lab: pd.DataFrame({v: S[lab][v]["net"] for v in variants}).reindex(cal).fillna(0.0) for lab in scen}
    folds = walk_forward(cal, train_months=36, test_months=12, step_months=12, embargo_days=1)
    chosen, oos = [], {lab: [] for lab in scen}
    oos_trades = 0
    for f in folds:
        rows = [d for d in f.train if d in D["fees1.5"].index]
        sc = {v: stats.block_bootstrap(D["fees1.5"].loc[rows, v], n_sims=500, seed=f.k)["net_p5"] for v in variants}
        best = max(sc, key=sc.get)
        chosen.append({"fold": f.k, "test": f"{f.test[0]}..{f.test[-1]}", "variant": best, "train_net_p5": round(sc[best])})
        for lab in scen:
            oos[lab].append(D[lab].loc[[d for d in f.test if d in D[lab].index], best])
        tt = S["base"][best]
        oos_trades += int(tt.loc[tt.index.isin(f.test), "trades"].sum())
    od = {lab: pd.concat(v) for lab, v in oos.items()}
    oos_dates = list(od["base"].index)
    srs = [stats.per_period_sharpe(D["base"][v]) for v in variants]
    n_global = trials.count() - trials.count(family="engine-sanity") + len(variants)
    full_net = np.array([D["base"][v].sum() for v in variants])
    cl = clusters.cluster_trials(D["base"])
    pbo = stats.pbo_cscv(D["base"], n_blocks=16)
    final = chosen[-1]["variant"]
    fi = variants.index(final)
    q = clusters.cluster_quality(cl["labels"], full_net)
    fc = int(cl["labels"][fi])
    nb = [full_net[j] for j in range(len(variants)) if j != fi]
    yrs = od["base"].groupby([d.year for d in od["base"].index]).sum()
    bb = stats.block_bootstrap(od["fees1.5"], n_sims=2000, seed=1)
    st = oos_stats(od["base"], CAPITAL)

    # G12 placebo: each market's signal circularly shifted by an independent offset (>= 63 days)
    rng = np.random.default_rng(22)
    real = float(od["base"].sum())
    shifted = []
    for _ in range(a.placebo_draws):
        ov = {}
        for p in preps:
            s = p.signals[final]
            k = int(rng.integers(63, max(64, len(s) - 63)))
            ov[p.root] = pd.Series(np.roll(s.to_numpy(), k), index=s.index)
        sim = simulate(preps, final, CAPITAL, *scen["base"], signal_override=ov)["net"].reindex(cal).fillna(0.0)
        shifted.append(float(sim.loc[oos_dates].sum()))
    placebo_p = float((np.array(shifted) >= real).mean())

    evidence = {
        "oos_trades": oos_trades, "oos_net_stress": float(od["stress"].sum()),
        "dsr_raw": stats.dsr(od["base"], srs, n_trials=n_global), "oos_t": st["t_daily"],
        "pbo": pbo["pbo"], "plateau_pass": stats.plateau_test(full_net[fi], nb)["pass"],
        "concentrated": concentration(od["base"])["flag_concentrated"],
        "years_positive_share": float((yrs > 0).mean()), "n_years": int(len(yrs)),
        "tier_b_same_sign": bool(od["base"].sum() > 0 and od["plus1tick"].sum() > 0),
        "mc_net_p5": bb["net_p5"], "mc_p_loss": bb["p_loss"],
        "is_medoid": bool(cl["medoids"].get(fc) == fi),
        "cluster_share_profitable": float(q.loc[fc, "share_profitable"]), "island": not bool(q.loc[fc, "credible"]),
        "dsr_k": stats.dsr(od["base"], [srs[m] for m in cl["medoids"].values()], n_trials=max(cl["k"], 1)),
        "placebo_p": placebo_p,
    }
    table = gates.evaluate(evidence)
    verdict = gates.verdict(table, evidence)

    # realism check at $100k with integer contracts (same fold choices); not a gate
    small = pd.concat([simulate(preps, ch["variant"], SMALL, *scen["base"])["net"].reindex(cal).fillna(0.0)
                       .loc[[d for d in f.test if d in cal]] for ch, f in zip(chosen, folds)])
    st_small = oos_stats(small, SMALL)
    # contribution by sector / market of the chosen variants, OOS
    det = pd.concat([simulate(preps, ch["variant"], CAPITAL, *scen["base"], detail=True)
                     .pipe(lambda x: x[x["date"].isin(f.test)]) for ch, f in zip(chosen, folds)])
    det["sector"] = det["root"].map(lambda r: BY_ROOT[r].sector)
    by_sector = det.groupby("sector")["net"].sum().round(0).sort_values()
    by_root = det.groupby("root")["net"].sum().round(0).sort_values()

    dd = ROOT / "research" / "daily" / HYP
    dd.mkdir(parents=True, exist_ok=True)
    for g, v in zip(grid, variants):
        D["base"][v].to_csv(dd / f"{v}.csv", header=["net_pnl"])
        s = oos_stats(D["base"][v], CAPITAL)
        trials.append({"family": HYP, "hypothesis": HYP, "params": g, "data": f"26 CME futures ohlcv-1d v.0/v.1 {cal[0]}..{cal[-1]}",
                       "fill_mode": "next-day close, 1 tick + fees per contract side, $1M integer contracts",
                       "results": {"net_full_period": round(float(D["base"][v].sum()), 2), **s},
                       "daily_pnl_path": str((dd / f"{v}.csv").relative_to(ROOT))})
    by_year = pd.DataFrame({"oos_net": yrs.round(0), "return_pct": (100 * yrs / CAPITAL).round(2)})
    fam = pd.DataFrame({v: oos_stats(D["base"][v], CAPITAL) for v in variants}).T
    fam["net_full"] = full_net.round(0)
    out = ROOT / "vault" / "results" / f"{HYP.lower()}-report.md"
    out.write_text("\n".join([
        "---", "type: result", f"date: {date.today().isoformat()}", f"tags: [R7, {HYP}, gates, portfolio]", "---",
        f"# {HYP} futures portfolio: gate verdict **{verdict}**", "",
        f"{hyp.title}. {len(preps)} markets, {len(cal)} dates {cal[0]}..{cal[-1]}; {len(folds)} folds (3 y / 1 y). "
        f"DSR N = {n_global}. Capital $1M, integer contracts, 15% vol target, next-day-close execution, "
        "1 tick + fees per contract side (stress 2 ticks + fees x1.5). Coverage: [futures-daily-check](futures-daily-check.md).", "",
        "## User target (D-048): Sharpe >= 1.0 net (~15%/yr at 15% vol)",
        f"OOS (walk-forward) at $1M: {st}", f"OOS at $100k (integer contracts, same choices; realism check): {st_small}", "",
        "## Gates", md(table), "", f"Placebo: real OOS net {real:,.0f} vs shifted-signal median {np.median(shifted):,.0f} "
        f"(95th pct {np.percentile(shifted, 95):,.0f}); p = {placebo_p:.3f}", "",
        f"Net by scenario (OOS): { {lab: round(float(v.sum())) for lab, v in od.items()} }; OOS contract trades {oos_trades}", "",
        "### By year (OOS)", md(by_year), "", "### By sector (OOS net, $)", md(by_sector.to_frame("net")), "",
        "### By market (OOS net, $)", md(by_root.to_frame("net")), "",
        "## Variant chosen per fold", md(pd.DataFrame(chosen), index=False), "",
        f"## Family (full period): PBO = {pbo['pbo']:.3f}, K = {cl['k']}", md(fam), ""]) + "\n")
    print(table.to_string())
    print("verdict:", verdict, "| OOS $1M:", st, "| $100k:", st_small, "| placebo p", placebo_p)
    print(by_year.to_string()); print(by_sector.to_string()); print(pd.DataFrame(chosen).to_string())
    print("saved", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
