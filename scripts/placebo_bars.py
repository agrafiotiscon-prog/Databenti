"""G12 placebo diagnostics for the long-only bar rules H-005 and H-009 (no parameter selection).

H-005: turn-of-month holds (entry_k=2, exit_day=3: ~4-day hold) vs equally long holds started on random
       non-turn-of-month days (20,000 draws), OOS 2013-06..2025-09.
H-009: overnight (15:00 CT -> 08:00 CT next day) vs the null that the overnight period earns only its
       time share (17/24) of the close-to-close drift: paired daily differences, one-sided t and bootstrap p.
Report -> vault/results/placebo-bars.md
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
from strategies import h005                               # noqa: E402
from strategies.bars_common import next_date, px, sym_of, trade   # noqa: E402

OOS_FROM, OOS_TO = date(2013, 6, 1), date(2025, 9, 30)


def main() -> int:
    dl = Downloader()
    P = {s: hourly_table(fetch_hourly(dl, s)) for s in ("ES.c.0", "ES.c.1")}
    dates = sorted(set(P["ES.c.0"].index) | set(P["ES.c.1"].index))
    c = load_costs()
    fee, pv = c.fee(1) * 2, c.point_value
    rng = np.random.default_rng(11)
    lines = ["---", "type: result", f"date: {date.today().isoformat()}", "tags: [placebo, G12, H-005, H-009]", "---",
             "# G12 placebo diagnostics for long-only bar rules (no selection)", ""]

    # ---- H-005
    t5 = h005.trades(P, dates, {"entry_k": 2, "exit_day": 3}, 1.0, fee, pv)
    t5 = t5[(t5["trading_date"] >= OOS_FROM) & (t5["trading_date"] <= OOS_TO)]
    tom_exit = set(t5["trading_date"])
    hold = 4
    pool = []
    for i in range(len(dates) - hold):
        de, dx = dates[i], dates[i + hold]
        if not (OOS_FROM <= dx <= OOS_TO) or dx in tom_exit or de.month != dx.month:
            continue
        s = sym_of(de)
        e, x = px(P, s, de, "p1500"), px(P, s, dx, "p1500")
        if e is not None and x is not None:
            pool.append(trade(dx, 1, e, x, 1.0, fee, pv)["net_pnl"])
    pool = np.array(pool)
    draws = np.array([rng.choice(pool, size=len(t5), replace=False).mean() for _ in range(20000)])
    p5 = float((draws >= t5["net_pnl"].mean()).mean())
    lines += ["## H-005 turn of month (entry_k = 2, exit_day = 3, i.e. 4-day holds)",
              f"- real: {len(t5)} trades, mean ${t5['net_pnl'].mean():.1f}/trade; random 4-day holds within a month: "
              f"mean ${draws.mean():.1f}, 95th pct ${np.percentile(draws, 95):.1f}",
              f"- **one-sided p = {p5:.4f}**", ""]

    # ---- H-009
    rows = []
    for d in dates:
        s = sym_of(d)
        dn = next_date(P, s, d)
        if dn is None or (dn - d).days > 1 or not (OOS_FROM <= dn <= OOS_TO):
            continue
        a, b, nx = px(P, s, d, "p1500"), px(P, s, dn, "p0800"), px(P, s, dn, "p1500")
        if None in (a, b, nx):
            continue
        rows.append(((b - a) * pv, (nx - a) * pv))
    on, cc = np.array(rows).T
    diff = on - (17 / 24) * cc
    t = diff.mean() / (diff.std(ddof=1) / np.sqrt(len(diff)))
    boot = np.array([rng.choice(diff, size=len(diff)).mean() for _ in range(20000)])
    p9 = float((boot <= 0).mean())
    lines += ["## H-009 overnight drift (weeknight holds, 15:00 -> 08:00 CT), gross of costs",
              f"- {len(diff)} nights: overnight mean ${on.mean():.1f}, close-to-close mean ${cc.mean():.1f} "
              f"(time share 17/24 -> ${(17/24) * cc.mean():.1f})",
              f"- overnight minus time share: mean ${diff.mean():.1f}, t = {t:.2f}, **bootstrap one-sided p = {p9:.4f}**",
              f"- after costs (~$29.5 per round trip incl. 1 tick adverse per side) the overnight mean is "
              f"${on.mean() - 29.5:.1f}/night", ""]
    out = ROOT / "vault" / "results" / "placebo-bars.md"
    out.write_text("\n".join(lines) + "\n")
    print("\n".join(lines[6:]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
