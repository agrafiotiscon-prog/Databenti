"""Placebo tests for the Fed-calendar co-leaders H-007 and H-012 (diagnostic, no parameter selection).

  python scripts/placebo_fed.py

H-007: the 24 h pre-statement trade (13:00 CT day before -> 13:00 CT) on scheduled FOMC days vs the
same trade on random non-FOMC days (equal count, 20,000 draws), over the OOS period 2013-06..2025-09.
H-012: the even-week rule with the FOMC calendar shifted by k = 1..30 trading days (k = 0 is the real
calendar). If the real calendar is not exceptional, the 'edge' is mostly the equity drift.
Costs as in D-023 (1 tick adverse per side + fees). Report -> vault/results/placebo-fed.md
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backtest.costs import load_costs                     # noqa: E402
from data.download import Downloader                      # noqa: E402
from scripts.run_bars_hypothesis import hourly_table      # noqa: E402
from scripts.run_h003 import fetch_hourly                 # noqa: E402
from strategies import h007, h012                         # noqa: E402
from strategies.bars_common import prev_date, px, sym_of, trade   # noqa: E402

OOS_FROM, OOS_TO = date(2013, 6, 1), date(2025, 9, 30)


def lm24h(P, d, fee, pv):
    sym = sym_of(prev_date(P, sym_of(d), d) or d)
    de = prev_date(P, sym, d)
    if de is None:
        return None
    e, x = px(P, sym, de, "p1300"), px(P, sym, d, "p1300")
    return None if e is None or x is None else trade(d, 1, e, x, 1.0, fee, pv)["net_pnl"]


def main() -> int:
    dl = Downloader()
    P = {s: hourly_table(fetch_hourly(dl, s)) for s in ("ES.c.0", "ES.c.1")}
    dates = sorted(set(P["ES.c.0"].index) | set(P["ES.c.1"].index))
    c = load_costs()
    fee, pv = c.fee(1) * 2, c.point_value
    oos = [d for d in dates if OOS_FROM <= d <= OOS_TO]
    fomc = set(h007.fomc_dates())
    real = [v for d in oos if d in fomc and (v := lm24h(P, d, fee, pv)) is not None]
    pool = np.array([v for d in oos if d not in fomc and (v := lm24h(P, d, fee, pv)) is not None])
    rng = np.random.default_rng(7)
    draws = np.array([rng.choice(pool, size=len(real), replace=False).mean() for _ in range(20000)])
    p7 = float((draws >= np.mean(real)).mean())

    pos = {d: i for i, d in enumerate(dates)}
    real_fomc = [d for d in h007.fomc_dates() if d in pos]
    res = {}
    for k in range(0, 31):
        shifted = [dates[pos[d] + k] for d in real_fomc if pos[d] + k < len(dates)]
        h012.fomc_dates = (lambda s=shifted: s)
        t = h012.trades(P, dates, {"weeks": "even"}, 1.0, fee, pv)
        t = t[(t["trading_date"] >= OOS_FROM) & (t["trading_date"] <= OOS_TO)]
        res[k] = float(t["net_pnl"].sum())
    shifts = pd.Series(res)
    rank = int((shifts.drop(0) >= shifts[0]).sum())
    bh = (px(P, "ES.c.0", oos[-1], "p1500") or np.nan)
    lines = ["---", "type: result", f"date: {date.today().isoformat()}", "tags: [placebo, H-007, H-012]", "---",
             "# Placebo tests for the Fed-calendar co-leaders (diagnostic; no selection)", "",
             f"## H-007 (24 h pre-FOMC), OOS {OOS_FROM}..{OOS_TO}",
             f"- real FOMC days: {len(real)} trades, mean net ${np.mean(real):.1f}/trade",
             f"- random non-FOMC days ({len(pool)} available, 20,000 draws of {len(real)}): mean of means "
             f"${draws.mean():.1f}, 95th pct ${np.percentile(draws, 95):.1f}",
             f"- **one-sided p = {p7:.4f}** (share of random draws with a mean at least as high)", "",
             "## H-012 (FOMC-cycle even weeks) with the calendar shifted by k trading days",
             f"- real calendar (k = 0): net ${shifts[0]:,.0f} over the OOS period",
             f"- shifted calendars k = 1..30: median ${shifts.drop(0).median():,.0f}, max ${shifts.drop(0).max():,.0f}",
             f"- **{rank} of 30 shifted calendars do at least as well as the real one** (permutation p ≈ {(rank + 1) / 31:.3f})", "",
             "```", shifts.round(0).to_string(), "```"]
    out = ROOT / "vault" / "results" / "placebo-fed.md"
    out.write_text("\n".join(lines) + "\n")
    print("\n".join(lines[6:16]))
    print("saved", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
