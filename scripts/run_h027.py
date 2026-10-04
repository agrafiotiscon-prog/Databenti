"""H-027: pre-FOMC drift replication on NQ/RTY/YM daily bars (registry H-027). Single evaluation.

  python scripts/run_h027.py [--coverage-only]

Coverage (FOMC events found per market vs expected, D-042) is printed and written before any P&L.
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
from data.universe import BY_ROOT                           # noqa: E402
from portfolio.data import build, chain_returns, load_bars  # noqa: E402
from research import registry, trials                       # noqa: E402
from scripts.fetch_futures_daily import path_for            # noqa: E402
from scripts.run_h001 import md                             # noqa: E402
from strategies.h007 import fomc_dates                      # noqa: E402

HYP, MARKETS, NOTIONAL = "H-027", ("NQ", "RTY", "YM"), 1_000_000.0 / 3


def day_pnl(rd, slip_ticks: float, fee_side: float) -> pd.Series:
    """Net $ of a one-day long (close t-1 -> close t) for every date, $333k notional in integer contracts."""
    spec = BY_ROOT[rd.root]
    r = chain_returns(rd)
    out = {}
    for prev, d in zip(rd.dates, rd.dates[1:]):
        px = rd.closes[rd.held[prev]].get(prev)
        if np.isnan(r[d]) or px is None or px <= 0:
            continue
        n = max(1, int(round(NOTIONAL / (px * spec.point_value))))
        out[d] = n * (r[d] * px * spec.point_value - 2 * (slip_ticks * spec.tick_value + fee_side))
    return pd.Series(out, dtype=float)


def pooled(daily: list[pd.Series], days) -> pd.Series:
    """Sum over markets of the one-day P&L on `days` (markets without a bar that day are skipped)."""
    df = pd.concat(daily, axis=1)
    return df.loc[df.index.isin(set(days))].sum(axis=1, min_count=1).dropna().sort_index()


def main(argv=None) -> int:
    from data.download import Downloader
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--coverage-only", action="store_true")
    ap.add_argument("--draws", type=int, default=2000)
    a = ap.parse_args(argv)
    hyp = registry.load(HYP)
    if not a.coverage_only and (hyp.status != "open" or trials.count(hypothesis=HYP) >= hyp.trial_budget):
        raise SystemExit(f"{HYP}: closed or already evaluated (single evaluation).")
    dl = Downloader()
    rds = [build(m, load_bars(path_for(dl, f"{m}.v.0")), load_bars(path_for(dl, f"{m}.v.1"))) for m in MARKETS]
    for rd in rds:
        holdout_check(rd.dates)
    cov = []
    for rd in rds:
        lo, hi = rd.dates[1], rd.dates[-1]
        exp = [d for d in fomc_dates() if lo <= d <= hi]
        found = [d for d in exp if d in set(rd.dates)]
        cov.append({"market": rd.root, "first": lo, "last": hi, "fomc_expected": len(exp), "fomc_found": len(found),
                    "missing": ", ".join(str(d) for d in exp if d not in set(rd.dates)) or "-"})
    cov = pd.DataFrame(cov)
    print(cov.to_string(), flush=True)
    if a.coverage_only:
        return 0
    c = load_costs()
    fee = c.fee(1)
    fomc = set(fomc_dates())
    D = [day_pnl(rd, 1.0, fee) for rd in rds]
    base, stress = pooled(D, fomc), pooled([day_pnl(rd, 2.0, fee * 1.5) for rd in rds], fomc)
    per = {rd.root: d[d.index.isin(fomc)] for rd, d in zip(rds, D)}
    n = len(base)
    mean, t = float(base.mean()), float(base.mean() / base.std() * np.sqrt(n))
    # placebo: random non-FOMC days, same count, same markets (RTY only exists from 2017 - draws use its dates too)
    allp = pd.concat(D, axis=1).sum(axis=1, min_count=1).dropna()
    cal = list(allp.index)
    pool = allp[~allp.index.isin(fomc)].to_numpy()
    rng = np.random.default_rng(27)
    sims = np.array([rng.choice(pool, size=n, replace=False).sum() for _ in range(a.draws)])
    p = float((sims >= base.sum()).mean())
    verdict = "REPLICATES" if mean > 0 and t >= 2 and p <= 0.05 else "DOES NOT REPLICATE"
    yrs = base.groupby([d.year for d in base.index]).agg(["count", "sum"]).round(0)
    pm = pd.DataFrame({m: {"events": len(s), "net": round(s.sum()), "mean": round(s.mean()), "win_rate": round((s > 0).mean(), 3),
                           "t": round(s.mean() / s.std() * np.sqrt(len(s)), 2)} for m, s in per.items()}).T
    res = {"verdict": verdict, "events": n, "net": round(float(base.sum())), "mean_per_event": round(mean),
           "t": round(t, 3), "win_rate": round(float((base > 0).mean()), 3), "net_stress": round(float(stress.sum())),
           "placebo_p": round(p, 4), "placebo_median": round(float(np.median(sims)))}
    trials.append({"family": HYP, "hypothesis": HYP, "params": {"variant": "fixed"},
                   "data": f"NQ/RTY/YM ohlcv-1d v.0 {cal[0]}..{cal[-1]}", "fill_mode": "close-to-close, 1 tick + fees per side",
                   "results": res})
    out = ROOT / "vault" / "results" / "h027-report.md"
    out.write_text("\n".join([
        "---", "type: result", f"date: {date.today().isoformat()}", "tags: [R8, H-027, FOMC, replication]", "---",
        f"# H-027 pre-FOMC drift on NQ/RTY/YM daily bars: **{verdict}**", "",
        "Pre-registered: REPLICATES if pooled mean > 0, per-event t >= 2 and placebo p <= 0.05 (registry H-027).",
        "Window: UTC-day close before the statement day -> statement-day close (includes the 14:00 ET reaction).", "",
        "## Coverage (before P&L)", md(cov, index=False), "", "## Result (pooled, $333k notional per market)", "",
        "```", "\n".join(f"{k}: {v}" for k, v in res.items()), "```", "", "## Per market", md(pm), "",
        "## By year (pooled)", md(yrs), ""]) + "\n")
    print(res); print(pm.to_string()); print(yrs.to_string()); print("saved", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
