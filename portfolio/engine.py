"""Daily futures portfolio simulator (H-022 rules; registry research/hypotheses/H-022.yaml).

Timeline per market (its own trading dates): signal and size are computed at day t's close from data
up to t; the integer target is traded at day t+1's close (one full day lag); P&L of the contracts held
over (t, t+1] uses the instrument held at t. A roll (v.0 instrument changes) closes the old instrument
and opens the new one at that day's close (both legs pay costs).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from data.universe import BY_ROOT
from portfolio.data import RootData, carry_sign, chain_returns

VOL_TARGET, EWMA_SPAN, VOL_MIN_OBS = 0.15, 60, 40
SCALE_WIN, SCALE_MIN_OBS, SCALE_CAP = 252, 126, 2.5


@dataclass
class Prepared:
    root: str
    dates: list
    r: pd.Series            # chain returns
    sigma: pd.Series        # annualised EWMA vol known at t
    price: pd.Series        # close of the held instrument at t
    held: pd.Series
    closes: dict
    signals: dict           # name -> pd.Series in [-1, 1]
    rd: RootData | None = None


def _trend(r: pd.Series, lookback: int) -> pd.Series:
    lr = np.log1p(r)
    s = lr.rolling(lookback, min_periods=int(0.8 * lookback)).sum()
    return np.sign(s).fillna(0.0)


def prepare(rd: RootData) -> Prepared:
    r = chain_returns(rd)
    sigma = r.ewm(span=EWMA_SPAN, min_periods=VOL_MIN_OBS).std() * np.sqrt(252)
    price = pd.Series({d: rd.closes[rd.held[d]].get(d, np.nan) for d in rd.dates})
    t126, t252, carry = _trend(r, 126), _trend(r, 252), carry_sign(rd)
    sig = {"trend126": t126, "trend252": t252, "carry": carry, "combo": (t252 + carry) / 2}
    return Prepared(rd.root, rd.dates, r, sigma, price, rd.held, rd.closes, sig, rd)


def target_contracts(preps: list[Prepared], variant: str, capital: float,
                     signal_override: dict | None = None) -> dict[str, pd.Series]:
    """Integer contracts decided at each date's close (traded at the next close), per root."""
    cal = sorted(set().union(*[p.dates for p in preps]))
    # 1. unscaled weights w = sig * 0.15 / sqrt(N) / sigma  (fraction of capital per market)
    sigs, active = {}, pd.Series(0, index=pd.Index(cal))
    for p in preps:
        s = (signal_override or {}).get(p.root, p.signals[variant])
        ok = p.sigma.notna() & p.price.notna() & (p.sigma > 0)
        sigs[p.root] = (s.where(ok, 0.0), ok)
        active = active.add(ok.reindex(cal, fill_value=False).astype(int), fill_value=0)
    n = active.clip(lower=1)
    w = {}
    for p in preps:
        s, ok = sigs[p.root]
        w[p.root] = (s * VOL_TARGET / np.sqrt(n.reindex(p.dates).to_numpy()) / p.sigma).where(ok, 0.0)
    # 2. portfolio scale k from the unscaled book's trailing realised vol (known at t)
    u = pd.Series(0.0, index=pd.Index(cal))
    for p in preps:
        contrib = (w[p.root].shift(2) * p.r).fillna(0.0)        # weight decided at t-2 is held over (t-1, t]
        u = u.add(contrib.reindex(cal, fill_value=0.0), fill_value=0.0)
    rv = u.rolling(SCALE_WIN, min_periods=SCALE_MIN_OBS).std() * np.sqrt(252)
    k = (VOL_TARGET / rv).clip(upper=SCALE_CAP).fillna(1.0)
    out = {}
    for p in preps:
        pv = BY_ROOT[p.root].point_value
        kk = k.reindex(p.dates).to_numpy()
        tgt = np.round(kk * w[p.root].to_numpy() * capital / (pv * p.price.fillna(1.0).to_numpy()))
        out[p.root] = pd.Series(np.nan_to_num(tgt), index=pd.Index(p.dates))
    return out


def simulate(preps: list[Prepared], variant: str, capital: float, slip_ticks: float, fee_side: float,
             signal_override: dict | None = None, detail: bool = False) -> pd.DataFrame:
    """Daily portfolio P&L (detail=True: one row per market-day). signal_override: root -> pd.Series
    replacing the variant's signal (placebo)."""
    targets = target_contracts(preps, variant, capital, signal_override)
    # 3. per market: integer targets, lagged execution, P&L and costs
    rows = []
    for p in preps:
        spec = BY_ROOT[p.root]
        pv, cost_c = spec.point_value, slip_ticks * spec.tick_value + fee_side
        tgt = targets[p.root].to_numpy()
        held = p.held.to_numpy()
        pos_prev, inst_prev = 0.0, None
        for j, d in enumerate(p.dates):
            gross = 0.0
            if j > 0 and pos_prev != 0:
                s = p.closes[inst_prev]
                a, b = s.get(p.dates[j - 1]), s.get(d)
                if a is not None and b is not None:
                    gross = pos_prev * (b - a) * pv
            new = tgt[j - 1] if j > 0 else 0.0
            if inst_prev is not None and held[j] != inst_prev:
                traded = abs(pos_prev) + abs(new)                # roll: close old, open new
            else:
                traded = abs(new - pos_prev)
            rows.append((d, p.root, gross, traded * cost_c, traded, int(traded > 0)))
            pos_prev, inst_prev = new, held[j]
    df = pd.DataFrame(rows, columns=["date", "root", "gross", "costs", "contracts", "trades"])
    if detail:
        df["net"] = df["gross"] - df["costs"]
        return df
    out = df.groupby("date")[["gross", "costs", "contracts", "trades"]].sum()
    out["net"] = out["gross"] - out["costs"]
    return out
