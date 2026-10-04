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


def expiry_spacing_years(rd) -> float:
    """Median gap between consecutive contract expiries, from the last date each expired instrument
    appears in v.0/v.1 (contract calendar, not prices). Falls back to a quarter if unknown."""
    last = sorted(r[0] for r in rd.expiry_rank.values() if r[0] != pd.Timestamp.max.date())
    gaps = [(b - a).days for a, b in zip(last, last[1:]) if (b - a).days > 0]
    return float(np.median(gaps)) / 365.25 if gaps else 0.25


def carry_value(rd) -> pd.Series:
    """Annualised carry log(P_near / P_far) / gap_years on each date (NaN if unknown). gap_years = the
    gap between the two instruments' last appearances in v.0/v.1 (contract calendar, not prices); when the
    far one is still listed at the end of the data, the root's median expiry spacing is used."""
    sp = expiry_spacing_years(rd)
    END = pd.Timestamp.max.date()
    out = pd.Series(np.nan, index=pd.Index(rd.dates))
    for d in rd.dates:
        i0, i1 = rd.held.get(d), rd.nxt.get(d)
        if i1 is None or (isinstance(i1, float) and np.isnan(i1)) or i0 == i1:
            continue
        p0, p1 = rd.closes[i0].get(d), rd.closes[i1].get(d)
        if p0 is None or p1 is None or p0 <= 0 or p1 <= 0:
            continue
        (near, n_id), (far, f_id) = sorted([(p0, i0), (p1, i1)], key=lambda t: rd.expiry_rank[t[1]])
        a, b = rd.expiry_rank[n_id][0], rd.expiry_rank[f_id][0]
        gap = (b - a).days / 365.25 if b != END and a != END and (b - a).days >= 20 else sp
        out[d] = float(np.log(near / far)) / gap
    return out


@register("H-024")
def h024(preps: list[Prepared]) -> dict:
    raw = {p.root: carry_value(p.rd) for p in preps}
    smooth = {r: s.rolling(63, min_periods=40).mean() for r, s in raw.items()}
    return {"xsc_sector": cross_sectional(raw, by_sector=True), "xsc_global": cross_sectional(raw, by_sector=False),
            "xsc_sector_smooth": cross_sectional(smooth, by_sector=True),
            "xsc_global_smooth": cross_sectional(smooth, by_sector=False)}


@register("H-025")
def h025(preps: list[Prepared]) -> dict:
    out = {}
    for lb in (126, 252):
        sc = {p.root: momentum_score(p, lb, skip=21) for p in preps}
        out[f"xsm{lb}_sector"] = cross_sectional(sc, by_sector=True)
        out[f"xsm{lb}_global"] = cross_sectional(sc, by_sector=False)
    return out


COMMODITY_SECTORS = ("energy", "metals", "grains", "livestock")


def near_far_returns(rd) -> pd.DataFrame:
    """Own close-to-close returns t-1 -> t of the near and far instrument (by expiry) of day t-1's v.0/v.1."""
    rows = {}
    for a, b in zip(rd.dates, rd.dates[1:]):
        i0, i1 = rd.held.get(a), rd.nxt.get(a)
        if i1 is None or (isinstance(i1, float) and np.isnan(i1)) or i0 == i1:
            continue
        n_id, f_id = sorted((i0, i1), key=lambda i: rd.expiry_rank[i])
        rr = []
        for i in (n_id, f_id):
            s = rd.closes[i]
            pa, pb = s.get(a), s.get(b)
            rr.append(pb / pa - 1 if pa is not None and pb is not None and pa > 0 else np.nan)
        rows[b] = rr
    df = pd.DataFrame.from_dict(rows, orient="index", columns=["near", "far"])
    return df.reindex(rd.dates)


def basis_momentum(rd, lookback: int) -> pd.Series:
    nf = near_far_returns(rd)
    d = np.log1p(nf["near"]) - np.log1p(nf["far"])
    return d.rolling(lookback, min_periods=int(0.8 * lookback)).sum()


@register("H-026")
def h026(preps: list[Prepared]) -> dict:
    com = [p for p in preps if BY_ROOT[p.root].sector in COMMODITY_SECTORS]
    zero = {p.root: pd.Series(0.0, index=pd.Index(p.dates)) for p in preps}
    out = {}
    for lb in (126, 252):
        sc = {p.root: basis_momentum(p.rd, lb) for p in com}
        out[f"tsbm{lb}"] = {**zero, **{r: np.sign(s).fillna(0.0) for r, s in sc.items()}}
        out[f"xsbm{lb}"] = {**zero, **cross_sectional(sc, by_sector=False)}
    return out
