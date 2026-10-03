"""R7: download daily bars (ohlcv-1d) for the diversified universe, volume-ranked continuous v.0 and v.1.

  python scripts/fetch_futures_daily.py [--dry]

Cost-checked per request and against the cumulative cap (data/download.py). ~$0.047 per symbol.
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from data.cost_guard import Request          # noqa: E402
from data.universe import END, START, UNIVERSE   # noqa: E402


def path_for(dl, symbol: str) -> Path:
    return dl.cache_dir / dl.dataset / "ohlcv-1d-range" / symbol / f"{START}_{END}.dbn.zst"


def request(dl, symbol: str) -> Request:
    iso = lambda s: datetime.fromisoformat(s).replace(tzinfo=timezone.utc).isoformat()   # noqa: E731
    return Request(dl.dataset, "ohlcv-1d", symbol, "continuous", iso(START), iso(END))


def main(argv=None) -> int:
    from data.download import Downloader
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args(argv)
    dl = Downloader()
    todo = [(request(dl, f"{s.root}.v.{k}"), path_for(dl, f"{s.root}.v.{k}")) for s in UNIVERSE for k in (0, 1)]
    todo = [(r, p) for r, p in todo if not p.exists()]
    cost = sum(dl.guard.estimate(r) for r, _ in todo)
    print(f"{len(todo)} files to fetch, estimated ${cost:.2f}; spent so far ${dl.spent_total():.2f}")
    if a.dry or not todo:
        return 0
    dl.check_total_cap(cost)
    for r, p in todo:
        dl.guard.check([r])
        dl._download([(r, p)])
    print(f"done; spent now ${dl.spent_total():.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
