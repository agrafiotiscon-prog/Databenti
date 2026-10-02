"""CLI: estimate and/or download cached Databento data.

Examples
--------
  # Price only (no download):
  python -m data.fetch --schemas trades mbp-10 mbo ohlcv-1m --start 2024-03-05 --end 2024-03-07 --dry-run

  # Download (asks for confirmation if total > $5):
  python -m data.fetch --schemas trades ohlcv-1m --start 2024-03-05 --end 2024-03-07

By default the contract is chosen per trading date by the roll rule
(ES.c.0 normally, ES.c.1 from the roll Thursday to expiry). Pass --symbol to
force one symbol.
"""
from __future__ import annotations

import argparse
from datetime import date

from .config import DEFAULT_ROOT, DEFAULT_STYPE_IN, SUPPORTED_SCHEMAS
from .cost_guard import CostLimitExceeded
from .download import Downloader
from .sessions import trading_dates


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--schemas", nargs="+", default=["trades"], choices=SUPPORTED_SCHEMAS)
    ap.add_argument("--symbol", default=None, help="force a symbol (default: roll rule per date)")
    ap.add_argument("--root", default=DEFAULT_ROOT, help="product root for the roll rule, e.g. ES, NQ")
    ap.add_argument("--stype-in", default=DEFAULT_STYPE_IN)
    ap.add_argument("--start", required=True, type=date.fromisoformat, help="first trading date")
    ap.add_argument("--end", required=True, type=date.fromisoformat, help="last trading date (inclusive)")
    ap.add_argument("--rth-only", action="store_true")
    ap.add_argument("--dry-run", action="store_true", help="only print cost estimates")
    args = ap.parse_args(argv)

    dl = Downloader()
    tdays = trading_dates(args.start, args.end)
    plan = dl.session_plan(tdays, args.symbol, args.root, args.rth_only)
    print(f"Trading dates: {[d.isoformat() for d in tdays]}")
    for sym, days in plan.items():
        print(f"  {sym}: UTC days {[d.isoformat() for d in sorted(days)]}")

    # Price everything up front so the user sees one combined total.
    total = sum(dl.estimate(s, days, sym, args.stype_in) for s in args.schemas for sym, days in plan.items())
    print(f"\nGRAND TOTAL estimated cost for missing data: ${total:,.4f}")
    if args.dry_run:
        return 0

    allow = False
    if total > dl.max_cost_usd:
        ans = input(f"Total ${total:,.2f} exceeds ${dl.max_cost_usd:,.2f}. Type 'yes' to download: ")
        if ans.strip().lower() != "yes":
            print("Aborted. Nothing downloaded.")
            return 1
        allow = True

    try:
        for s in args.schemas:
            dl.fetch_sessions(s, tdays, args.symbol, args.stype_in, args.rth_only,
                              allow_over_limit=allow, root=args.root)
    except CostLimitExceeded as e:
        print(e)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
