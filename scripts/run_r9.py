"""R9 hypotheses on cached daily futures data: H-029 (index roll), H-030 (Treasury month-end), H-031 (auction cycle).

  python scripts/run_r9.py H-029|H-030|H-031 [--coverage-only]

Each hypothesis is evaluated ONCE through research/daily_eval.py; coverage (D-042) is printed and written
into the report before any P&L. The three can run in parallel (trials.append is locked).
"""
from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backtest.costs import load_costs                      # noqa: E402
from data.holdout import check as holdout_check             # noqa: E402
from data.universe import BY_ROOT                           # noqa: E402
from portfolio.data import build, load_bars                 # noqa: E402
from research import daily_eval, registry, trials           # noqa: E402
from research.daily_eval import SCEN_COSTS, Outright, window_pnl  # noqa: E402
from scripts.fetch_futures_daily import path_for            # noqa: E402
from scripts.run_h001 import md                             # noqa: E402

CAPITAL = 1_000_000.0
GSCI_ROLL_MONTHS = {**{r: set(range(1, 13)) for r in ("CL", "HO", "RB", "NG")},
                    "GC": {1, 3, 5, 7, 11}, **{r: {2, 4, 6, 8, 11} for r in ("SI", "HG", "ZC", "ZW")},
                    "ZS": {2, 4, 6, 10, 12}, "LE": {1, 3, 5, 7, 9, 11}, "HE": {1, 3, 5, 6, 7, 9, 11}}


def load(dl, root):
    return build(root, load_bars(path_for(dl, f"{root}.v.0")), load_bars(path_for(dl, f"{root}.v.1")))


def by_month(dates) -> dict:
    out = defaultdict(list)
    for d in dates:
        out[(d.year, d.month)].append(d)
    return out


def variants_of(hyp) -> list[str]:
    return ["|".join(str(g[k]) for k in hyp.space) for g in hyp.grid()]


def assemble(hyp, cal, fn) -> tuple[dict, pd.DataFrame]:
    """fn(params, scen) -> (daily net Series, entries Series) on any index; returns D and trades on cal."""
    D, T = {}, {}
    for scen in SCEN_COSTS:
        cols = {}
        for v, g in zip(variants_of(hyp), hyp.grid()):
            net, ent = fn(g, scen)
            cols[v] = net.reindex(cal).fillna(0.0)
            if scen == "base":
                T[v] = ent.reindex(cal).fillna(0.0)
        D[scen] = pd.DataFrame(cols)
    return D, pd.DataFrame(T)


def entries(windows, idx) -> pd.Series:
    s = pd.Series(0.0, index=pd.Index(idx))
    for w in windows:
        if w[0] in s.index:
            s[w[0]] += 1
    return s


# ---------------------------------------------------------------- H-029 index roll (calendar spread)
def spread_pnl(rd, spec, events, notional, slip, fee):
    """events: (start, end). Short near / long far fixed at start; returns (daily net, entries)."""
    idx = pd.Index(rd.dates)
    net = pd.Series(0.0, index=idx)
    ent = pd.Series(0.0, index=idx)
    pos_i = {d: i for i, d in enumerate(rd.dates)}
    cost = slip * spec.tick_value + fee
    for start, end in events:
        a, b = pos_i.get(start), pos_i.get(end)
        if a is None or b is None or b <= a:
            continue
        i0, i1 = rd.held.get(start), rd.nxt.get(start)
        if i1 is None or (isinstance(i1, float) and np.isnan(i1)) or i0 == i1:
            continue
        n_id, f_id = sorted((i0, i1), key=lambda i: rd.expiry_rank[i])
        win = rd.dates[a:b + 1]
        near = rd.closes[n_id].reindex(win).ffill()
        far = rd.closes[f_id].reindex(win).ffill()
        if not (near.iloc[0] > 0 and far.iloc[0] > 0):
            continue
        n = max(1, int(round(notional / (near.iloc[0] * spec.point_value))))
        pnl = n * spec.point_value * (far.diff() - near.diff()).fillna(0.0)
        net.loc[win] += pnl.to_numpy()
        net[start] -= 2 * n * cost
        net[end] -= 2 * n * cost
        ent[start] += 1
    return net, ent


def h029(dl, hyp, coverage_only):
    roots = list(GSCI_ROLL_MONTHS)
    rds = {r: load(dl, r) for r in roots}
    fee = load_costs().fee(1)
    notional = CAPITAL / len(roots)
    months = {r: by_month(rd.dates) for r, rd in rds.items()}

    def events(r, k, exit_bd, anchor_idx=None, rng=None):
        rd, ev, pos_i = rds[r], [], {d: i for i, d in enumerate(rds[r].dates)}
        for (y, m), ds in sorted(months[r].items()):
            if m not in GSCI_ROLL_MONTHS[r] or len(ds) < 18:
                continue
            ai = 4 if rng is None else int(rng.integers(10, 17))           # R = 5th trading day / placebo 11th-17th
            A = pos_i[ds[ai]]
            s, e = A - k, A + (exit_bd - 5)
            if s < 0 or e >= len(rd.dates):
                continue
            ev.append((rd.dates[s], rd.dates[e]))
        return ev

    cov = []
    for r in roots:
        exp = sum(1 for (y, m) in months[r] if m in GSCI_ROLL_MONTHS[r])
        used = len(events(r, 5, 9))
        cov.append({"market": r, "roll_months_in_data": exp, "events_used": used})
    cov = pd.DataFrame(cov)
    print(cov.to_string(), flush=True)
    if coverage_only:
        return
    cal = sorted(set().union(*[rd.dates for rd in rds.values()]))
    holdout_check(cal)

    def fn(g, scen, rng=None):
        slip, fm = SCEN_COSTS[scen]
        nets, ents = [], []
        for r in roots:
            a, b = spread_pnl(rds[r], BY_ROOT[r], events(r, g["entry_k"], g["exit_bd"], rng=rng), notional, slip, fee * fm)
            nets.append(a)
            ents.append(b)
        return pd.concat(nets, axis=1).sum(axis=1), pd.concat(ents, axis=1).sum(axis=1)

    D, T = assemble(hyp, cal, fn)

    def placebo(final, oos_dates, n):
        g = dict(zip(hyp.space, final.split("|")))
        g = {k: int(v) for k, v in g.items()}
        rng = np.random.default_rng(29)
        return [fn(g, "base", rng)[0].reindex(oos_dates).fillna(0.0).sum() for _ in range(n)]

    return D, T, placebo, cov, "26-market cached ohlcv-1d v.0/v.1, 12 GSCI commodities", \
        "calendar spread short near / long far, instruments fixed at entry, 4 contract sides x (1 tick + fees)"


# ---------------------------------------------------------------- H-030 Treasury month-end
def h030(dl, hyp, coverage_only):
    roots = ["ZT", "ZF", "ZN", "ZB"]
    rds = {r: load(dl, r) for r in roots}
    om = {r: Outright(rds[r], BY_ROOT[r].point_value, BY_ROOT[r].tick_value) for r in roots}
    fee = load_costs().fee(1)
    zn_months = by_month(rds["ZN"].dates)
    month_ends = sorted(ds[-1] for ds in zn_months.values())         # data ends 2025-09-30 = a real month end

    def windows(r, window, k, anchors):
        m, out = om[r], []
        for me in anchors:
            ds = [d for d in m.dates if d <= me]
            if not ds:
                continue
            i = m.pos_i[ds[-1]]
            if window == "pre" and i - k >= 0:
                out.append((m.dates[i - k], m.dates[i], 1))
            elif window == "post" and i + k < len(m.dates):
                out.append((m.dates[i], m.dates[i + k], 1))
        return out

    cov = pd.DataFrame([{"market": r, "first": om[r].dates[0], "last": om[r].dates[-1],
                         "month_ends": len(month_ends), "pre5_windows": len(windows(r, "pre", 5, month_ends)),
                         "post5_windows": len(windows(r, "post", 5, month_ends))} for r in roots])
    print(cov.to_string(), flush=True)
    if coverage_only:
        return
    cal = sorted(set().union(*[rd.dates for rd in rds.values()]))
    holdout_check(cal)
    sets = {"long_end": ["ZN", "ZB"], "all": roots}

    def fn(g, scen, anchors=None):
        slip, fm = SCEN_COSTS[scen]
        mk = sets[g["markets"]]
        nets, ents = [], []
        for r in mk:
            w = windows(r, g["window"], g["k"], anchors or month_ends)
            a, _ = window_pnl(om[r], w, CAPITAL / len(mk), slip, fee * fm)
            nets.append(a)
            ents.append(entries(w, om[r].dates))
        return pd.concat(nets, axis=1).sum(axis=1), pd.concat(ents, axis=1).sum(axis=1)

    D, T = assemble(hyp, cal, fn)

    def placebo(final, oos_dates, n):
        w, k, mk = final.split("|")
        g = {"window": w, "k": int(k), "markets": mk}
        rng = np.random.default_rng(30)
        out = []
        for _ in range(n):
            anchors = [ds[int(rng.integers(5, len(ds) - 6))] for ds in zn_months.values() if len(ds) >= 14]
            out.append(fn(g, "base", anchors)[0].reindex(oos_dates).fillna(0.0).sum())
        return out

    return D, T, placebo, cov, "ZT/ZF/ZN/ZB ohlcv-1d v.0", "long outright, enter/exit at closes, 1 tick + fees per side"


# ---------------------------------------------------------------- H-031 auction cycle
def h031(dl, hyp, coverage_only):
    roots = ["ZT", "ZF", "ZN", "ZB"]
    rds = {r: load(dl, r) for r in roots}
    om = {r: Outright(rds[r], BY_ROOT[r].point_value, BY_ROOT[r].tick_value) for r in roots}
    fee = load_costs().fee(1)
    auc = pd.read_csv(ROOT / "config" / "treasury_auctions.csv", comment="#")
    auc["d"] = pd.to_datetime(auc["auction_date"]).dt.date
    ev = {r: sorted(set(auc.loc[auc["future"] == r, "d"])) for r in roots}

    def windows(r, window, k, dates):
        m, out = om[r], []
        for t in dates:
            i = m.pos_i.get(t)
            if i is None:
                continue
            if window == "pre" and i - k - 1 >= 0:
                out.append((m.dates[i - k - 1], m.dates[i - 1], -1))
            elif window == "post" and i + k < len(m.dates):
                out.append((m.dates[i], m.dates[i + k], 1))
        return out

    cov = pd.DataFrame([{"market": r, "auctions_in_range": sum(om[r].dates[0] <= d <= om[r].dates[-1] for d in ev[r]),
                         "on_trading_dates": sum(d in om[r].pos_i for d in ev[r]),
                         "skipped": ", ".join(str(d) for d in ev[r] if om[r].dates[0] <= d <= om[r].dates[-1]
                                              and d not in om[r].pos_i) or "-"} for r in roots])
    print(cov.to_string(), flush=True)
    if coverage_only:
        return
    cal = sorted(set().union(*[rd.dates for rd in rds.values()]))
    holdout_check(cal)

    def fn(g, scen, evd=None):
        slip, fm = SCEN_COSTS[scen]
        nets, ents = [], []
        for r in roots:
            w = windows(r, g["window"], g["k"], (evd or ev)[r])
            a, _ = window_pnl(om[r], w, 250_000.0, slip, fee * fm)
            nets.append(a)
            ents.append(entries(w, om[r].dates))
        return pd.concat(nets, axis=1).sum(axis=1), pd.concat(ents, axis=1).sum(axis=1)

    D, T = assemble(hyp, cal, fn)

    def placebo(final, oos_dates, n):
        w, k = final.split("|")
        g = {"window": w, "k": int(k)}
        rng = np.random.default_rng(31)
        pools = {}
        for r in roots:
            m = om[r]
            near = set()
            for t in ev[r]:
                i = m.pos_i.get(t)
                if i is not None:
                    near.update(range(i - g["k"] - 1, i + g["k"] + 2))
            pools[r] = [d for j, d in enumerate(m.dates) if j not in near and g["k"] + 1 <= j < len(m.dates) - g["k"] - 1]
        out = []
        for _ in range(n):
            evd = {r: list(rng.choice(np.array(pools[r], dtype=object), size=sum(d in om[r].pos_i for d in ev[r]),
                                      replace=False)) for r in roots}
            out.append(fn(g, "base", evd)[0].reindex(oos_dates).fillna(0.0).sum())
        return out

    return D, T, placebo, cov, "ZT/ZF/ZN/ZB ohlcv-1d v.0 + config/treasury_auctions.csv", \
        "outright short pre / long post auction, closes, 1 tick + fees per side, $250k per position"


BUILDERS = {"H-029": (h029, "commodity index roll front-running"), "H-030": (h030, "Treasury month-end"),
            "H-031": (h031, "Treasury auction cycle")}


def main(argv=None) -> int:
    from data.download import Downloader
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("hypothesis", choices=sorted(BUILDERS))
    ap.add_argument("--coverage-only", action="store_true")
    a = ap.parse_args(argv)
    hyp = registry.load(a.hypothesis)
    if not a.coverage_only and (hyp.status != "open" or trials.count(hypothesis=hyp.id) + hyp.space_size > hyp.trial_budget):
        raise SystemExit(f"{hyp.id}: closed or already evaluated (single evaluation).")
    fn, title = BUILDERS[a.hypothesis]
    res = fn(Downloader(), hyp, a.coverage_only)
    if a.coverage_only:
        return 0
    D, T, placebo, cov, data_desc, fill_desc = res
    out = ROOT / "vault" / "results" / f"{hyp.id.lower().replace('-', '')}-report.md"
    r = daily_eval.evaluate(hyp, D, T, CAPITAL, placebo, data_desc, fill_desc, out, title,
                            notes=["## Coverage (before P&L, D-042)", md(cov, index=False)])
    print(r["table"].to_string())
    print("verdict:", r["verdict"], "| OOS:", r["oos"], "| placebo p", r["placebo_p"])
    print(r["by_year"].to_string()); print(r["family"].to_string()); print("saved", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
