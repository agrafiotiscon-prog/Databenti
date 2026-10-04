"""Cross-market signals for portfolio hypotheses (R8.1).

A hypothesis that only needs a new signal registers a builder in BUILDERS:
    builder(preps) -> {variant: {root: pd.Series(date -> signal in [-1, 1])}}
scripts/run_portfolio.py injects these into each Prepared.signals and runs the usual protocol
(walk-forward, gates, G12 placebo). Every signal at date t may use data up to t only; the engine
adds the one-day execution lag.
"""
from __future__ import annotations

from typing import Callable

import numpy as np
import pandas as pd

from data.universe import BY_ROOT
from portfolio.engine import Prepared

BUILDERS: dict[str, Callable[[list[Prepared]], dict]] = {}


def register(hyp: str):
    def deco(fn):
        BUILDERS[hyp] = fn
        return fn
    return deco


def builtin(preps: list[Prepared]) -> dict:
    """Signals already computed by engine.prepare (trend126, trend252, carry, combo)."""
    names = set.intersection(*[set(p.signals) for p in preps]) if preps else set()
    return {v: {p.root: p.signals[v] for p in preps} for v in names}


def momentum_score(p: Prepared, lookback: int, skip: int = 0) -> pd.Series:
    """Sum of log chain returns over (t-lookback-skip, t-skip]; NaN until 80% of the window exists."""
    lr = np.log1p(p.r)
    return lr.rolling(lookback, min_periods=int(0.8 * lookback)).sum().shift(skip)


def cross_sectional(scores: dict[str, pd.Series], by_sector: bool = True, frac: float = 1 / 3,
                    min_names: int = 3) -> dict[str, pd.Series]:
    """Rank scores across markets on each date: top `frac` -> +1, bottom `frac` -> -1, rest 0.
    Ranking is within sector (data/universe.py) when by_sector; groups with fewer than min_names
    valid scores that day get 0. Each output series is indexed like its input."""
    df = pd.DataFrame(scores)
    out = pd.DataFrame(0.0, index=df.index, columns=df.columns)
    groups = ({BY_ROOT[r].sector for r in df.columns} if by_sector else {None})
    for g in groups:
        cols = [r for r in df.columns if not by_sector or BY_ROOT[r].sector == g]
        sub = df[cols]
        n = sub.notna().sum(axis=1)
        k = np.floor(n * frac)
        rk = sub.rank(axis=1, method="first")               # 1 = lowest
        ok = (n >= min_names) & (k >= 1)
        long = rk.gt(n - k, axis=0) & ok.to_numpy()[:, None]
        short = rk.le(k, axis=0) & ok.to_numpy()[:, None]
        out.loc[:, cols] = long.astype(float) - short.astype(float)
    return {r: out[r].reindex(scores[r].index).fillna(0.0) for r in scores}
