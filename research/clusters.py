"""Cluster analysis of trials (methodology.md 6c; Phase 4, R4.4). numpy only.

Trials are clustered by the correlation of their daily PnL: distance d = sqrt((1 - rho) / 2),
average-linkage agglomeration, number of clusters chosen by the best mean silhouette (k >= 2;
a single cluster if no split has a positive silhouette). The number of clusters is the
EFFECTIVE number of independent trials K for the deflated Sharpe.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def corr_distance(pnl: pd.DataFrame) -> np.ndarray:
    c = np.nan_to_num(np.corrcoef(np.asarray(pnl, float).T), nan=0.0)
    np.fill_diagonal(c, 1.0)
    return np.sqrt(np.clip((1 - c) / 2, 0, 1))


def _average_linkage(d: np.ndarray) -> list[list[list[int]]]:
    """All partitions from n singletons down to 1 cluster (index = n_clusters - 1)."""
    clusters = [[i] for i in range(len(d))]
    history = {len(clusters): [list(c) for c in clusters]}
    while len(clusters) > 1:
        best, pair = np.inf, None
        for a in range(len(clusters)):
            for b in range(a + 1, len(clusters)):
                dist = d[np.ix_(clusters[a], clusters[b])].mean()
                if dist < best:
                    best, pair = dist, (a, b)
        a, b = pair
        clusters[a] = clusters[a] + clusters[b]
        del clusters[b]
        history[len(clusters)] = [list(c) for c in clusters]
    return history


def silhouette(d: np.ndarray, labels: np.ndarray) -> float:
    n, out = len(d), []
    for i in range(n):
        same = labels == labels[i]
        if same.sum() <= 1:
            out.append(0.0)
            continue
        a = d[i, same & (np.arange(n) != i)].mean()
        b = min(d[i, labels == l].mean() for l in set(labels) if l != labels[i])
        out.append((b - a) / max(a, b) if max(a, b) > 0 else 0.0)
    return float(np.mean(out))


def cluster_trials(pnl: pd.DataFrame, max_k: int | None = None) -> dict:
    """pnl: T days x N trials. Returns labels, effective K, medoid per cluster, silhouette."""
    d = corr_distance(pnl)
    n = d.shape[0]
    if n < 3:
        labels = np.zeros(n, int)
        return {"labels": labels, "k": 1, "silhouette": 0.0, "medoids": {0: int(np.argmin(d.sum(1)))}}
    hist = _average_linkage(d)
    best_k, best_s = 1, 0.0
    for k in range(2, min(max_k or n - 1, n - 1) + 1):
        lab = np.empty(n, int)
        for ci, members in enumerate(hist[k]):
            lab[members] = ci
        s = silhouette(d, lab)
        if s > best_s:
            best_k, best_s = k, s
    labels = np.empty(n, int)
    for ci, members in enumerate(hist[best_k]):
        labels[members] = ci
    medoids = {int(c): int(np.flatnonzero(labels == c)[np.argmin(d[np.ix_(labels == c, labels == c)].sum(1))])
               for c in set(labels)}
    return {"labels": labels, "k": int(best_k), "silhouette": best_s, "medoids": medoids}


def cluster_quality(labels: np.ndarray, oos_net: np.ndarray, mc_net_p5: np.ndarray | None = None,
                    min_share: float = 0.70) -> pd.DataFrame:
    """Per cluster: size, share profitable OOS (and with positive MC 5th pct), credible?"""
    rows = []
    for c in sorted(set(labels)):
        m = labels == c
        prof = oos_net[m] > 0
        if mc_net_p5 is not None:
            prof = prof & (mc_net_p5[m] > 0)
        rows.append({"cluster": int(c), "size": int(m.sum()), "share_profitable": float(prof.mean()),
                     "credible": bool(prof.mean() >= min_share and m.sum() >= 2)})
    return pd.DataFrame(rows).set_index("cluster")
