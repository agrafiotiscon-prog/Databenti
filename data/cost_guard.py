"""Cost guard: every historical download must be priced first.

`CostGuard.check()` calls `client.metadata.get_cost(...)` for each pending
request, prints the estimate, appends it to a spend log, and refuses to
proceed if the total exceeds the configured limit (default $5) unless the
caller explicitly passes `allow_over_limit=True` (which the CLI only does
after an interactive "yes").
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


class CostLimitExceeded(RuntimeError):
    pass


@dataclass(frozen=True)
class Request:
    dataset: str
    schema: str
    symbols: str
    stype_in: str
    start: str  # ISO timestamp (UTC)
    end: str    # ISO timestamp (UTC), exclusive


class CostGuard:
    def __init__(self, client, max_cost_usd: float, log_path: Path | None = None):
        self.client = client
        self.max_cost_usd = max_cost_usd
        self.log_path = log_path

    def estimate(self, req: Request) -> float:
        return float(
            self.client.metadata.get_cost(
                dataset=req.dataset,
                start=req.start,
                end=req.end,
                symbols=req.symbols,
                schema=req.schema,
                stype_in=req.stype_in,
            )
        )

    def check(self, requests: list[Request], allow_over_limit: bool = False) -> float:
        """Price all requests; raise CostLimitExceeded if total > limit."""
        total = 0.0
        for req in requests:
            cost = self.estimate(req)
            total += cost
            print(f"  [cost] {req.schema:9s} {req.symbols} {req.start[:10]} -> ${cost:,.4f}")
            self._log(req, cost)
        print(f"  [cost] TOTAL estimated: ${total:,.4f} (limit ${self.max_cost_usd:,.2f})")
        if total > self.max_cost_usd and not allow_over_limit:
            raise CostLimitExceeded(
                f"Estimated cost ${total:,.2f} exceeds limit ${self.max_cost_usd:,.2f}. "
                "Nothing was downloaded. Re-run with explicit approval to proceed."
            )
        return total

    def _log(self, req: Request, cost: float) -> None:
        if self.log_path is None:
            return
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        new = not self.log_path.exists()
        with self.log_path.open("a", newline="") as f:
            w = csv.writer(f)
            if new:
                w.writerow(["logged_at_utc", "dataset", "schema", "symbols", "stype_in",
                            "start", "end", "estimated_cost_usd"])
            w.writerow([datetime.now(timezone.utc).isoformat(), req.dataset, req.schema,
                        req.symbols, req.stype_in, req.start, req.end, f"{cost:.6f}"])
