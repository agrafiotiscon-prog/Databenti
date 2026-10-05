"""FOMC-window confirmations on rates and FX (single evaluation each, fixed rules from the literature):
  H-044: long ZT/ZF/ZN/ZB/TN/UB over the 3-day window day-1..day+1 around the FOMC announcement (Hillenbrand 2025)
  H-045: long 8 CME FX futures (= short USD) on the FOMC announcement day (Mueller, Tahbaz-Salehi & Vedolin 2017)

  python scripts/run_fomc_xasset.py --hypothesis H-044|H-045 [--coverage-only] [--draws 1000]
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
from portfolio.data import build, load_bars                 # noqa: E402
from research import registry, trials                       # noqa: E402
from research.daily_eval import Outright, window_pnl        # noqa: E402
from scripts.fetch_futures_daily import path_for            # noqa: E402
from scripts.run_h001 import md                             # noqa: E402
from scripts.run_r9 import by_month                         # noqa: E402

EXTRA = {"TN": Spec("TN", "rates", 1000, 1 / 64), "UB": Spec("UB", "rates", 1000, 1 / 32),
         "6N": Spec("6N", "fx", 100_000, 0.00005), "6M": Spec("6M", "fx", 500_000, 0.00001)}
FIRST = {"TN": date(2016, 1, 11)}           # earlier TN bars are a different, illiquid product (see run_h032)
# hypothesis -> (markets, reference calendar market, bars before the announcement day, bars after, notional)
CONF = {"H-044": (["ZT", "ZF", "ZN", "ZB", "TN", "UB"], "ZN", 2, 1, 250_000.0),
        "H-045": (["6E", "6J", "6B", "6A", "6C", "6S", "6N", "6M"], "6E", 1, 0, 125_000.0)}
PAPER_END = {"H-044": 2017, "H-045": 2014}
GAP = 5                                      # placebo anchors at least this many trading days from any FOMC day


def fomc_dates() -> list[date]:
    df = pd.read_csv(ROOT / "config" / "fomc_dates.csv", comment="#")
    return [date.fromisoformat(s) for s in df["date"]]


def windows(m: Outright, anchors, pre: int, post: int) -> list[tuple]:
    """(close `pre` bars before the anchor, close `post` bars after it, long) for anchors traded in m."""
    out = []
    for a in anchors:
        i = m.pos_i.get(a)
        if i is not None and i - pre >= 0 and i + post < len(m.dates):
            out.append((m.dates[i - pre], m.dates[i + post], 1))
    return out


def placebo_pool(cal: list[date], events: list[date]) -> list[list[date]]:
    """For each FOMC meeting, the candidate trading days until the next meeting that are >= GAP days from any
    FOMC day (one random draw per meeting keeps the number of windows equal to the real one)."""
    pos = {d: i for i, d in enumerate(cal)}
    ev_i = sorted(pos[d] for d in events if d in pos)
    pools = []
    for a, b in zip(ev_i, ev_i[1:] + [len(cal)]):
        cand = [cal[j] for j in range(a + GAP, b - GAP + 1) if 0 <= j < len(cal)]
        if cand:
            pools.append(cand)
    return pools


def month_end_days(m: Outright, k: int = 3) -> set:
    """Exposure days of the H-030 window: the last k trading days of each month."""
    return {d for ds in by_month(m.dates).values() for d in ds[-k:]}


def main(argv=None) -> int:
    from data.download import Downloader
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--hypothesis", choices=sorted(CONF), required=True)
    ap.add_argument("--coverage-only", action="store_true")
    ap.add_argument("--draws", type=int, default=1000)
    a = ap.parse_args(argv)
    HYP = a.hypothesis
    roots, ref, PRE, POST, NOTIONAL = CONF[HYP]
    hyp = registry.load(HYP)
    if not a.coverage_only and (hyp.status != "open" or trials.count(hypothesis=HYP) >= hyp.trial_budget):
        raise SystemExit(f"{HYP}: closed or already evaluated (single evaluation).")
    dl = Downloader()
    fee = load_costs().fee(1)
    M, cov = {}, []
    for r in roots:
        spec = EXTRA.get(r) or BY_ROOT[r]
        v0, v1 = (load_bars(path_for(dl, f"{r}.v.{k}")) for k in (0, 1))
        if r in FIRST:
            v0, v1 = v0[v0.index >= FIRST[r]], v1[v1.index >= FIRST[r]]
        rd = build(r, v0, v1)
        holdout_check(rd.dates)
        M[r] = Outright(rd, spec.point_value, spec.tick_value)
    fomc = [d for d in fomc_dates() if M[ref].dates[0] <= d <= M[ref].dates[-1]]
    for r, m in M.items():
        ev = [d for d in fomc if m.dates[0] <= d <= m.dates[-1]]
        cov.append({"market": r, "first": m.dates[0], "last": m.dates[-1], "fomc_in_range": len(ev),
                    "fomc_traded": sum(d in m.pos_i for d in ev), "windows": len(windows(m, ev, PRE, POST)),
                    "returns_ok": round(float(np.isfinite(m.r[1:]).mean()), 4),
                    "median_close": round(float(np.nanmedian(m.px)), 5)})
    cov = pd.DataFrame(cov)
    print(cov.to_string(), flush=True)
    if a.coverage_only:
        return 0

    def pooled(anchors, slip, fm):
        return pd.concat([window_pnl(M[r], windows(M[r], anchors, PRE, POST), NOTIONAL, slip, fee * fm)[0]
                          for r in roots], axis=1).sum(axis=1, min_count=1).fillna(0.0)

    base, stress = pooled(fomc, 1.0, 1.0), pooled(fomc, 2.0, 1.5)
    L = PRE + POST
    rows, excess = [], []
    for r in roots:
        m = M[r]
        w = windows(m, fomc, PRE, POST)
        net, _ = window_pnl(m, w, NOTIONAL, 1.0, fee)
        allL = pd.Series(m.r).rolling(L).sum().dropna().to_numpy()
        me = month_end_days(m)
        for s, e, _ in w:
            i0, i1 = m.pos_i[s], m.pos_i[e]
            ret = float(np.nansum(m.r[i0 + 1:i1 + 1]))
            excess.append(ret - allL.mean())
            rows.append({"market": r, "fomc": m.dates[i0 + PRE], "ret_bp": ret * 1e4,
                         "pnl": float(net.iloc[i0:i1 + 1].sum()),
                         "month_end_overlap": any(d in me for d in m.dates[i0 + 1:i1 + 1])})
    W = pd.DataFrame(rows)
    excess = np.array(excess)

    def tstat(x):
        x = np.asarray(x, float)
        return float(x.mean() / x.std() * np.sqrt(len(x))) if len(x) > 1 and x.std() > 0 else 0.0

    t_win, t_ex = tstat(W["pnl"]), tstat(excess)
    t_nome = tstat(W.loc[~W["month_end_overlap"], "pnl"])
    pools = placebo_pool(M[ref].dates, fomc)
    rng = np.random.default_rng(44 if HYP == "H-044" else 45)
    sims = np.array([pooled([p[int(rng.integers(len(p)))] for p in pools], 1.0, 1.0).sum() for _ in range(a.draws)])
    p = float((sims >= base.sum()).mean())
    crit = {"stress_net_pos": bool(stress.sum() > 0), "t_window_ge_2": t_win >= 2, "t_drift_neutral_ge_2": t_ex >= 2,
            "placebo_p_le_0.05": p <= 0.05}
    if HYP == "H-044":
        crit["t_no_month_end_ge_2"] = t_nome >= 2
    verdict = "CONFIRMS" if all(crit.values()) else "DOES NOT CONFIRM"
    W["year"] = [d.year for d in W["fomc"]]
    W["period"] = np.where(W["year"] <= PAPER_END[HYP], f"<= {PAPER_END[HYP]} (paper overlap)",
                           f"> {PAPER_END[HYP]} (post-sample)")
    per = W.groupby("market").agg(windows=("pnl", "size"), net=("pnl", "sum"), mean_bp=("ret_bp", "mean"),
                                  win_rate=("pnl", lambda s: (s > 0).mean())).round(2)
    yrs = W.groupby("year")["pnl"].sum().round(0)
    period = W.groupby("period").agg(windows=("pnl", "size"), net=("pnl", "sum"), mean_bp=("ret_bp", "mean"),
                                     t=("pnl", tstat)).round(2)
    res = {"verdict": verdict, **crit, "windows": int(len(W)), "net": round(float(base.sum())),
           "net_stress": round(float(stress.sum())), "t_window": round(t_win, 3), "t_drift_neutral": round(t_ex, 3),
           "t_no_month_end": round(t_nome, 3), "month_end_overlap_share": round(float(W["month_end_overlap"].mean()), 3),
           "placebo_p": round(p, 4), "placebo_median": round(float(np.median(sims))),
           "years_positive": f"{int((yrs > 0).sum())}/{len(yrs)}"}
    trials.append({"family": HYP, "hypothesis": HYP, "params": {"variant": "fixed"},
                   "data": f"{'/'.join(roots)} ohlcv-1d v.0/v.1 2010-06..2025-09, FOMC window -{PRE}..+{POST}",
                   "fill_mode": "closes, 1 tick + fees per side", "results": res})
    title = {"H-044": "Treasury futures, long day-1..day+1 around FOMC", "H-045": "FX futures, short USD on FOMC days"}[HYP]
    out = ROOT / "vault" / "results" / f"{HYP.lower().replace('-', '')}-report.md"
    out.write_text("\n".join([
        "---", "type: result", f"date: {date.today().isoformat()}", f"tags: [R15, {HYP}, fomc, confirmation]", "---",
        f"# {HYP} {title}: **{verdict}**", "",
        f"Pre-registered (research/hypotheses/{HYP}.yaml, committed before the run). Fixed rule from the paper, "
        f"single evaluation, ${NOTIONAL:,.0f} notional per market, 2010-06..2025-09 (development data only).", "",
        "## Coverage (before P&L)", md(cov, index=False), "",
        "## Result", "```", "\n".join(f"{k}: {v}" for k, v in res.items()), "```", "",
        "## Paper overlap vs post-sample", md(period), "",
        "## Per market", md(per), "", "## By year (pooled $)", md(yrs.to_frame("net")), ""]) + "\n")
    print(res); print(period.to_string()); print(per.to_string()); print(yrs.to_string()); print("saved", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
