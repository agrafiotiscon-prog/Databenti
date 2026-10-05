"""H-046: hedgers' liquidity provision (Kang, Rouwenhorst & Tang 2020), tradable days 5-20 only. Single evaluation.

  python scripts/run_h046.py [--coverage-only] [--draws 1000]
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
from data.cot import hedger_change, load_cot                # noqa: E402
from data.holdout import check as holdout_check             # noqa: E402
from data.universe import BY_ROOT                           # noqa: E402
from portfolio.data import build, load_bars                 # noqa: E402
from research import registry, trials                       # noqa: E402
from research.daily_eval import Outright, window_pnl        # noqa: E402
from scripts.fetch_futures_daily import path_for            # noqa: E402
from scripts.run_h001 import md                             # noqa: E402
from scripts.run_h041 import SPECS as EXTRA                 # noqa: E402

HYP = "H-046"
ROOTS = ["CL", "NG", "RB", "HO", "GC", "SI", "HG", "PL", "PA", "ZC", "ZS", "ZW", "KE", "ZL", "ZM", "LE", "HE", "GF"]
ENTRY, EXIT, NOTIONAL = 5, 20, 1_000_000.0
SHUTDOWNS = [(date(2013, 10, 1), date(2013, 10, 29)), (date(2018, 12, 24), date(2019, 2, 26))]
FIRST, LAST = date(2010, 6, 7), date(2025, 9, 30)


def sides_from(sig: pd.DataFrame) -> pd.DataFrame:
    """+1 top floor(n/2), -1 bottom floor(n/2) per row (NaN = market unavailable), 0 otherwise."""
    out = pd.DataFrame(0, index=sig.index, columns=sig.columns)
    for t, row in sig.iterrows():
        x = row.dropna()
        h = len(x) // 2
        if h == 0:
            continue
        o = x.sort_values(kind="mergesort")
        out.loc[t, o.index[-h:]] = 1
        out.loc[t, o.index[:h]] = -1
    return out


def cohort_window(m: Outright, t: date):
    """(entry, exit) dates: closes of the ENTRY-th and EXIT-th trading day after as-of date t (market's calendar)."""
    i0 = int(np.searchsorted(np.array(m.dates), t, side="right")) - 1     # last trading day <= t
    if i0 < 0 or i0 + EXIT >= len(m.dates):
        return None
    return m.dates[i0 + ENTRY], m.dates[i0 + EXIT]


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
    for r in ROOTS:
        spec = EXTRA.get(r) or BY_ROOT[r]
        rd = build(r, load_bars(path_for(dl, f"{r}.v.0")), load_bars(path_for(dl, f"{r}.v.1")))
        holdout_check(rd.dates)
        M[r] = Outright(rd, spec.point_value, spec.tick_value)
    dH = hedger_change(load_cot())[ROOTS]
    keep = [t for t in dH.index if FIRST <= t and not any(s <= t <= e for s, e in SHUTDOWNS)]
    dH = dH.loc[keep]
    # weekly Tuesday-to-Tuesday own return (reversal benchmark), from the market's closes on/before each as-of date
    rev = pd.DataFrame(index=dH.index, columns=ROOTS, dtype=float)
    for r, m in M.items():
        cum = pd.Series(np.nancumsum(np.nan_to_num(m.r)), index=m.dates)
        at = cum.reindex(pd.Index(sorted(set(m.dates) | set(dH.index)))).ffill().reindex(dH.index)
        rev[r] = -(at - at.shift())
    # cohort windows per (week, market); a market is available if it has dH, a window and a price
    W = {}
    for t in dH.index:
        for r, m in M.items():
            w = cohort_window(m, t)
            if w is not None and w[1] <= LAST and np.isfinite(dH.loc[t, r]):
                W[(t, r)] = w
    avail = pd.DataFrame(np.nan, index=dH.index, columns=ROOTS)
    for (t, r) in W:
        avail.loc[t, r] = 1.0
    dH, rev = dH.where(avail.notna()), rev.where(avail.notna() & rev.notna())
    cov = pd.DataFrame({"weeks_with_signal": dH.notna().sum(), "first_week": dH.apply(lambda s: s.first_valid_index()),
                        "last_week": dH.apply(lambda s: s.last_valid_index()),
                        "returns_ok": pd.Series({r: round(float(np.isfinite(M[r].r[1:]).mean()), 4) for r in ROOTS}),
                        "median_close": pd.Series({r: round(float(np.nanmedian(M[r].px)), 3) for r in ROOTS})})
    print(cov.to_string(), f"\nweeks: {len(dH)}, cohorts: {len(W)}", flush=True)
    if a.coverage_only:
        return 0

    def daily(sides: pd.DataFrame, slip: float, fm: float) -> pd.Series:
        parts = []
        for r, m in M.items():
            ws = [(W[(t, r)][0], W[(t, r)][1], int(sides.loc[t, r])) for t in sides.index
                  if (t, r) in W and sides.loc[t, r] != 0]
            parts.append(window_pnl(m, ws, NOTIONAL, slip, fee * fm)[0])
        return pd.concat(parts, axis=1).sum(axis=1, min_count=1).fillna(0.0)

    S = sides_from(dH)
    base, stress = daily(S, 1.0, 1.0), daily(S, 2.0, 1.5)
    bench = daily(sides_from(rev), 1.0, 1.0)
    x = pd.concat([base, bench], axis=1).fillna(0.0)
    x = x[(x.index >= FIRST) & (x.index <= LAST)]
    y, b = x.iloc[:, 0].to_numpy(), x.iloc[:, 1].to_numpy()
    t_daily = float(y.mean() / y.std() * np.sqrt(len(y)))
    X = np.c_[np.ones(len(b)), b]
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    se = np.sqrt(np.diag(np.linalg.inv(X.T @ X)) * resid.var(ddof=2))
    t_alpha = float(beta[0] / se[0])
    # placebo: per (week, market) gross P&L of a long cohort and its cost, then random week-to-week signal swaps
    g_long, cost = {}, {}
    for (t, r), (s0, e0) in W.items():
        m = M[r]
        net1, cnt = window_pnl(m, [(s0, e0, 1)], NOTIONAL, 1.0, fee)
        c = float((cnt * (1.0 * m.tv + fee)).sum())
        g_long[(t, r)], cost[(t, r)] = float(net1.sum()) + c, c
    weeks = list(dH.index)
    G = np.array([[g_long.get((t, r), 0.0) for r in ROOTS] for t in weeks])
    C = np.array([[cost.get((t, r), 0.0) for r in ROOTS] for t in weeks])
    A = avail.loc[weeks].notna().to_numpy()
    real = float((S.loc[weeks].to_numpy() * G - (S.loc[weeks].to_numpy() != 0) * C).sum())
    rng = np.random.default_rng(46)
    dHv = dH.loc[weeks].to_numpy()
    sims = []
    for _ in range(a.draws):
        perm = rng.permutation(len(weeks))
        sig = np.where(A, dHv[perm], np.nan)                    # another week's signal on this week's markets
        sig = np.where(A & np.isnan(sig), np.nanmedian(dHv), sig)
        sd = sides_from(pd.DataFrame(np.where(A, sig, np.nan), columns=ROOTS)).to_numpy()
        sims.append(float((sd * G - (sd != 0) * C).sum()))
    sims = np.array(sims)
    p = float((sims >= real).mean())
    crit = {"stress_net_pos": bool(stress.sum() > 0), "t_daily_ge_2": t_daily >= 2, "t_alpha_vs_reversal_ge_2": t_alpha >= 2,
            "placebo_p_le_0.05": p <= 0.05}
    verdict = "CONFIRMS" if all(crit.values()) else "DOES NOT CONFIRM"
    yrs = (base.groupby([d.year for d in base.index]).sum()).round(0)
    sector = {r: (EXTRA.get(r) or BY_ROOT[r]).sector for r in ROOTS}
    per_mkt = pd.Series({r: float((S[r].to_numpy() * G[:, i] - (S[r].to_numpy() != 0) * C[:, i]).sum())
                         for i, r in enumerate(ROOTS)})
    by_sector = per_mkt.groupby(sector).sum().round(0)
    legs = {leg: float(((S.to_numpy() == sgn) * (sgn * G - C)).sum()) for leg, sgn in (("long", 1), ("short", -1))}
    early = base[[d.year <= 2012 for d in base.index]]
    late = base[[d.year > 2012 for d in base.index]]
    tt = lambda s: round(float(s.mean() / s.std() * np.sqrt(len(s))), 2) if s.std() > 0 else 0.0   # noqa: E731
    gross_notional = float((S != 0).to_numpy().sum()) * NOTIONAL
    res = {"verdict": verdict, **crit, "weeks": len(weeks), "cohort_positions": int((S != 0).to_numpy().sum()),
           "net": round(float(base.sum())), "net_stress": round(float(stress.sum())),
           "net_per_position_bp": round(1e4 * float(base.sum()) / gross_notional, 2),
           "t_daily": round(t_daily, 3), "alpha_t_vs_reversal": round(t_alpha, 3), "beta_on_reversal": round(float(beta[1]), 3),
           "corr_with_reversal": round(float(np.corrcoef(y, b)[0, 1]), 3), "reversal_net": round(float(bench.sum())),
           "placebo_p": round(p, 4), "placebo_median": round(float(np.median(sims))),
           "t_2010_2012": tt(early), "t_2013_2025": tt(late), "years_positive": f"{int((yrs > 0).sum())}/{len(yrs)}",
           "long_leg": round(legs["long"]), "short_leg": round(legs["short"])}
    trials.append({"family": HYP, "hypothesis": HYP, "params": {"variant": "fixed"},
                   "data": "18 commodity futures ohlcv-1d v.0/v.1 2010-06..2025-09 + CFTC COT legacy futures-only",
                   "fill_mode": "closes, 1 tick + fees per side, per cohort", "results": res})
    out = ROOT / "vault" / "results" / "h046-report.md"
    out.write_text("\n".join([
        "---", "type: result", f"date: {date.today().isoformat()}", "tags: [R15, H-046, cftc, hedging-pressure, confirmation]", "---",
        f"# H-046 hedgers' liquidity provision (CFTC COT, tradable days 5-20): **{verdict}**", "",
        "Pre-registered (research/hypotheses/H-046.yaml, committed before the run): fixed rule from Kang, Rouwenhorst & Tang "
        "(2020 JF); CONFIRMS only if stress net > 0, daily t >= 2, alpha t >= 2 beyond a reversal benchmark and week-shuffle "
        "placebo p <= 0.05. $1M notional per market per weekly cohort, ~9 long / 9 short.", "",
        "## Coverage (before P&L)", md(cov), "", "## Result", "```", "\n".join(f"{k}: {v}" for k, v in res.items()), "```", "",
        "## By sector ($)", md(by_sector.to_frame("net")), "", "## By year ($)", md(yrs.to_frame("net")), ""]) + "\n")
    print(res); print(by_sector.to_string()); print(yrs.to_string()); print("saved", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
