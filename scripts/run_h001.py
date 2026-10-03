"""Evaluate H-001 exactly as fixed in decision D-020 and write the gate report.

  python scripts/run_h001.py [--start 2024-11-01] [--end 2025-09-30]

Uses ONLY cached RTH trade chunks (Downloader.fetch_rth downloads them; this script never
downloads). Logs all 72 variants via research.trials.append, saves their daily PnL to
research/daily/H-001/, and writes vault/results/h001-report.md.
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

from backtest.bracket import Day                                    # noqa: E402
from backtest.costs import load_costs                               # noqa: E402
from backtest.engine import l1_from_trades                          # noqa: E402
from backtest.metrics import concentration, daily_pnl, trade_stats  # noqa: E402
from data import cache                                              # noqa: E402
from data.config import DATASET, load_settings                      # noqa: E402
from data.contracts import continuous_symbol                        # noqa: E402
from data.holdout import development_dates                          # noqa: E402
from data.loader import load_chunks, slice_session                  # noqa: E402
from data.sessions import trading_dates                             # noqa: E402
from research import clusters, gates, registry, stats, trials       # noqa: E402
from research.walkforward import walk_forward                       # noqa: E402
import strategies.h001 as H                                         # noqa: E402

HYP = "H-001"
DAILY_DIR = ROOT / "research" / "daily" / HYP
KEYS = ("min_vol", "level_tol", "div_lookback", "stop_ticks", "target_ticks")


def md(df: pd.DataFrame, index: bool = True) -> str:
    try:
        return df.to_markdown(index=index)
    except ImportError:                       # tabulate not installed
        return "```\n" + df.to_string(index=index) + "\n```"


def vid(p: dict) -> str:
    return "_".join(f"{k}{p[k]}" for k in KEYS)


def cached_days(start: date, end: date, schema_dir: str = "trades-rth") -> list[tuple[date, Path]]:
    root = load_settings().cache_dir
    out = []
    for d in development_dates(trading_dates(start, end)):
        p = cache.chunk_path(root, DATASET, schema_dir, continuous_symbol(d), d)
        if p.exists():
            out.append((d, p))
    return out


def run_all(days, hyp, costs_map) -> dict:
    """{cost_label: {variant_id: trades DataFrame}} for every variant."""
    res = {lab: {vid(p): [] for p in hyp.grid()} for lab in costs_map}
    mvs, lbs = hyp.space["min_vol"], hyp.space["div_lookback"]
    for k, (d, path) in enumerate(days):
        tr = slice_session(load_chunks([path]), d, rth_only=True)
        if tr.empty:
            continue
        feat = H.day_features(tr, mvs, lbs)
        day = Day.from_l1(l1_from_trades(tr))
        sig_cache = {}
        for p in hyp.grid():
            key = (p["min_vol"], p["level_tol"], p["div_lookback"])
            if key not in sig_cache:
                sig_cache[key] = H.signals(feat, *key, d)
            for lab, c in costs_map.items():
                res[lab][vid(p)] += H.trade_day(day, sig_cache[key], p["stop_ticks"], p["target_ticks"], d, c)
        if k % 20 == 0:
            print(f"  {k + 1}/{len(days)} days", flush=True)
    cols = ["entry_ts", "exit_ts", "side", "entry_px", "exit_px", "reason", "gross_pnl", "fees", "net_pnl",
            "ticks", "trading_date"]
    return {lab: {v: pd.DataFrame(t, columns=cols) for v, t in d.items()} for lab, d in res.items()}


def daily(trades: pd.DataFrame, dates) -> pd.Series:
    s = pd.Series(0.0, index=pd.Index(sorted(dates)))
    if len(trades):
        g = trades.groupby("trading_date")["net_pnl"].sum()
        s.loc[g.index] = g.to_numpy()
    return s


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--start", type=date.fromisoformat, default=date(2024, 11, 1))
    ap.add_argument("--end", type=date.fromisoformat, default=date(2025, 9, 30))
    ap.add_argument("--dry", action="store_true", help="pipeline test: no trial logging, report to --out")
    ap.add_argument("--schema-dir", default="trades-rth")
    ap.add_argument("--out", type=Path, default=ROOT / "vault" / "results" / "h001-report.md")
    a = ap.parse_args(argv)
    hyp = registry.load(HYP)
    if not a.dry:
        used = trials.count(hypothesis=HYP)
        if used + hyp.space_size > hyp.trial_budget:
            raise SystemExit(f"{HYP}: {used} trials already logged; budget {hyp.trial_budget} has no room for "
                             f"{hyp.space_size} more. The evaluation runs once (D-020).")
    days = cached_days(a.start, a.end, a.schema_dir)
    dates = [d for d, _ in days]
    print(f"{len(days)} cached RTH days {dates[0]}..{dates[-1]}", flush=True)
    base = load_costs()
    costs_map = {"base": base, "fees1.5": load_costs(fee_multiplier=1.5),
                 "fees1.5_lat250": load_costs(fee_multiplier=1.5, latency_ms=250),
                 "fees2_lat500": load_costs(fee_multiplier=2.0, latency_ms=500)}
    allres = run_all(days, hyp, costs_map)
    variants = list(allres["base"])
    D = {lab: pd.DataFrame({v: daily(allres[lab][v], dates) for v in variants}) for lab in costs_map}

    # ---- walk-forward (D-020): select on train by block-bootstrap 5th pct net at 1.5x fees
    folds = walk_forward(dates, train_months=6, test_months=1, step_months=1, embargo_days=1)
    oos = {lab: [] for lab in costs_map}
    chosen = []
    for f in folds:
        tr_rows = [d for d in f.train if d in D["fees1.5"].index]
        scores = {v: stats.block_bootstrap(D["fees1.5"].loc[tr_rows, v], n_sims=500, seed=f.k)["net_p5"]
                  for v in variants}
        best = max(scores, key=scores.get)
        chosen.append({"fold": f.k, "test_from": str(f.test[0]), "test_to": str(f.test[-1]), "variant": best,
                       "train_net_p5": round(scores[best], 2)})
        for lab in costs_map:
            t = allres[lab][best]
            oos[lab].append(t[t["trading_date"].isin(f.test)])
    oos_tr = {lab: pd.concat(v) if v else allres[lab][variants[0]].iloc[0:0] for lab, v in oos.items()}
    oos_dates = [d for f in folds for d in f.test]
    oos_daily = daily(oos_tr["base"], oos_dates)

    # ---- family statistics
    srs = [stats.per_period_sharpe(D["base"][v]) for v in variants]
    cl = clusters.cluster_trials(D["base"])
    k_srs = [stats.per_period_sharpe(D["base"][variants[m]]) for m in cl["medoids"].values()]
    pbo = stats.pbo_cscv(D["base"], n_blocks=8) if len(dates) >= 16 else {"pbo": None}
    final = chosen[-1]["variant"] if chosen else None
    fin_idx = variants.index(final) if final else None
    full_net = np.array([D["base"][v].sum() for v in variants])
    fin_cluster = cl["labels"][fin_idx] if final else None
    q = clusters.cluster_quality(cl["labels"], full_net)
    neighbours = []
    params_of = {vid(p): p for p in hyp.grid()}
    if final:
        p = params_of[final]
        for k in ("stop_ticks", "target_ticks", "min_vol"):
            vals = hyp.space[k]
            i = vals.index(p[k])
            for j in (i - 1, i + 1):
                if 0 <= j < len(vals):
                    neighbours.append(D["base"][vid({**p, k: vals[j]})].sum())
    yrs = oos_daily.groupby([d.year for d in oos_daily.index]).sum() if len(oos_daily) else pd.Series(dtype=float)
    ts_oos = trade_stats(oos_tr["base"])
    evidence = {
        "oos_trades": ts_oos["trades"],
        "oos_net_stress": float(oos_tr["fees1.5_lat250"]["net_pnl"].sum()) if len(oos_tr["fees1.5_lat250"]) else 0.0,
        "dsr_raw": stats.dsr(oos_daily, srs, n_trials=len(variants)) if len(oos_daily) > 2 else None,
        "oos_t": ts_oos.get("t_stat"),
        "pbo": pbo["pbo"],
        "plateau_pass": stats.plateau_test(D["base"][final].sum(), neighbours)["pass"] if final else None,
        "concentrated": concentration(oos_daily)["flag_concentrated"] if len(oos_daily) else None,
        "years_positive_share": float((yrs > 0).mean()) if len(yrs) else None,
        "n_years": int(len(yrs)),
        "tier_b_same_sign": None,                      # R3.5 calibration not run yet -> FAIL by design
        "mc_net_p5": None, "mc_p_loss": None,
        "is_medoid": bool(final and cl["medoids"].get(int(fin_cluster)) == fin_idx),
        "cluster_share_profitable": float(q.loc[int(fin_cluster), "share_profitable"]) if final else None,
        "island": (not bool(q.loc[int(fin_cluster), "credible"])) if final else None,
        "dsr_k": stats.dsr(oos_daily, k_srs, n_trials=cl["k"]) if len(oos_daily) > 2 else None,
    }
    if len(oos_tr["base"]):
        mc = stats.execution_mc(oos_tr["base"]["net_pnl"].to_numpy(), oos_tr["base"]["fees"].to_numpy(), n_sims=1000)
        evidence["mc_net_p5"], evidence["mc_p_loss"] = mc["net_p5"], mc["p_loss"]
    table = gates.evaluate(evidence)
    verdict = gates.verdict(table, evidence)

    # ---- log every variant (append-only, budget-checked) and save daily series
    DAILY_DIR.mkdir(parents=True, exist_ok=True)
    for p in ([] if a.dry else hyp.grid()):
        v = vid(p)
        D["base"][v].to_csv(DAILY_DIR / f"{v}.csv", header=["net_pnl"])
        s = trade_stats(allres["base"][v])
        trials.append({"family": HYP, "hypothesis": HYP, "params": p,
                       "data": f"ES RTH trades {dates[0]}..{dates[-1]} ({len(dates)} days)",
                       "fill_mode": "market entry, trade_through target, stop at worse book; quotes from trades",
                       "results": {k: (round(x, 4) if isinstance(x, float) else x) for k, x in s.items()},
                       "daily_pnl_path": str((DAILY_DIR / f"{v}.csv").relative_to(ROOT))})

    # ---- report
    stress = {lab: round(float(oos_tr[lab]["net_pnl"].sum()), 2) if len(oos_tr[lab]) else 0.0 for lab in costs_map}
    months = oos_tr["base"].groupby(pd.to_datetime(oos_tr["base"]["trading_date"]).dt.strftime("%Y-%m"))["net_pnl"].agg(
        ["size", "sum"]) if len(oos_tr["base"]) else pd.DataFrame()
    fam = pd.DataFrame({"net": full_net, "trades": [len(allres["base"][v]) for v in variants],
                        "sharpe_ann": [s * np.sqrt(252) if np.isfinite(s) else np.nan for s in srs]}, index=variants)
    lines = ["---", "type: result", f"date: {date.today().isoformat()}", "tags: [phase-5, H-001, gates]", "---",
             f"# H-001 evaluation (D-020): verdict **{verdict}**", "",
             f"Data: {len(dates)} RTH days {dates[0]}..{dates[-1]}, quotes rebuilt from trades (D-019). "
             f"72 variants, {len(folds)} walk-forward folds (6 m train / 1 m test, 1-day embargo).", "",
             "## Gates", md(table), "",
             "## Out-of-sample (concatenated test months)",
             "```", json.dumps({k: (round(v, 4) if isinstance(v, float) else v) for k, v in ts_oos.items()}, indent=1), "```",
             f"Net PnL by cost scenario: {stress}", "", "### Per month", md(months) if len(months) else "none", "",
             "## Variant chosen per fold", md(pd.DataFrame(chosen), index=False) if chosen else "none", "",
             f"## Family: PBO = {pbo['pbo']}, clusters K = {cl['k']}, DSR raw = {evidence['dsr_raw']}, "
             f"DSR K = {evidence['dsr_k']}", "",
             "Full-period results of all 72 variants (in-sample for selection; not evidence of an edge):", "",
             md(fam.sort_values("net", ascending=False).round(2)), "",
             "Limitations: one year of data (G7 cannot pass); tier-B fill check (G8) not run; no market impact; "
             "quotes rebuilt from trades (81% exact)."]
    out = a.out
    out.write_text("\n".join(lines) + "\n")
    print(table.to_string())
    print("verdict:", verdict, "| OOS:", {k: ts_oos.get(k) for k in ("trades", "net_pnl", "avg_ticks", "t_stat")})
    print("saved", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
