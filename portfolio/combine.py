"""Combine daily P&L sleeves into one book with causal risk-based weights (R8.6).

Weights for day t use sleeve P&L up to t-1 only (trailing window), so a combined book can be evaluated
walk-forward without lookahead. Only sleeves registered BEFORE the combination is seen may be combined
(research/ROUTINE.md); this module does no selection.

  inverse_vol : w_i ∝ 1 / sigma_i
  erc         : equal risk contribution w_i * (Σw)_i equal for all i (Maillard, Roncalli & Teiletche 2010),
                solved by fixed-point iteration on the trailing covariance
Both are then scaled so the book's trailing vol hits `target_vol` (annualised, as a fraction of capital),
with no sleeve's effective weight above `max_leverage` (1.0 = the sleeve run at full capital).
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def erc_weights(cov: np.ndarray, iters: int = 500, tol: float = 1e-10) -> np.ndarray:
    """Long-only equal-risk-contribution weights summing to 1."""
    n = cov.shape[0]
    w = np.ones(n) / n
    for _ in range(iters):
        rc = w * (cov @ w)
        if not np.all(np.isfinite(rc)) or rc.sum() <= 0:
            return np.ones(n) / n
        # multiplicative update towards equal risk contributions
        w_new = w * (rc.mean() / np.maximum(rc, 1e-18)) ** 0.5
        w_new /= w_new.sum()
        if np.max(np.abs(w_new - w)) < tol:
            return w_new
        w = w_new
    return w


def combine(sleeves: pd.DataFrame, capital: float, method: str = "erc", window: int = 252, min_obs: int = 126,
            target_vol: float = 0.15, max_leverage: float = 2.5) -> pd.DataFrame:
    """sleeves: daily net P&L in $ per sleeve (columns), each run at `capital`. Returns a frame with the
    weights per sleeve (w_<name>), the scale and the combined daily P&L ('net')."""
    s = sleeves.fillna(0.0)
    names = list(s.columns)
    W = pd.DataFrame(np.nan, index=s.index, columns=names)
    scale = pd.Series(np.nan, index=s.index)
    x = s.to_numpy() / capital
    for t in range(len(s)):
        lo = max(0, t - window)
        hist = x[lo:t]                                   # rows strictly before t
        if len(hist) < min_obs:
            continue
        cov = np.cov(hist, rowvar=False).reshape(len(names), len(names))
        sd = np.sqrt(np.clip(np.diag(cov), 0, None))
        if method == "inverse_vol":
            w = np.where(sd > 0, 1 / np.where(sd > 0, sd, 1), 0.0)
            w = w / w.sum() if w.sum() > 0 else np.ones(len(names)) / len(names)
        elif method == "erc":
            ok = sd > 0
            w = np.zeros(len(names))
            if ok.any():
                w[ok] = erc_weights(cov[np.ix_(ok, ok)])
        else:
            raise ValueError(f"unknown method {method}")
        book_vol = float(np.sqrt(w @ cov @ w) * np.sqrt(252))
        k = min(target_vol / book_vol, max_leverage / max(w.max(), 1e-12)) if book_vol > 0 else 0.0
        W.iloc[t] = w
        scale.iloc[t] = k
    eff = W.mul(scale, axis=0).fillna(0.0)
    out = W.add_prefix("w_")
    out["scale"] = scale
    out["net"] = (eff * s).sum(axis=1)
    return out
