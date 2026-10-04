"""Shared single-evaluation pipeline for hypotheses expressed as daily P&L per variant (R9).

Same protocol as scripts/run_portfolio.py (D-023): walk-forward 36/12/12 months, variant chosen on the
train block-bootstrap net p5 at fees x1.5, OOS stitched from the chosen variants, gates G1-G12 via
research.gates. The caller supplies the daily P&L per scenario and variant, the trade counts and a
placebo function; this module logs every variant through research.trials.append and writes the report.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

from backtest.metrics import concentration, drawdown
from research import clusters, gates, stats, trials
from research.walkforward import walk_forward

SCENARIOS = ("base", "fees1.5", "stress", "plus1tick")


def oos_stats(daily: pd.Series, capital: float) -> dict:
    ann = daily.mean() * 252 / capital
    vol = daily.std() * np.sqrt(252) / capital
    dd = drawdown(daily)
    return {"ann_return_pct": round(100 * float(ann), 2), "ann_vol_pct": round(100 * float(vol), 2),
            "sharpe": round(float(ann / vol), 3) if vol > 0 else None,
            "max_dd_pct": round(100 * float(dd.get("max_drawdown", np.nan)) / capital, 2) if dd else None,
            "t_daily": round(float(daily.mean() / daily.std() * np.sqrt(len(daily))), 3) if daily.std() > 0 else None}


def evaluate(hyp, D: dict[str, pd.DataFrame], trades: pd.DataFrame, capital: float,
             placebo: Callable[[str, list, int], np.ndarray], data_desc: str, fill_desc: str,
             out: Path, title: str, notes: list[str] | None = None, n_placebo: int = 300) -> dict:
    """D[scenario] = DataFrame(index=dates, columns=variants) of daily net $; trades = DataFrame of trade
    counts per date and variant. placebo(variant, oos_dates, n) -> array of n placebo OOS nets."""
    variants = list(D["base"].columns)
    cal = list(D["base"].index)
    folds = walk_forward(cal, train_months=36, test_months=12, step_months=12, embargo_days=1)
    chosen, oos = [], {lab: [] for lab in SCENARIOS}
    oos_trades = 0
    for f in folds:
        rows = [d for d in f.train if d in D["fees1.5"].index]
        sc = {v: stats.block_bootstrap(D["fees1.5"].loc[rows, v], n_sims=500, seed=f.k)["net_p5"] for v in variants}
        best = max(sc, key=sc.get)
        test = [d for d in f.test if d in D["base"].index]
        chosen.append({"fold": f.k, "test": f"{f.test[0]}..{f.test[-1]}", "variant": best, "train_net_p5": round(sc[best])})
        for lab in SCENARIOS:
            oos[lab].append(D[lab].loc[test, best])
        oos_trades += int(trades.loc[test, best].sum())
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
    st = oos_stats(od["base"], capital)
    real = float(od["base"].sum())
    sims = np.asarray(placebo(final, oos_dates, n_placebo), dtype=float)
    placebo_p = float((sims >= real).mean())
    evidence = {
        "oos_trades": oos_trades, "oos_net_stress": float(od["stress"].sum()),
        "dsr_raw": stats.dsr(od["base"], srs, n_trials=n_global), "oos_t": st["t_daily"],
        "pbo": pbo["pbo"], "plateau_pass": stats.plateau_test(full_net[fi], nb)["pass"] if nb else False,
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
    for v in variants:
        s = oos_stats(D["base"][v], capital)
        params = dict(zip(hyp.space.keys(), v.split("|")))
        params = {k: type(hyp.space[k][0])(x) if not isinstance(hyp.space[k][0], bool) else x == "True"
                  for k, x in params.items()}
        trials.append({"family": hyp.id, "hypothesis": hyp.id, "params": params, "data": data_desc, "fill_mode": fill_desc,
                       "results": {"net_full_period": round(float(D["base"][v].sum()), 2), "trades": int(trades[v].sum()), **s}})
    by_year = pd.DataFrame({"oos_net": yrs.round(0), "return_pct": (100 * yrs / capital).round(2)})
    fam = pd.DataFrame({v: {**oos_stats(D["base"][v], capital), "net_full": round(float(D["base"][v].sum())),
                            "trades": int(trades[v].sum())} for v in variants}).T
    from scripts.run_h001 import md
    out.write_text("\n".join([
        "---", "type: result", f"date: {date.today().isoformat()}", f"tags: [R9, {hyp.id}, gates]", "---",
        f"# {hyp.id} {title}: gate verdict **{verdict}**", "",
        f"{hyp.title}. {len(cal)} dates {cal[0]}..{cal[-1]}; {len(folds)} folds (3 y / 1 y). DSR N = {n_global}. "
        f"Capital ${capital:,.0f}. {fill_desc}.", "", *(notes or []), "",
        f"OOS (walk-forward): {st}", f"OOS contract trades: {oos_trades}", "",
        "## Gates", md(table), "", f"Placebo: real OOS net {real:,.0f} vs placebo median {np.median(sims):,.0f} "
        f"(95th pct {np.percentile(sims, 95):,.0f}); p = {placebo_p:.3f}", "",
        f"Net by scenario (OOS): { {lab: round(float(v.sum())) for lab, v in od.items()} }", "",
        "### By year (OOS)", md(by_year), "", "## Variant chosen per fold", md(pd.DataFrame(chosen), index=False), "",
        f"## Family (full period): PBO = {pbo['pbo']:.3f}, K = {cl['k']}", md(fam), ""]) + "\n")
    return {"verdict": verdict, "table": table, "oos": st, "placebo_p": placebo_p, "by_year": by_year,
            "chosen": chosen, "family": fam, "real": real}


class Outright:
    """Precomputed per-market arrays for fast window P&L (used many times by placebos)."""

    def __init__(self, rd, point_value: float, tick_value: float):
        from portfolio.data import chain_returns
        self.rd, self.pv, self.tv = rd, point_value, tick_value
        self.dates = list(rd.dates)
        self.pos_i = {d: i for i, d in enumerate(self.dates)}
        self.r = chain_returns(rd).to_numpy(float)
        held = rd.held.reindex(self.dates).to_numpy()
        self.px = np.array([rd.closes[h].get(d, np.nan) for d, h in zip(self.dates, held)], dtype=float)
        self.roll = np.r_[False, held[1:] != held[:-1]]            # v.0 instrument changed on day j


def window_pnl(m: "Outright", windows: list[tuple], notional: float, slip_ticks: float,
               fee_side: float) -> tuple[pd.Series, pd.Series]:
    """Daily net $ and contract-side counts for outright positions held over windows (start, end, side):
    exposed to the returns of days d with start < d <= end, entered at start's close and exited at end's
    close. Contracts = round(notional / (price x point_value)) >= 1 at entry. A v.0 instrument change
    strictly inside a window pays a roll (2 sides). Returns are same-instrument (chain returns)."""
    n_d = len(m.dates)
    pos = np.zeros(n_d)
    sides = np.zeros(n_d)
    for start, end, side in windows:
        a, b = m.pos_i.get(start), m.pos_i.get(end)
        if a is None or b is None or b <= a or not m.px[a] > 0:
            continue
        n = max(1, int(round(notional / (m.px[a] * m.pv))))
        sides[a] += n
        sides[b] += n
        pos[a + 1:b + 1] += side * n
        inside = np.flatnonzero(m.roll[a + 1:b]) + a + 1
        sides[inside] += 2 * n
    pxprev = np.r_[np.nan, m.px[:-1]]
    gross = np.where((pos != 0) & np.isfinite(m.r) & np.isfinite(pxprev), pos * m.r * pxprev * m.pv, 0.0)
    idx = pd.Index(m.dates)
    cnt = pd.Series(sides, index=idx)
    return pd.Series(gross, index=idx) - cnt * (slip_ticks * m.tv + fee_side), cnt


SCEN_COSTS = {"base": (1.0, 1.0), "fees1.5": (1.0, 1.5), "stress": (2.0, 1.5), "plus1tick": (2.0, 1.0)}
