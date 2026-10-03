"""H-023 combined book: 26-market trend252 portfolio + pre-FOMC ES sleeve (registry H-023, D-050).

  python scripts/run_h023.py --development     # descriptive only (components chosen in hindsight)
  python scripts/run_h023.py --holdout         # ONE evaluation; refuses unless research/HOLDOUT_UNLOCK exists

The holdout mode downloads 2025-10-01..today (26 markets ohlcv-1d v.0/v.1, ES ohlcv-1h c.0/c.1; < $0.5),
uses pre-holdout history only as signal warm-up, and counts P&L only from the frozen holdout start.
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

from backtest.costs import load_costs                      # noqa: E402
from backtest.metrics import drawdown                       # noqa: E402
from data import holdout                                    # noqa: E402
from data.cost_guard import Request                         # noqa: E402
from data.universe import END, START, UNIVERSE              # noqa: E402
from portfolio.data import build, load_bars                 # noqa: E402
from portfolio.engine import prepare, simulate              # noqa: E402
from research import registry, trials                       # noqa: E402
from scripts.fetch_futures_daily import path_for            # noqa: E402
from scripts.run_bars_hypothesis import hourly_table        # noqa: E402
from scripts.run_h001 import md                             # noqa: E402
from strategies.bars_common import prev_date, px, sym_of    # noqa: E402
from strategies.h007 import fomc_dates                      # noqa: E402

HYP, CAPITAL, SMALL, TICK, PV = "H-023", 1_000_000.0, 100_000.0, 0.25, 50.0
H_START = "2025-10-01"


def _req(dl, schema, symbol, start, end):
    iso = lambda s: datetime.fromisoformat(s).replace(tzinfo=timezone.utc).isoformat()   # noqa: E731
    return Request(dl.dataset, schema, symbol, "continuous", iso(start), iso(end))


def fetch(dl, schema, symbol, start, end) -> Path:
    folder = "ohlcv-1d-range" if schema == "ohlcv-1d" else "ohlcv-1h-range"
    path = dl.cache_dir / dl.dataset / folder / symbol / f"{start}_{end}.dbn.zst"
    if not path.exists():
        r = _req(dl, schema, symbol, start, end)
        cost = dl.guard.check([r])
        dl.check_total_cap(cost)
        dl._download([(r, path)])
    return path


def load_root(dl, root, extra_end=None):
    """v.0/v.1 bars for a root: development file, plus the holdout file when extra_end is given."""
    parts = {}
    for k in (0, 1):
        sym = f"{root}.v.{k}"
        df = load_bars(path_for(dl, sym))
        if extra_end:
            h = load_bars(fetch(dl, "ohlcv-1d", sym, H_START, extra_end))
            df = pd.concat([df, h[~h.index.isin(df.index)]]).sort_index()
        parts[k] = df
    return build(root, parts[0], parts[1])


def es_hourly(dl, extra_end=None):
    from scripts.run_h003 import fetch_hourly
    P = {}
    for s in ("ES.c.0", "ES.c.1"):
        bars = fetch_hourly(dl, s)
        if extra_end:
            import databento as db
            h = db.DBNStore.from_file(fetch(dl, "ohlcv-1h", s, H_START, extra_end)).to_df(pretty_ts=True)
            bars = pd.concat([bars, h[~h.index.isin(bars.index)]]).sort_index()
        P[s] = hourly_table(bars)
    return P


def fomc_sleeve(P, capital, fee_rt) -> pd.Series:
    """Daily net P&L of the H-007 lm24h trade sized at 1x notional (contracts = round(capital / (price*50)))."""
    out = {}
    have = set(P["ES.c.0"].index) | set(P["ES.c.1"].index)
    for d in fomc_dates():
        if d not in have:
            continue
        sym = sym_of(prev_date(P, sym_of(d), d) or d)
        de = prev_date(P, sym, d)
        if de is None:
            continue
        e, x = px(P, sym, de, "p1300"), px(P, sym, d, "p1300")
        if e is None or x is None:
            continue
        n = max(1, int(round(capital / (e * PV))))
        out[d] = n * (((x - TICK) - (e + TICK)) * PV - fee_rt)
    return pd.Series(out, dtype=float)


def stats(daily: pd.Series, capital: float) -> dict:
    if daily.std() == 0 or len(daily) < 2:
        return {"net": round(float(daily.sum()))}
    ann, vol = daily.mean() * 252 / capital, daily.std() * np.sqrt(252) / capital
    return {"net": round(float(daily.sum())), "ann_return_pct": round(100 * ann, 2), "ann_vol_pct": round(100 * vol, 2),
            "sharpe": round(float(ann / vol), 3), "max_dd_pct": round(100 * drawdown(daily)["max_drawdown"] / capital, 2),
            "days": len(daily)}


def book(dl, capital, extra_end=None):
    c = load_costs()
    preps = [prepare(load_root(dl, s.root, extra_end)) for s in UNIVERSE]
    trend = simulate(preps, "trend252", capital, 1.0, c.fee(1))["net"]
    fomc = fomc_sleeve(es_hourly(dl, extra_end), capital, 2 * c.fee(1))
    cal = sorted(set(trend.index) | set(fomc.index))
    trend, fomc = trend.reindex(cal).fillna(0.0), fomc.reindex(cal).fillna(0.0)
    return trend, fomc, trend + fomc


def main(argv=None) -> int:
    from data.download import Downloader
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--development", action="store_true")
    g.add_argument("--holdout", action="store_true")
    a = ap.parse_args(argv)
    dl = Downloader()
    hs = date.fromisoformat(holdout.load()["holdout_start"])
    if a.development:
        rows = {}
        for cap in (CAPITAL, SMALL):
            t, f, b = book(dl, cap)
            win = [d for d in b.index if date(2013, 6, 1) <= d < hs]
            rows[cap] = {"trend": stats(t.loc[win], cap), "fomc": stats(f.loc[win], cap), "book": stats(b.loc[win], cap),
                         "corr": round(float(np.corrcoef(t.loc[win], f.loc[win])[0, 1]), 3)}
            yrs = (b.loc[win].groupby([d.year for d in win]).sum() / cap * 100).round(1)
            rows[cap]["by_year_pct"] = yrs.to_dict()
        print(json.dumps(rows, indent=1, default=str))
        out = ROOT / "vault" / "results" / "h023-development-descriptive.md"
        out.write_text("\n".join([
            "---", "type: result", f"date: {date.today().isoformat()}", "tags: [H-023, descriptive, not-evidence]", "---",
            "# H-023 combined book on development data (2013-06..2025-09): DESCRIPTIVE ONLY",
            "", "Both components were selected after seeing these years, so these numbers are what the book would have",
            "done with hindsight - an upper bound, not evidence. The test is the holdout (D-050).", "",
            "```", json.dumps(rows, indent=1, default=str), "```", ""]) + "\n")
        print("saved", out)
        return 0

    # ---- holdout: single evaluation ----
    hyp = registry.load(HYP)
    if hyp.status != "open" or trials.count(hypothesis=HYP) >= hyp.trial_budget:
        raise SystemExit("H-023 holdout already evaluated (single evaluation).")
    if not holdout.unlocked():
        raise SystemExit("Holdout is locked: only the user may create research/HOLDOUT_UNLOCK.")
    end = date.today().isoformat()
    res = {}
    for cap in (CAPITAL, SMALL):
        t, f, b = book(dl, cap, extra_end=end)
        win = [d for d in b.index if d >= hs]
        res[cap] = {"trend": stats(t.loc[win], cap), "fomc": stats(f.loc[win], cap), "book": stats(b.loc[win], cap),
                    "fomc_trades": int((f.loc[win] != 0).sum()), "first": str(win[0]), "last": str(win[-1])}
    r = res[CAPITAL]
    net, sh, tnet = r["book"]["net"], r["book"].get("sharpe", 0) or 0, r["trend"]["net"]
    verdict = "CONFIRM (paper trading next)" if net > 0 and sh >= 0.4 and tnet > 0 else ("REJECT" if net <= 0 else "INCONCLUSIVE")
    trials.append({"family": HYP, "hypothesis": HYP, "params": {"variant": "fixed"},
                   "data": f"HOLDOUT {r['first']}..{r['last']} 26 futures daily + ES hourly",
                   "fill_mode": "as H-022 trend252 + H-007 lm24h, 1 tick + fees", "results": {"verdict": verdict, **r["book"]}})
    out = ROOT / "vault" / "results" / "h023-holdout.md"
    out.write_text("\n".join([
        "---", "type: result", f"date: {date.today().isoformat()}", "tags: [H-023, holdout, confirmation]", "---",
        f"# H-023 holdout evaluation (single, D-050): **{verdict}**", "",
        "Pre-registered criteria: CONFIRM if holdout net > 0 AND Sharpe >= 0.4 AND trend sleeve net > 0; REJECT if net <= 0.",
        "", "```", json.dumps(res, indent=1, default=str), "```", ""]) + "\n")
    print(json.dumps(res, indent=1, default=str)); print("verdict:", verdict, "| saved", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
