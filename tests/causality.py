"""Generic no-lookahead checks for features.

For each cut time c: run the feature on input truncated to ts_recv < c and on
the full input. Every output row known strictly before c must be identical in
both, and the same set of such rows must exist. A second check perturbs all
input after c and requires the same rows to be unchanged.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def _known_before(out: pd.DataFrame, cut) -> pd.DataFrame:
    o = out.reset_index()
    o = o[o["known_at"] < cut]
    return o.sort_values(list(o.columns)).reset_index(drop=True)


def assert_causal(feature, df: pd.DataFrame, n_cuts: int = 6, seed: int = 0):
    rng = np.random.default_rng(seed)
    lo, hi = df.index[len(df) // 10], df.index[-len(df) // 10]
    cuts = [lo + (hi - lo) * float(x) for x in rng.random(n_cuts)]
    full = feature(df)
    for cut in cuts:
        trunc = feature(df[df.index < cut])
        a, b = _known_before(full, cut), _known_before(trunc, cut)
        pd.testing.assert_frame_equal(a, b, check_dtype=False, obj=f"truncated at {cut}")
        future = df.index >= cut
        pert = df.copy()
        pert.loc[future, "size"] = (pert.loc[future, "size"].astype("int64") * 3 + 1).astype("uint32")
        pert.loc[future, "price"] = pert.loc[future, "price"] + 2.5
        c = _known_before(feature(pert), cut)
        pd.testing.assert_frame_equal(a, c, check_dtype=False, obj=f"perturbed after {cut}")
