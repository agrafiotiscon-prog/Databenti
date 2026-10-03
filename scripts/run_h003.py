"""H-003: last-hour intraday momentum on 15 years of hourly bars. Protocol: decision D-023.

  python scripts/run_h003.py [--dry]

Downloads ES ohlcv-1h for ES.c.0 and ES.c.1 (2010-06-07..2025-09-30) through the cost guard and the
cumulative cap, then evaluates the 4 registered variants once and writes vault/results/h003-report.md.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backtest.costs import load_costs                               # noqa: E402
from backtest.metrics import concentration, trade_stats             # noqa: E402
from data.contracts import continuous_symbol                        # noqa: E402
from data.cost_guard import Request                                 # noqa: E402
from data.holdout import check as holdout_check                     # noqa: E402
from data.sessions import CT                                        # noqa: E402
from research import clusters, gates, registry, stats, trials       # noqa: E402
from research.walkforward import walk_forward                       # noqa: E402
from scripts.run_h001 import md                                     # noqa: E402

HYP, START, END = "H-003", "2010-06-07", "2025-10-01"   # END exclusive -> last date 2025-09-30
TICK = 0.25


def fetch_hourly(dl, symbol: str) -> pd.DataFrame:
    import databento as db
    req = Request(dl.dataset, "ohlcv-1h", symbol, "continuous",
                  datetime.fromisoformat(START).replace(tzinfo=timezone.utc).isoformat(),
                  datetime.fromisoformat(END).replace(tzinfo=timezone.utc).isoformat())
    path = dl.cache_dir / dl.dataset / "ohlcv-1h-range" / symbol / f"{START}_{END}.dbn.zst"
    if not path.exists():
        cost = dl.guard.check([req])
        dl.check_total_cap(cost)
        dl._download([(req, path)])
    return db.DBNStore.from_file(path).to_df(pretty_ts=True)


def daily_prices(bars: pd.DataFrame) -> pd.DataFrame:
    """Per CME trading date (= CT calendar date for RTH): p0900, p1400, p1500 from bar closes."""
    b = bars.copy()
    start_ct = pd.DatetimeIndex(b.index).tz_convert(CT)
    b["d"] = start_ct.date
    b["h"] = start_ct.hour                 # bar START hour in CT; close = price at h+1:00
    pick = {8: "p0900", 13: "p1400", 14: "p1500"}
    b = b[b["h"].isin(pick)]
    t = b.pivot_table(index="d", columns="h", values="close", aggfunc="last").rename(columns=pick)
    return t.dropna()


def build_table(c0: pd.DataFrame, c1: pd.DataFrame) -> pd.DataFrame:
    p = {"ES.c.0": daily_prices(c0), "ES.c.1": daily_prices(c1)}
    rows = []
    dates = sorted(set(p["ES.c.0"].index) | set(p["ES.c.1"].index))
    for i, d in enumerate(dates):
        sym = continuous_symbol(d)
        t = p[sym]
        if d not in t.index:
            continue
        prev = [x for x in t.index if x < d]
        if not prev:
            continue
        pd_ = prev[-1]
        if (d - pd_).days > 5:                     # gap (missing data) -> no valid previous close
            continue
        r = t.loc[d]
        rows.append({"d": d, "sym": sym, "prev_close": t.loc[pd_, "p1500"], "p0900": r["p0900"],
                     "p1400": r["p1400"], "p1500": r["p1500"]})
    return pd.DataFrame(rows).set_index("d")


def variant_trades(tab: pd.DataFrame, p: dict, adverse_ticks: float, fee_rt: float, point_value: float) -> pd.DataFrame:
    end_px = tab["p0900"] if p["signal"] == "open30" else tab["p1400"]
    ret_bp = (end_px / tab["prev_close"] - 1) * 1e4
    side = np.sign(ret_bp).where(ret_bp.abs() >= max(p["min_abs_bp"], 1e-9), 0.0)
    take = side != 0
    t = tab[take]
    s = side[take]
    entry = t["p1400"] + s * adverse_ticks * TICK
    exit_ = t["p1500"] - s * adverse_ticks * TICK
    gross = s * (exit_ - entry) * point_value
    return pd.DataFrame({"trading_date": t.index, "side": s.to_numpy(), "entry_px": entry.to_numpy(),
                         "exit_px": exit_.to_numpy(), "gross_pnl": gross.to_numpy(), "fees": fee_rt,
                         "net_pnl": (gross - fee_rt).to_numpy(), "ticks": (gross / (point_value * TICK)).to_numpy()})


def daily(tr: pd.DataFrame, dates) -> pd.Series:
    s = pd.Series(0.0, index=pd.Index(list(dates)))
    if len(tr):
        g = tr.groupby("trading_date")["net_pnl"].sum()
        s.loc[g.index] = g.to_numpy()
    return s


def main(argv=None) -> int:
    from data.download import Downloader
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args(argv)
    hyp = registry.load(HYP)
    if not a.dry and trials.count(hypothesis=HYP) + hyp.space_size > hyp.trial_budget:
        raise SystemExit(f"{HYP} already evaluated (single evaluation).")
    dl = Downloader()
    tab = build_table(fetch_hourly(dl, "ES.c.0"), fetch_hourly(dl, "ES.c.1"))
    holdout_check(list(tab.index))
    dates = list(tab.index)
    print(f"{HYP}: {len(dates)} trading dates {dates[0]}..{dates[-1]}", flush=True)
    c = load_costs()
    scen = {"base": (1.0, c.fee(1) * 2), "fees1.5": (1.0, c.fee(1) * 3), "stress": (2.0, c.fee(1) * 3),
            "plus1tick": (2.0, c.fee(1) * 2)}
    grid = list(hyp.grid())
    vid = lambda p: f"signal{p['signal']}_min_abs_bp{p['min_abs_bp']}"   # noqa: E731
    variants = [vid(p) for p in grid]
    T = {lab: {vid(p): variant_trades(tab, p, adv, fee, c.point_value) for p in grid} for lab, (adv, fee) in scen.items()}
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
    oos_dates = [d for f in folds for d in f.test]
    oos_daily = daily(oos_tr["base"], oos_dates)
    srs = [stats.per_period_sharpe(D["base"][v]) for v in variants]
    n_global = trials.count() - trials.count(family="engine-sanity") + (0 if a.dry else len(variants))
    cl = clusters.cluster_trials(D["base"])
    pbo = stats.pbo_cscv(D["base"], n_blocks=16)
    full_net = np.array([D["base"][v].sum() for v in variants])
    final = chosen[-1]["variant"]
    fi = variants.index(final)
    q = clusters.cluster_quality(cl["labels"], full_net)
    fc = int(cl["labels"][fi])
    nb = [full_net[j] for j, p in enumerate(grid) if j != fi and sum(p[k] != grid[fi][k] for k in p) == 1]
    yrs = oos_daily.groupby([d.year for d in oos_daily.index]).sum()
    ts_oos = trade_stats(oos_tr["base"])
    mc = stats.execution_mc(oos_tr["base"]["net_pnl"].to_numpy(float), oos_tr["base"]["fees"].to_numpy(float), n_sims=1000)
    evidence = {
        "oos_trades": ts_oos["trades"], "oos_net_stress": float(oos_tr["stress"]["net_pnl"].sum()),
        "dsr_raw": stats.dsr(oos_daily, srs, n_trials=max(len(variants), n_global)), "oos_t": ts_oos.get("t_stat"),
        "pbo": pbo["pbo"], "plateau_pass": stats.plateau_test(full_net[fi], nb)["pass"],
        "concentrated": concentration(oos_daily)["flag_concentrated"],
        "years_positive_share": float((yrs > 0).mean()), "n_years": int(len(yrs)),
        "tier_b_same_sign": bool(np.sign(oos_tr["plus1tick"]["net_pnl"].sum()) == np.sign(oos_tr["base"]["net_pnl"].sum())
                                 and oos_tr["base"]["net_pnl"].sum() > 0),
        "mc_net_p5": mc["net_p5"], "mc_p_loss": mc["p_loss"],
        "is_medoid": bool(cl["medoids"].get(fc) == fi),
        "cluster_share_profitable": float(q.loc[fc, "share_profitable"]), "island": not bool(q.loc[fc, "credible"]),
        "dsr_k": stats.dsr(oos_daily, [srs[m] for m in cl["medoids"].values()], n_trials=cl["k"]),
    }
    table = gates.evaluate(evidence)
    verdict = gates.verdict(table, evidence)
    if not a.dry:
        dd = ROOT / "research" / "daily" / HYP
        dd.mkdir(parents=True, exist_ok=True)
        for p in grid:
            v = vid(p)
            D["base"][v].to_csv(dd / f"{v}.csv", header=["net_pnl"])
            s = trade_stats(T["base"][v])
            trials.append({"family": HYP, "hypothesis": HYP, "params": p, "data": f"ES ohlcv-1h {dates[0]}..{dates[-1]}",
                           "fill_mode": "bar closes, 1 tick adverse per side + fees",
                           "results": {k: (round(x, 4) if isinstance(x, float) else x) for k, x in s.items()},
                           "daily_pnl_path": str((dd / f"{v}.csv").relative_to(ROOT))})
    by_year = pd.DataFrame({"oos_net": yrs.round(1), "oos_trades": oos_tr["base"].groupby(
        [d.year for d in oos_tr["base"]["trading_date"]]).size()})
    fam = pd.DataFrame({"net": full_net.round(1), "trades": [len(T["base"][v]) for v in variants],
                        "avg_ticks": [round(T["base"][v]["ticks"].mean(), 3) for v in variants]}, index=variants)
    stress = {lab: round(float(oos_tr[lab]["net_pnl"].sum()), 1) for lab in scen}
    out = ROOT / "vault" / "results" / "h003-report.md"
    out.write_text("\n".join([
        "---", "type: result", f"date: {date.today().isoformat()}", "tags: [phase-5, H-003, gates]", "---",
        f"# H-003 evaluation (D-023): gate verdict **{verdict}**", "",
        f"{hyp.title}. {len(dates)} trading dates {dates[0]}..{dates[-1]}; {len(folds)} folds (3 y train / 1 y test). "
        f"DSR N = {max(len(variants), n_global)}. Costs: 1 tick adverse per side + fees (stress 2 ticks + fees x1.5).", "",
        "## Gates", md(table), "", "## Out-of-sample", "```", json.dumps(
            {k: (round(v, 4) if isinstance(v, float) else v) for k, v in ts_oos.items()}, indent=1), "```",
        f"Net by scenario: {stress}", "", "### By year (OOS)", md(by_year), "",
        "## Variant chosen per fold", md(pd.DataFrame(chosen), index=False), "",
        f"## Family: PBO = {pbo['pbo']:.3f}, K = {cl['k']}", "", md(fam), ""]) + "\n")
    print(table.to_string())
    print("verdict:", verdict, "| OOS:", {k: ts_oos.get(k) for k in ("trades", "net_pnl", "avg_ticks", "t_stat")})
    print(by_year.to_string())
    print("saved", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
