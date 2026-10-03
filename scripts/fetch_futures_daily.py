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
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args(argv)
    dl = Downloader()
    todo = [(request(dl, f"{s.root}.v.{k}"), path_for(dl, f"{s.root}.v.{k}")) for s in UNIVERSE for k in (0, 1)]
    todo = [(r, p) for r, p in todo if not p.exists()]
    import socket
    socket.setdefaulttimeout(300)               # a metadata call once hung forever without a timeout
    cost = sum(dl.guard.check([r]) for r, _ in todo)   # priced and logged once per file
    print(f"{len(todo)} files to fetch, estimated ${cost:.2f}; spent so far ${dl.spent_total():.2f}", flush=True)
    if a.dry or not todo:
        return 0
    dl.check_total_cap(cost)
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from data import cache

    def fetch(r, path):
        path.parent.mkdir(parents=True, exist_ok=True)
        part = cache.part_path(path)
        part.unlink(missing_ok=True)
        try:
            dl.client.timeseries.get_range(dataset=r.dataset, schema=r.schema, symbols=r.symbols,
                                           stype_in=r.stype_in, start=r.start, end=r.end, path=part)
        except BaseException:
            part.unlink(missing_ok=True)
            raise
        return r, path

    with ThreadPoolExecutor(a.workers) as ex:                    # Databento resolves continuous symbols slowly
        for fut in as_completed([ex.submit(fetch, r, path) for r, path in todo]):
            r, path = fut.result()
            cache.finalize(path)                                 # finalize + log in the main thread
            dl._log_download(r, path)
            print(f"  [download] {path.relative_to(dl.cache_dir)}", flush=True)
    print(f"done; spent now ${dl.spent_total():.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
