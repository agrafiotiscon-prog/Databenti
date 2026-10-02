"""When does ES liquidity actually cross from the expiring to the next contract? (Phase 1b)

  python scripts/roll_history.py [--start 2019-01-01] [--end 2025-10-01] [--root ES]

Downloads daily bars (ohlcv-1d, about $0.02 per symbol for 7 years) for <root>.c.0 and
<root>.c.1 through the cost guard, then for every quarterly expiry:
  - crossover day: first day from which c.1 out-trades c.0 on every remaining day to expiry
  - for each candidate calendar rule (roll N days before expiry) and for a volume rule that
    uses the PREVIOUS day's volume (like Databento's `v` rank), the number of days on which the
    rule picks the less-traded contract.
Calendar-spread leg trades print the same quantity in both outrights, so they cancel out of
"which contract trades more". Report: vault/results/roll-history-<root>.md.

The --end default stops before the future holdout (config/splits.toml, last 12 months).
"""
from __future__ import annotations

import argparse
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data.contracts import quarterly_expiries   # noqa: E402

CANDIDATE_DAYS_BEFORE = (8, 7, 4, 3, 2)   # 4, 5 and 6 all mean the Monday of expiry week
WINDOW_DAYS = 15     # calendar days before expiry to examine


def roll_table(vol0: pd.Series, vol1: pd.Series, expiries: list[date]) -> pd.DataFrame:
    """vol0/vol1: daily volume of rank 0 / rank 1, indexed by date. One row per expiry."""
    rows = []
    for exp in expiries:
        days = [d for d in vol0.index if exp - timedelta(days=WINDOW_DAYS) <= d <= exp and d in vol1.index]
        if len(days) < 5:
            continue
        v0, v1 = vol0.loc[days], vol1.loc[days]
        c1_wins = (v1 > v0).tolist()
        cross = None
        for i in range(len(days)):
            if all(c1_wins[i:]):
                cross = days[i]
                break
        row = {"expiry": exp, "crossover": cross,
               "weekday": cross.strftime("%a") if cross else None,
               "cal_days_before": (exp - cross).days if cross else None,
               "trading_days_before": sum(1 for d in days if cross and cross <= d < exp) if cross else None}
        for n in CANDIDATE_DAYS_BEFORE:
            pick1 = [d >= exp - timedelta(days=n) for d in days]
            row[f"wrong_cal{n}"] = sum(p != w for p, w in zip(pick1, c1_wins))
        prev_pick1 = [False] + c1_wins[:-1]                 # yesterday's winner, no lookahead
        row["wrong_prevday_volume"] = sum(p != w for p, w in zip(prev_pick1, c1_wins))
        rows.append(row)
    return pd.DataFrame(rows)


def summarize(table: pd.DataFrame) -> pd.DataFrame:
    cols = [c for c in table.columns if c.startswith("wrong_")]
    return pd.DataFrame({"total_wrong_days": table[cols].sum(), "rolls_with_errors": (table[cols] > 0).sum(),
                         "max_wrong_in_one_roll": table[cols].max()}).sort_values("total_wrong_days")


def _fetch_daily(dl, symbol: str, start: str, end: str) -> pd.DataFrame:
    from data.cost_guard import Request
    import databento as db

    req = Request(dl.dataset, "ohlcv-1d", symbol, "continuous",
                  datetime.fromisoformat(start).replace(tzinfo=timezone.utc).isoformat(),
                  datetime.fromisoformat(end).replace(tzinfo=timezone.utc).isoformat())
    path = dl.cache_dir / dl.dataset / "ohlcv-1d-range" / symbol / f"{start}_{end}.dbn.zst"
    if not path.exists():
        dl.guard.check([req])                               # raises if > limit
        dl._download([(req, path)])
    df = db.DBNStore.from_file(path).to_df(pretty_ts=True)
    return to_trading_dates(df["volume"])


def to_trading_dates(volume: pd.Series) -> pd.Series:
    """ohlcv-1d bars are UTC days. A weekend bar (Sunday 17:00 CT open) belongs to Monday's
    CME session, so fold Sat/Sun into the next Monday; weekday bars keep their date."""
    d = pd.Series([ts.date() for ts in volume.index])
    d = d.map(lambda x: x + timedelta(days=(7 - x.weekday()) % 7) if x.weekday() >= 5 else x)
    out = volume.groupby(d.values).sum()
    out.index = pd.Index(out.index)
    return out


def main(argv=None) -> int:
    from data.download import Downloader
    from scripts.verify_data import render, save

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--start", default="2019-01-01")
    ap.add_argument("--end", default="2025-10-01")
    ap.add_argument("--root", default="ES")
    a = ap.parse_args(argv)
    dl = Downloader()
    vol0 = _fetch_daily(dl, f"{a.root}.c.0", a.start, a.end)
    vol1 = _fetch_daily(dl, f"{a.root}.c.1", a.start, a.end)
    y0, y1 = int(a.start[:4]), int(a.end[:4])
    exps = [e for e in quarterly_expiries(y0, y1) if date.fromisoformat(a.start) <= e < date.fromisoformat(a.end)]
    table = roll_table(vol0, vol1, exps)
    summary = summarize(table)
    text = render(f"Roll history {a.root} {a.start} to {a.end} (ohlcv-1d, c.0 vs c.1)",
                  {"rule comparison (fewer wrong days is better)": summary,
                   "crossover day per expiry": table[["expiry", "crossover", "weekday", "cal_days_before",
                                                      "trading_days_before"]],
                   "crossover weekday counts": table["weekday"].value_counts().to_frame(),
                   "per expiry wrong days": table.drop(columns=["crossover", "weekday"])})
    p = save(f"roll-history-{a.root}.md", text)
    print(summary.to_string())
    print(table[["expiry", "crossover", "weekday", "cal_days_before"]].to_string())
    print(f"saved {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
