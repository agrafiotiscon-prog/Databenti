"""Monthly summary of forward paper tracking (R13.3, ROUTINE step 2b).

  python scripts/paper_summary.py [--month 2026-10] [--ledger research/paper/ledger.csv]

From the ledger alone (no new data): per sleeve and market, gross P&L of the target decided at close t held
over (t, t+1] on the same instrument, minus costs (|change in target| x (1 tick + $2.26) per contract; a v.0
instrument change pays both legs). The book = fixed sleeve weights from the 5-year average of the risk-balanced
combination (vault/results/combined-book-100k-last5y.md: trend 0.76x, H-030 6.49x of the $1M sleeve definitions),
fixed here in advance so the forward test cannot be tuned. h035_watch is reported alone (not in the book).
Writes vault/results/paper-<month>.md.
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

from data.universe import BY_ROOT                           # noqa: E402

FEE_SIDE = 2.26
BOOK_WEIGHTS = {"trend252": 0.76, "h030": 6.49}             # fixed in advance (D-063 / combined-book note)


def daily_pnl(ledger: pd.DataFrame) -> pd.DataFrame:
    """Net daily P&L rows: date, sleeve, root, gross, costs, net."""
    out = []
    for (sl, r), g in ledger.groupby(["sleeve", "root"]):
        g = g.sort_values("asof").reset_index(drop=True)
        spec = BY_ROOT[r]
        cost_c = spec.tick_value + FEE_SIDE
        for a, b in zip(g.index, g.index[1:]):
            same = g.loc[a, "instrument_id"] == g.loc[b, "instrument_id"]
            gross = g.loc[a, "target"] * (g.loc[b, "close"] - g.loc[a, "close"]) * spec.point_value if same else 0.0
            # traded at b's close: change of target; a v.0 change closes the old and opens the new position
            traded = abs(g.loc[b, "target"] - g.loc[a, "target"]) if same else abs(g.loc[a, "target"]) + abs(g.loc[b, "target"])
            out.append([g.loc[b, "asof"], sl, r, gross, traded * cost_c])
    df = pd.DataFrame(out, columns=["date", "sleeve", "root", "gross", "costs"])
    df["net"] = df["gross"] - df["costs"]
    return df


def summarize(ledger: pd.DataFrame, month: str | None) -> tuple[pd.DataFrame, pd.Series]:
    d = daily_pnl(ledger)
    d["month"] = pd.to_datetime(d["date"]).dt.strftime("%Y-%m")
    if month:
        d = d[d["month"] <= month]
    by_sleeve = d.groupby(["month", "sleeve"])[["gross", "costs", "net"]].sum().round(0)
    book = sum(w * d[d["sleeve"] == s].groupby("month")["net"].sum() for s, w in BOOK_WEIGHTS.items())
    return by_sleeve, book.round(0) if isinstance(book, pd.Series) else pd.Series(dtype=float)


def main(argv=None) -> int:
    from scripts.run_h001 import md
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--month", default=None)
    ap.add_argument("--ledger", type=Path, default=ROOT / "research" / "paper" / "ledger.csv")
    ap.add_argument("--out-dir", type=Path, default=ROOT / "vault" / "results")
    a = ap.parse_args(argv)
    if not a.ledger.exists():
        print("no ledger yet")
        return 0
    led = pd.read_csv(a.ledger)
    by_sleeve, book = summarize(led, a.month)
    month = a.month or (max(by_sleeve.index.get_level_values(0)) if len(by_sleeve) else date.today().strftime("%Y-%m"))
    cum = book.cumsum()
    lines = ["---", "type: result", f"date: {date.today().isoformat()}", "tags: [paper-tracking, forward]", "---",
             f"# Forward paper tracking through {month} (no broker, simulated fills at closes)", "",
             "Book = trend252 x 0.76 + H-030 x 6.49 (weights fixed in advance; $1M sleeve definitions). h035_watch is not in the book.",
             "Descriptive expectation (hindsight, not a forecast): ~12.7%/yr at 15% vol for the book "
             "(vault/results/combined-trend-h030-descriptive.md).", "",
             "## By month and sleeve ($)", md(by_sleeve) if len(by_sleeve) else "none yet", "",
             "## Book by month ($, cumulative)", md(pd.DataFrame({"net": book, "cumulative": cum})) if len(book) else "none yet",
             ""]
    a.out_dir.mkdir(parents=True, exist_ok=True)
    out = a.out_dir / f"paper-{month}.md"
    out.write_text("\n".join(lines) + "\n")
    print(by_sleeve.to_string() if len(by_sleeve) else "no P&L rows yet"); print("saved", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
