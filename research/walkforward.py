"""Walk-forward folds over development trading dates (vault/05-anti-overfitting/methodology.md).

Rolling train window -> test window, stepping forward; `embargo_days` TRADING days are dropped
between the end of train and the start of test. Test windows never overlap, and holdout dates
are removed before anything else (data.holdout.development_dates).
"""
from __future__ import annotations

import tomllib
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from data import holdout


@dataclass(frozen=True)
class Fold:
    k: int
    train: tuple[date, ...]
    test: tuple[date, ...]


def _add_months(d: date, months: int) -> date:
    y, m = divmod(d.year * 12 + d.month - 1 + months, 12)
    return date(y, m + 1, 1)


def walk_forward(dates: list[date], train_months: int = 12, test_months: int = 3, step_months: int = 3,
                 embargo_days: int = 1, splits_path: Path = holdout.SPLITS_TOML,
                 today: date | None = None) -> list[Fold]:
    dev = holdout.development_dates(dates, splits_path, today)
    if not dev:
        return []
    folds, k = [], 0
    start = date(dev[0].year, dev[0].month, 1)
    while True:
        train_end = _add_months(start, train_months)            # exclusive month boundaries
        test_end = _add_months(train_end, test_months)
        train = [d for d in dev if start <= d < train_end]
        test_all = [d for d in dev if train_end <= d < test_end]
        if not test_all or train_end > dev[-1]:
            break
        test = test_all[embargo_days:]                          # embargo: first trading day(s) after train
        if train and test:
            folds.append(Fold(k, tuple(train), tuple(test)))
            k += 1
        start = _add_months(start, step_months)
    return folds


def from_config(dates: list[date], splits_path: Path = holdout.SPLITS_TOML, today: date | None = None) -> list[Fold]:
    wf = tomllib.loads(Path(splits_path).read_text())["walk_forward"]
    return walk_forward(dates, wf["train_months"], wf["test_months"], wf["step_months"], wf["embargo_days"],
                        splits_path, today)
