"""Forward paper tracking (R9.5): record what the confirmed/candidate rules would hold, day by day. No broker.

  python scripts/paper_track.py --asof 2025-09-30 [--ledger research/paper/ledger.csv] [--replay-days 0]
  python scripts/paper_track.py --live                 # forward: fetch new daily bars, log every new closed day

Sleeves (rules fixed in advance, nothing is tuned here):
  * trend252 - H-023's confirmed trend sleeve: portfolio.engine.target_contracts on the 26 markets, $1M
  * h030     - H-030 rule "pre|3|all" (confirmed on TN/UB, D-062): long ZT/ZF/ZN/ZB ($250k notional each)
               from the close 3 trading days before month-end to the month-end close
  * h035_watch - H-035 rule "5|es" (not confirmed, 6/12 gates, placebo p 0.047; D-065): ES $1M notional over the last
               5 days of the month, side = -sign(ES - ZN month-to-date at entry)
  * h044     - H-044 (confirmed 2026-10-05): long ZT/ZF/ZN/ZB ($250k each) from the close 2 trading days before a
               scheduled FOMC announcement to the close of the day after it (TN/UB of the test are not in the universe)
  * h045     - H-045 (confirmed 2026-10-05): long 6E/6J/6B/6A/6C/6S ($125k each, = short USD) from the close of the
               day before a scheduled FOMC announcement to the announcement-day close (6N/6M not in the universe)
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
H035_K, H035_NOTIONAL = 5, 1_000_000.0   # watch sleeve (D-065): pre-registered H-035 rule 5|es, not confirmed
COLS = ["asof", "sleeve", "root", "target", "close", "instrument_id"]
H044_MARKETS, H044_NOTIONAL = ("ZT", "ZF", "ZN", "ZB"), 250_000.0
H045_MARKETS, H045_NOTIONAL = ("6E", "6J", "6B", "6A", "6C", "6S"), 125_000.0


def fomc_dates() -> list[date]:
    df = pd.read_csv(ROOT / "config" / "fomc_dates.csv", comment="#")
    return [date.fromisoformat(x) for x in df["date"]]


def days_until(dates: list, asof: date, f: date) -> int:
    """Trading days in (asof, f]: from the known calendar, extended with US business days (federal holidays
    excluded) beyond its end - in forward use the next days are not in the data yet."""
    known = [d for d in dates if asof < d <= f]
    last = max([asof] + [d for d in dates if d <= f])
    if last >= f:
        return len(known)
    from pandas.tseries.holiday import USFederalHolidayCalendar
    hol = USFederalHolidayCalendar().holidays(last, f).date.tolist()
    return len(known) + int(np.busday_count(last + pd.Timedelta(days=1), f + pd.Timedelta(days=1), holidays=hol))


def fomc_long(dates: list, asof: date, before: int, after: int, fomc: list | None = None) -> int:
    """+1 if the position decided at asof's close is inside an FOMC window that is entered at the close `before`
    trading days before the announcement day F and exited at the close `after` days after it."""
    for f in fomc if fomc is not None else fomc_dates():
        if f >= asof:
            n = days_until(dates, asof, f)
            if n <= before:
                return 1 if n >= 1 or after >= 1 else 0
        elif after >= 1 and (asof - f).days <= 10 and asof in dates and f in dates and 0 < dates.index(asof) - dates.index(f) < after:
            return 1
    return 0


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


def h035_side(rds: dict, asof: date, k: int = H035_K) -> int:
    """H-035 rule 5|es: during the last k decision closes before month-end, side = -sign(ES - ZN log return from
    the previous month-end close to the entry close E = k trading days before month-end); 0 otherwise."""
    es_dates = rds["ES"].dates
    month = [d for d in es_dates if (d.year, d.month) == (asof.year, asof.month)]
    if asof not in month or not (len(month) - 1 - k <= month.index(asof) < len(month) - 1):
        return 0
    entry = month[len(month) - 1 - k]
    prev = [d for d in es_dates if d < month[0]]
    if not prev:
        return 0

    def lr(rd):
        from portfolio.data import chain_returns
        r = chain_returns(cut(rd, entry))
        return float(np.log1p(r[(r.index > prev[-1]) & (r.index <= entry)]).sum())
    rel = lr(rds["ES"]) - lr(rds["ZN"])
    return 0 if rel == 0 or np.isnan(rel) else int(-np.sign(rel))


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
    fomc = fomc_dates()
    for sleeve, roots, notional, before, after in (("h044", H044_MARKETS, H044_NOTIONAL, 2, 1),
                                                    ("h045", H045_MARKETS, H045_NOTIONAL, 1, 0)):
        for r in roots:
            if r not in rds:
                continue
            rd = cut(rds[r], asof)
            if not rd.dates or rd.dates[-1] != asof:
                continue
            held = rd.held[asof]
            px = float(rd.closes[held][asof])
            n = max(1, int(round(notional / (px * BY_ROOT[r].point_value))))
            rows.append([asof, sleeve, r, n * fomc_long(rd.dates, asof, before, after, fomc), px, int(held)])
    es = cut(rds["ES"], asof)
    if es.dates and es.dates[-1] == asof:
        held = es.held[asof]
        px = float(es.closes[held][asof])
        n = max(1, int(round(H035_NOTIONAL / (px * BY_ROOT["ES"].point_value))))
        rows.append([asof, "h035_watch", "ES", n * h035_side(rds, asof), px, int(held)])
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


LIVE_START = date(2026, 10, 5)        # first forward trading day (D-063); earlier data is signal warm-up only
MAX_FETCH_USD = 0.05                  # per run, all symbols together (user-approved forward tracking, R9.7)
_spent = [0.0]


def live_bars(dl, sym: str, today: date):
    """Development file + spent-holdout file (warm-up only, D-063) + forward files fetched since LIVE_START.
    Fetches [last fetched end, today) once per day when missing (cost-guarded)."""
    from datetime import datetime, timezone
    from data.cost_guard import Request
    folder = dl.cache_dir / dl.dataset / "ohlcv-1d-range" / sym
    parts = [load_bars(path_for(dl, sym))]
    hold = folder / "2025-10-01_2026-10-04.dbn.zst"
    if hold.exists():
        parts.append(load_bars(hold))
    fwd = sorted(folder.glob("fwd_*.dbn.zst"))
    start = max([date.fromisoformat(f.stem.split(".")[0].split("_")[2]) for f in fwd], default=LIVE_START)
    if today > start:
        iso = lambda d: datetime.combine(d, datetime.min.time(), tzinfo=timezone.utc).isoformat()   # noqa: E731
        req = Request(dl.dataset, "ohlcv-1d", sym, "continuous", iso(start), iso(today))
        path = folder / f"fwd_{start}_{today}.dbn.zst"
        try:
            cost = dl.guard.check([req])
            if _spent[0] + cost > MAX_FETCH_USD:
                raise RuntimeError(f"run fetch cap ${MAX_FETCH_USD} reached")
            dl.check_total_cap(cost)
            _spent[0] += cost
            dl._download([(req, path)])
        except Exception as e:                      # no new data yet (weekend/holiday) or fetch failure: keep going
            print(f"  [live] {sym}: no fetch ({type(e).__name__}: {str(e)[:80]})")
        fwd = sorted(folder.glob("fwd_*.dbn.zst"))
    for f in fwd:
        try:
            parts.append(load_bars(f))
        except Exception:
            pass
    df = pd.concat(parts)
    return df[~df.index.duplicated(keep="last")].sort_index()


def main(argv=None) -> int:
    from data.download import Downloader
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--asof", type=date.fromisoformat, default=None)
    ap.add_argument("--live", action="store_true", help="fetch new bars and log every closed day >= LIVE_START")
    ap.add_argument("--replay-days", type=int, default=0, help="also write the N trading days before --asof")
    ap.add_argument("--ledger", type=Path, default=ROOT / "research" / "paper" / "ledger.csv")
    a = ap.parse_args(argv)
    dl = Downloader()
    if a.live:
        today = date.today()
        rds = {s.root: build(s.root, live_bars(dl, f"{s.root}.v.0", today), live_bars(dl, f"{s.root}.v.1", today))
               for s in UNIVERSE}
        cal = sorted(set().union(*[rd.dates for rd in rds.values()]))
        done = set(pd.to_datetime(pd.read_csv(a.ledger)["asof"]).dt.date) if a.ledger.exists() else set()
        days = [d for d in cal if d >= LIVE_START and d < today and d not in done]
        if not days:
            print("live: no new closed trading day since the last ledger entry")
            return 0
    else:
        if a.asof is None:
            raise SystemExit("--asof or --live is required")
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
