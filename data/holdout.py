"""Final-holdout lock (decision D-014; vault/05-anti-overfitting/methodology.md).

The holdout is the most recent `holdout_months` of data. `holdout_start` in config/splits.toml is
frozen the first time a multi-month tier-A dataset is pulled (`maybe_freeze`), and never moves.
Until then a PROVISIONAL holdout applies: everything from `today - holdout_months` on. That way
nothing pulled before the freeze can leak into the future holdout.

Downloads and loads of holdout dates raise HoldoutLocked unless the unlock file
(`research/HOLDOUT_UNLOCK`, created only by the user) exists.
"""
from __future__ import annotations

import re
import tomllib
from datetime import date
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parent.parent
SPLITS_TOML = ROOT / "config" / "splits.toml"
TIER_A_SCHEMAS = {"trades", "tbbo", "mbp-1", "mbp-10", "mbo", "bbo-1s", "bbo-1m"}
MULTI_MONTH_DAYS = 60          # calendar span of one request that counts as "multi-month"


class HoldoutLocked(PermissionError):
    pass


def _months_before(d: date, months: int) -> date:
    y, m = divmod(d.year * 12 + d.month - 1 - months, 12)
    m += 1
    day = min(d.day, [31, 29 if y % 4 == 0 and (y % 100 or y % 400 == 0) else 28, 31, 30, 31, 30,
                      31, 31, 30, 31, 30, 31][m - 1])
    return date(y, m, day)


def load(path: Path = SPLITS_TOML) -> dict:
    return tomllib.loads(Path(path).read_text())


def holdout_start(path: Path = SPLITS_TOML, today: date | None = None) -> tuple[date, bool]:
    """(start date, frozen?)."""
    cfg = load(path)
    if cfg.get("holdout_start"):
        return date.fromisoformat(cfg["holdout_start"]), True
    return _months_before(today or date.today(), int(cfg["holdout_months"])), False


def unlocked(path: Path = SPLITS_TOML, root: Path = ROOT) -> bool:
    return (Path(root) / load(path)["unlock_file"]).exists()


def check(days: Iterable[date], path: Path = SPLITS_TOML, today: date | None = None, root: Path = ROOT) -> None:
    """Raise HoldoutLocked if any date is in the holdout and the user has not unlocked it."""
    start, frozen = holdout_start(path, today)
    bad = sorted(d for d in days if d >= start)
    if bad and not unlocked(path, root):
        kind = "frozen" if frozen else "provisional"
        raise HoldoutLocked(f"{len(bad)} date(s) from {bad[0]} are in the {kind} holdout (from {start}). "
                            f"Only the user may unlock it ({load(path)['unlock_file']}).")


def development_dates(days: Iterable[date], path: Path = SPLITS_TOML, today: date | None = None) -> list[date]:
    start, _ = holdout_start(path, today)
    return sorted(d for d in days if d < start)


def maybe_freeze(schema: str, days: Iterable[date], path: Path = SPLITS_TOML,
                 today: date | None = None) -> date | None:
    """Freeze holdout_start at the first multi-month tier-A request. Returns the date if it froze now."""
    days = sorted(days)
    cfg = load(path)
    if cfg.get("holdout_start") or schema not in TIER_A_SCHEMAS or not days:
        return None
    if (days[-1] - days[0]).days < MULTI_MONTH_DAYS:
        return None
    start = _months_before(today or date.today(), int(cfg["holdout_months"]))
    text = Path(path).read_text()
    new = re.sub(r'^holdout_start\s*=\s*""', f'holdout_start = "{start.isoformat()}"', text, count=1, flags=re.M)
    if new == text:
        raise RuntimeError("could not find an empty holdout_start line to freeze")
    Path(path).write_text(new)
    return start
