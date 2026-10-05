"""H-041: trend252 unchanged on 12 CME markets never used for trend (out-of-sample confirmation). Single evaluation.

  python scripts/run_h041.py [--coverage-only]
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
from portfolio.engine import prepare, simulate              # noqa: E402
from research import registry, trials                       # noqa: E402
from scripts.fetch_futures_daily import path_for            # noqa: E402
from scripts.run_h001 import md                             # noqa: E402

HYP, CAPITAL, START_PNL = "H-041", 1_000_000.0, date(2011, 6, 1)
# point value = USD per 1.00 of the quoted price; tick in quoted units [doc: CME contract specs; PA tick assumption]
SPECS = {
    "TN": Spec("TN", "rates", 1000, 1 / 64), "UB": Spec("UB", "rates", 1000, 1 / 32),
    "6N": Spec("6N", "fx", 100_000, 0.00005), "6M": Spec("6M", "fx", 500_000, 0.00001),
    "KE": Spec("KE", "grains", 50, 0.25), "ZL": Spec("ZL", "grains", 600, 0.01), "ZM": Spec("ZM", "grains", 100, 0.1),
    "GF": Spec("GF", "livestock", 500, 0.025), "PL": Spec("PL", "metals", 50, 0.1), "PA": Spec("PA", "metals", 100, 0.5),
    "EMD": Spec("EMD", "equity", 100, 0.1), "NKD": Spec("NKD", "equity", 5, 5.0),
}
FIRST = {"TN": date(2016, 1, 11)}          # TN root before 2016 is a different, illiquid product (H-032)


def load(dl, r):
    v0, v1 = (load_bars(path_for(dl, f"{r}.v.{k}")) for k in (0, 1))
    f = FIRST.get(r)
    if f:
        v0, v1 = v0[v0.index >= f], v1[v1.index >= f]
    return build(r, v0, v1)


def stats(x: pd.Series) -> dict:
    a, v = x.mean() * 252 / CAPITAL, x.std() * np.sqrt(252) / CAPITAL
    dd = (x.cumsum() - x.cumsum().cummax()).min() / CAPITAL
    return {"ann_return_pct": round(100 * a, 2), "ann_vol_pct": round(100 * v, 2), "sharpe": round(a / v, 3) if v > 0 else None,
            "max_dd_pct": round(100 * dd, 1), "net": round(float(x.sum()))}


def main(argv=None) -> int:
    from data.download import Downloader
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--coverage-only", action="store_true")
    ap.add_argument("--draws", type=int, default=300)
    a = ap.parse_args(argv)
    hyp = registry.load(HYP)
    if not a.coverage_only and (hyp.status != "open" or trials.count(hypothesis=HYP) >= hyp.trial_budget):
        raise SystemExit(f"{HYP}: closed or already evaluated (single evaluation).")
    dl = Downloader()
    rds = {r: load(dl, r) for r in SPECS}
    for rd in rds.values():
        holdout_check(rd.dates)
    preps = [prepare(rd) for rd in rds.values()]
    cov = pd.DataFrame([{"market": p.root, "first": p.dates[0], "last": p.dates[-1], "days": len(p.dates),
                         "returns_ok": round(float(p.r.notna().mean()), 4), "median_close": round(float(p.price.median()), 5),
                         "notional_per_contract": round(float(p.price.median() * SPECS[p.root].point_value)),
                         "max_abs_ret": round(float(p.r.abs().max()), 3)} for p in preps])
    print(cov.to_string(), flush=True)
    if a.coverage_only:
        return 0
    fee = load_costs().fee(1)
    cal = sorted(set().union(*[p.dates for p in preps]))

    def run(slip, fm, override=None):
        n = simulate(preps, "trend252", CAPITAL, slip, fee * fm, signal_override=override, specs=SPECS)["net"]
        n = n.reindex(cal).fillna(0.0)
        return n[n.index >= START_PNL]

    base, stress = run(1.0, 1.0), run(2.0, 1.5)
    rng = np.random.default_rng(41)
    sims = []
    for _ in range(a.draws):
        ov = {}
        for p in preps:
            s = p.signals["trend252"]
            k = int(rng.integers(63, max(64, len(s) - 63)))
            ov[p.root] = pd.Series(np.roll(s.to_numpy(), k), index=s.index)
        sims.append(float(run(1.0, 1.0, ov).sum()))
    sims = np.array(sims)
    p = float((sims >= base.sum()).mean())
    st = stats(base)
    crit = {"stress_net_pos": bool(stress.sum() > 0), "sharpe_ge_0.25": (st["sharpe"] or 0) >= 0.25, "placebo_p_le_0.05": p <= 0.05}
    verdict = "CONFIRMS" if all(crit.values()) else "DOES NOT CONFIRM"
    det = simulate(preps, "trend252", CAPITAL, 1.0, fee, specs=SPECS, detail=True)
    det = det[det["date"] >= START_PNL]
    by_mkt = det.groupby("root")["net"].sum().round(0).sort_values()
    yrs = base.groupby([d.year for d in base.index]).sum()
    old = pd.read_csv(ROOT / "research" / "daily" / "H-022" / "trend252.csv", index_col=0)["net_pnl"]
    old.index = pd.to_datetime(old.index).date
    j = pd.DataFrame({"new12": base, "orig26": old}).dropna()
    corr = round(float(j.corr().iloc[0, 1]), 3)
    both = (j["new12"] + j["orig26"])
    res = {"verdict": verdict, **crit, **st, "net_stress": round(float(stress.sum())), "placebo_p": round(p, 4),
           "placebo_median": round(float(np.median(sims))), "years_positive": f"{int((yrs > 0).sum())}/{len(yrs)}",
           "corr_with_orig26": corr}
    trials.append({"family": HYP, "hypothesis": HYP, "params": {"variant": "fixed"},
                   "data": "12 CME futures ohlcv-1d v.0/v.1 (never used for trend) 2010-06..2025-09",
                   "fill_mode": "trend252 engine, next-day close, 1 tick + fees", "results": res})
    out = ROOT / "vault" / "results" / "h041-report.md"
    out.write_text("\n".join([
        "---", "type: result", f"date: {date.today().isoformat()}", "tags: [R12, H-041, trend, confirmation]", "---",
        f"# H-041 trend252 on 12 never-used markets: **{verdict}**", "",
        "Pre-registered (research/hypotheses/H-041.yaml, committed before the data was downloaded): CONFIRMS only if stress net > 0, "
        "Sharpe >= 0.25 and circular-shift placebo p <= 0.05. Rule unchanged; $1M; P&L from 2011-06.", "",
        "## Coverage and quoted units (before P&L)", md(cov, index=False), "",
        "## Result", "```", "\n".join(f"{k}: {v}" for k, v in res.items()), "```", "",
        "## By year (% of $1M)", md((100 * yrs / CAPITAL).round(2).to_frame("return_pct")), "",
        "## By market (net $)", md(by_mkt.to_frame("net")), "",
        "## Descriptive: 26 original + 12 new markets as two equal-capital trend books (simple sum, not re-optimised)",
        f"Sum of both books: {stats(both)}; correlation of daily P&L {corr}.", ""]) + "\n")
    print(res); print(by_mkt.to_string()); print("saved", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
