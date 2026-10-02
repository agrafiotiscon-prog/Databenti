"""Cost-checked, cached historical downloads.

Typical use:

    from data.download import Downloader
    dl = Downloader()                      # reads .env, builds client
    paths = dl.fetch_sessions("trades", [date(2024, 3, 5)])

Flow for every call:
  1. Work out the UTC-day chunks needed.
  2. Drop chunks already in the cache (nothing is downloaded twice).
  3. Price ALL missing chunks via metadata.get_cost and print the total.
  4. Abort if total > limit (default $5) unless explicitly allowed.
  5. Download each chunk to a .part file, then atomically rename.
"""
from __future__ import annotations

import csv
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable

from . import cache
from .config import (DATASET, DEFAULT_ROOT, DEFAULT_STYPE_IN, DEFAULT_SYMBOL, SUPPORTED_SCHEMAS,
                     get_client, load_settings)
from .contracts import DEFAULT_ROLL_DAYS_BEFORE_EXPIRY, continuous_symbol
from .cost_guard import CostGuard, Request
from .sessions import utc_days_for_session


def _day_bounds(day: date) -> tuple[str, str]:
    start = datetime(day.year, day.month, day.day, tzinfo=timezone.utc)
    end = start + timedelta(days=1)
    return start.isoformat(), end.isoformat()


class Downloader:
    def __init__(self, client=None, cache_dir: Path | None = None, max_cost_usd: float | None = None,
                 dataset: str = DATASET):
        settings = load_settings()
        self.client = client if client is not None else get_client()
        self.cache_dir = Path(cache_dir) if cache_dir else settings.cache_dir
        self.max_cost_usd = settings.max_cost_usd if max_cost_usd is None else max_cost_usd
        self.dataset = dataset
        self.guard = CostGuard(self.client, self.max_cost_usd, self.cache_dir / "spend_log.csv")

    # ------------------------------------------------------------------ planning
    def plan(self, schema: str, days: Iterable[date], symbol: str = DEFAULT_SYMBOL,
             stype_in: str = DEFAULT_STYPE_IN) -> tuple[list[Path], list[tuple[Request, Path]]]:
        """Return (all chunk paths, missing (request, path) pairs)."""
        if schema not in SUPPORTED_SCHEMAS:
            raise ValueError(f"Unsupported schema {schema!r}; expected one of {SUPPORTED_SCHEMAS}")
        all_paths, missing = [], []
        for day in sorted(set(days)):
            p = cache.chunk_path(self.cache_dir, self.dataset, schema, symbol, day)
            all_paths.append(p)
            if not cache.is_cached(p):
                start, end = _day_bounds(day)
                missing.append((Request(self.dataset, schema, symbol, stype_in, start, end), p))
        return all_paths, missing

    def estimate(self, schema: str, days: Iterable[date], symbol: str = DEFAULT_SYMBOL,
                 stype_in: str = DEFAULT_STYPE_IN) -> float:
        """Dry run: price what is missing, download nothing."""
        _, missing = self.plan(schema, days, symbol, stype_in)
        if not missing:
            print(f"  [cache] {schema} {symbol}: everything already cached, cost $0")
            return 0.0
        return self.guard.check([r for r, _ in missing], allow_over_limit=True)

    # ------------------------------------------------------------------ fetching
    def fetch_days(self, schema: str, days: Iterable[date], symbol: str = DEFAULT_SYMBOL,
                   stype_in: str = DEFAULT_STYPE_IN, allow_over_limit: bool = False) -> list[Path]:
        all_paths, missing = self.plan(schema, days, symbol, stype_in)
        if not missing:
            print(f"  [cache] {schema} {symbol}: all {len(all_paths)} chunk(s) cached")
            return all_paths
        # Always price before downloading. Raises CostLimitExceeded if too expensive.
        self.guard.check([r for r, _ in missing], allow_over_limit=allow_over_limit)
        self._download(missing)
        return all_paths

    def _download(self, missing: list[tuple[Request, Path]]) -> None:
        """Download already-priced chunks (callers must run the cost guard first)."""
        for req, path in missing:
            path.parent.mkdir(parents=True, exist_ok=True)
            part = cache.part_path(path)
            part.unlink(missing_ok=True)       # leftover from an interrupted run; the client refuses to overwrite
            try:
                self.client.timeseries.get_range(
                    dataset=req.dataset, schema=req.schema, symbols=req.symbols,
                    stype_in=req.stype_in, start=req.start, end=req.end, path=part,
                )
            except BaseException:
                part.unlink(missing_ok=True)
                raise
            cache.finalize(path)
            self._log_download(req, path)
            print(f"  [download] {path.relative_to(self.cache_dir)}")

    def _log_download(self, req: Request, path: Path) -> None:
        """Record a completed download. spend_log.csv holds every estimate (dry runs too);
        download_log.csv holds only what was actually fetched, i.e. what was billed."""
        log = self.cache_dir / "download_log.csv"
        new = not log.exists()
        with log.open("a", newline="") as f:
            w = csv.writer(f)
            if new:
                w.writerow(["downloaded_at_utc", "dataset", "schema", "symbols", "start", "end",
                            "estimated_cost_usd", "bytes"])
            cost = self.guard.last_costs.get(req)
            w.writerow([datetime.now(timezone.utc).isoformat(), req.dataset, req.schema, req.symbols,
                        req.start, req.end, "" if cost is None else f"{cost:.6f}", path.stat().st_size])

    def session_plan(self, trading_days: Iterable[date], symbol: str | None = None,
                     root: str = DEFAULT_ROOT, rth_only: bool = False,
                     roll_days_before: int = DEFAULT_ROLL_DAYS_BEFORE_EXPIRY) -> dict[str, set[date]]:
        """Map symbol -> UTC days needed. With symbol=None the contract is chosen
        per trading date by the roll rule (ES.c.0 normally, ES.c.1 in roll week)."""
        plan: dict[str, set[date]] = {}
        for td in trading_days:
            sym = symbol or continuous_symbol(td, root, roll_days_before)
            plan.setdefault(sym, set()).update(utc_days_for_session(td, rth_only))
        return plan

    def fetch_sessions(self, schema: str, trading_days: Iterable[date], symbol: str | None = None,
                       stype_in: str = DEFAULT_STYPE_IN, rth_only: bool = False,
                       allow_over_limit: bool = False, root: str = DEFAULT_ROOT,
                       roll_days_before: int = DEFAULT_ROLL_DAYS_BEFORE_EXPIRY) -> list[Path]:
        """Fetch all UTC-day chunks covering the given CME trading sessions.

        All missing chunks (across symbols) are priced together before anything
        is downloaded, so the $ limit applies to the whole request.
        """
        all_paths: list[Path] = []
        missing: list[tuple[Request, Path]] = []
        for sym, days in self.session_plan(trading_days, symbol, root, rth_only, roll_days_before).items():
            paths, miss = self.plan(schema, days, sym, stype_in)
            all_paths += paths
            missing += miss
        if not missing:
            print(f"  [cache] {schema}: all {len(all_paths)} chunk(s) cached")
            return all_paths
        self.guard.check([r for r, _ in missing], allow_over_limit=allow_over_limit)
        self._download(missing)
        return all_paths

    def roll_calendar(self, start: date, end: date, symbol: str = DEFAULT_SYMBOL):
        """Free symbology lookup: which instrument_id the continuous symbol maps to per day."""
        from .rolls import roll_calendar

        res = self.client.symbology.resolve(
            dataset=self.dataset, symbols=[symbol], stype_in=DEFAULT_STYPE_IN,
            stype_out="instrument_id", start_date=start.isoformat(),
            end_date=(end + timedelta(days=1)).isoformat(),
        )
        return roll_calendar(res, symbol)
