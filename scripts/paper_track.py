"""Forward paper tracking (R9.5): record what the confirmed/candidate rules would hold, day by day. No broker.

  python scripts/paper_track.py --asof 2025-09-30 [--ledger research/paper/ledger.csv] [--replay-days 0]

Sleeves (rules fixed in advance, nothing is tuned here):
  * trend252 - H-023's confirmed trend sleeve: portfolio.engine.target_contracts on the 26 markets, $1M
  * h030     - H-030 candidate, pre-registered rule "pre|3|all": long ZT/ZF/ZN/ZB ($250k notional each)
               from the close 3 trading days before month-end to the month-end close
For each as-of date the ledger gets one row per sleeve and market: the target contracts decided at that
close (to be traded at the next close) and the close itself, so P&L can be marked later from the ledger alone.
Running it forward needs fresh daily bars (a few cents/day of data) - only with the user's OK (R8.9/R9.6).
Today it runs on cached data (--asof <= 2025-09-30) to test the pipeline.
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

from data.universe import BY_ROOT, UNIVERSE                 # noqa: E402
from portfolio.data import build, load_bars                 # noqa: E402
from portfolio.engine import prepare, target_contracts     # noqa: E402
from scripts.fetch_futures_daily import path_for            # noqa: E402

CAPITAL = 1_000_000.0
H030_MARKETS, H030_K, H030_NOTIONAL = ("ZT", "ZF", "ZN", "ZB"), 3, 250_000.0
COLS = ["asof", "sleeve", "root", "target", "close", "instrument_id"]


def h030_target(dates: list, asof: date, k: int = H030_K) -> int:
    """+1 if the position decided at `asof`'s close must be long: i.e. asof is one of the k trading days
    before month-end (enter at the close k days before month-end, hold through the month-end close).
    Month-end = last trading date of asof's month in `dates` (needs the month's calendar: in forward use the
    CME holiday calendar, which is known in advance)."""
    month = [d for d in dates if (d.year, d.month) == (asof.year, asof.month)]
    if asof not in month:
        return 0
    i = month.index(asof)
    return 1 if len(month) - 1 - k <= i < len(month) - 1 else 0


def snapshot(rds: dict, asof: date) -> pd.DataFrame:
    rows = []
    trimmed = {r: rd for r, rd in rds.items()}
    preps = [prepare(cut(rd, asof)) for rd in trimmed.values()]
    preps = [p for p in preps if p.dates]
    tg = target_contracts(preps, "trend252", CAPITAL)
    for p in preps:
        if p.dates[-1] != asof:
            continue                                            # market closed that day
        held = p.held[asof]
        rows.append([asof, "trend252", p.root, int(tg[p.root].iloc[-1]), float(p.closes[held][asof]), int(held)])
    for r in H030_MARKETS:
        rd = cut(rds[r], asof)
        if not rd.dates or rd.dates[-1] != asof:
            continue
        held = rd.held[asof]
        px = float(rd.closes[held][asof])
        n = max(1, int(round(H030_NOTIONAL / (px * BY_ROOT[r].point_value))))
        # the full calendar of the month is needed to know month-end; use the uncut dates (exchange calendar)
        rows.append([asof, "h030", r, n * h030_target(rds[r].dates, asof), px, int(held)])
    return pd.DataFrame(rows, columns=COLS)


def cut(rd, asof: date):
    """RootData restricted to dates <= asof (so nothing after asof can leak into the decision)."""
    from portfolio.data import RootData
    dates = [d for d in rd.dates if d <= asof]
    closes = {i: s[s.index <= asof] for i, s in rd.closes.items()}
    return RootData(rd.root, dates, rd.held[rd.held.index <= asof], rd.nxt[rd.nxt.index <= asof], closes,
                    rd.expiry_rank)


def append(ledger: Path, df: pd.DataFrame) -> None:
    ledger.parent.mkdir(parents=True, exist_ok=True)
    old = pd.read_csv(ledger, parse_dates=["asof"]) if ledger.exists() else pd.DataFrame(columns=COLS)
    if len(old):
        old["asof"] = pd.to_datetime(old["asof"]).dt.date
        old = old[~old["asof"].isin(set(df["asof"]))]           # re-running a day replaces it
    pd.concat([old, df]).sort_values(["asof", "sleeve", "root"]).to_csv(ledger, index=False)


def mark(ledger: Path) -> pd.DataFrame:
    """Gross daily P&L per sleeve from the ledger: target decided at t, held over (t, t+1], same instrument."""
    df = pd.read_csv(ledger)
    out = []
    for (sl, r), g in df.groupby(["sleeve", "root"]):
        g = g.sort_values("asof").reset_index(drop=True)
        pv = BY_ROOT[r].point_value
        for a, b in zip(g.index, g.index[1:]):
            if g.loc[a, "instrument_id"] == g.loc[b, "instrument_id"]:
                out.append([g.loc[b, "asof"], sl, r, g.loc[a, "target"] * (g.loc[b, "close"] - g.loc[a, "close"]) * pv])
    return pd.DataFrame(out, columns=["date", "sleeve", "root", "gross"])


def main(argv=None) -> int:
    from data.download import Downloader
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--asof", type=date.fromisoformat, required=True)
    ap.add_argument("--replay-days", type=int, default=0, help="also write the N trading days before --asof")
    ap.add_argument("--ledger", type=Path, default=ROOT / "research" / "paper" / "ledger.csv")
    a = ap.parse_args(argv)
    dl = Downloader()
    rds = {s.root: build(s.root, load_bars(path_for(dl, f"{s.root}.v.0")), load_bars(path_for(dl, f"{s.root}.v.1")))
           for s in UNIVERSE}
    cal = sorted(set().union(*[rd.dates for rd in rds.values()]))
    days = [d for d in cal if d <= a.asof][-(a.replay_days + 1):]
    for d in days:
        append(a.ledger, snapshot(rds, d))
    m = mark(a.ledger)
    print(pd.read_csv(a.ledger).tail(12).to_string())
    if len(m):
        print(m.groupby("sleeve")["gross"].agg(["count", "sum"]).round(0).to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
