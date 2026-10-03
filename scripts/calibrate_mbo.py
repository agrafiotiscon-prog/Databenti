"""Calibrate MBO detector parameters on real data WITHOUT looking at any strategy outcome (R2.3).

  python scripts/calibrate_mbo.py --date 2024-03-05 [--rth-only]

Synthetic icebergs (features.iceberg.synthetic_icebergs, parameter dt):
  after an order is fully removed by fills, is the NEXT add at that side+price the same size
  as the removed clip more often right away than one second later? Measured as the same-size
  share of adds in [t, t+dt) versus [t+1s, t+1s+dt). The share controls for the burst of
  activity after a level trades out. Precision ~= 1 - share_far / share_near: the fraction of
  same-size re-adds above chance. A dt is only useful where precision is clearly positive.

Spoof-like (features.spoof.spoof_like_events, parameter min_size):
  for adds at >= 4 ticks from the touch, the spoof-like rate (pulled within 10 s, price never
  within 2 ticks) by size bucket. If large orders are not pulled more often than small ones,
  the label is ordinary behaviour at that size.

Report: vault/results/mbo-calibration-<date>.md. Uses cached data only.
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

FAR_OFFSET = pd.Timedelta("1s")
DT_GRID = ("500us", "1ms", "2ms", "5ms", "10ms", "50ms")
SIZE_BUCKETS = (1, 2, 5, 10, 20, 50, 100, 200, 10**9)


def readd_precision(ann: pd.DataFrame, dt_grid=DT_GRID, far_offset: pd.Timedelta = FAR_OFFSET,
                    min_clip: int = 1) -> pd.DataFrame:
    """Same-size share of adds after full fill-removals (clip >= min_clip), near vs one second later."""
    kind = ann["kind"].to_numpy()
    t = ann.index.asi8
    side, price = ann["side"].astype(str).to_numpy(), ann["price"].to_numpy(float)
    new, orig = ann["new_size"].to_numpy(np.int64), ann["orig_size"].to_numpy(np.int64)
    adds = np.flatnonzero(kind == "add")
    by_level: dict[tuple, tuple[np.ndarray, np.ndarray]] = {}
    df = pd.DataFrame({"s": side[adds], "p": price[adds], "t": t[adds], "q": new[adds]})
    for key, g in df.groupby(["s", "p"], sort=False):
        by_level[key] = (g["t"].to_numpy(), g["q"].to_numpy())
    ends = np.flatnonzero(np.isin(kind, ["fill_removal", "modify_down_fill"]) & (new == 0) & (orig >= max(min_clip, 1)))
    rows = []
    for dt in dt_grid:
        w, off = pd.Timedelta(dt).value, far_offset.value
        cnt = {"near_same": 0, "near_all": 0, "far_same": 0, "far_all": 0}
        for e in ends:
            lv = by_level.get((side[e], price[e]))
            if lv is None:
                continue
            ts, qs = lv
            for tag, lo in (("near", t[e]), ("far", t[e] + off)):
                a, b = np.searchsorted(ts, lo, "left"), np.searchsorted(ts, lo + w, "left")
                if b > a:
                    cnt[f"{tag}_all"] += b - a
                    cnt[f"{tag}_same"] += int((qs[a:b] == orig[e]).sum())
        near = cnt["near_same"] / cnt["near_all"] if cnt["near_all"] else np.nan
        far = cnt["far_same"] / cnt["far_all"] if cnt["far_all"] else np.nan
        rows.append({"dt": dt, **cnt, "same_share_near": near, "same_share_far": far,
                     "precision_est": 1 - far / near if near else np.nan})
    return pd.DataFrame(rows).set_index("dt")


def spoof_rate_by_size(ann: pd.DataFrame, buckets=SIZE_BUCKETS, min_dist_ticks: float = 4) -> pd.DataFrame:
    """Spoof-like rate among far adds, by add size (min_size=1, so every size is labelled)."""
    from features.common import TICK
    from features.spoof import spoof_like_events

    kind = ann["kind"].to_numpy()
    side, price = ann["side"].astype(str).to_numpy(), ann["price"].to_numpy(float)
    bb, ba = ann["best_bid"].to_numpy(float), ann["best_ask"].to_numpy(float)
    new = ann["new_size"].to_numpy(np.int64)
    a = np.flatnonzero(kind == "add")
    dist = np.where(side[a] == "B", (bb[a] - price[a]) / TICK, (price[a] - ba[a]) / TICK)
    far = a[np.isfinite(dist) & (dist >= min_dist_ticks)]
    sizes = pd.Series(new[far], index=ann["order_id"].to_numpy(np.uint64)[far])
    sp = spoof_like_events(ann, min_size=1, min_dist_ticks=min_dist_ticks)
    flagged = set(sp["order_id"].astype(np.uint64))
    lab = pd.cut(sizes.to_numpy(), list(buckets), right=False)
    is_sp = np.array([o in flagged for o in sizes.index])
    out = pd.DataFrame({"bucket": lab, "spoof": is_sp}).groupby("bucket", observed=True)["spoof"].agg(["size", "sum", "mean"])
    out.columns = ["far_adds", "spoof_like", "rate"]
    return out


def main(argv=None) -> int:
    from data.loader import load_chunks, with_book_warmup
    from data.sessions import session_bounds
    from features.book import annotate_mbo
    from features.iceberg import synthetic_icebergs
    from scripts.verify_data import render, save
    from data.config import load_settings

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--date", required=True, type=date.fromisoformat)
    ap.add_argument("--rth-only", action="store_true")
    a = ap.parse_args(argv)
    root = load_settings().cache_dir / "GLBX.MDP3" / "mbo" / "ES.c.0"
    paths = sorted(root.glob("*.dbn.zst"))
    start, end = session_bounds(a.date, a.rth_only)
    paths = [p for p in paths if start.date() <= date.fromisoformat(p.name[:10]) <= end.date()]
    if a.rth_only:
        paths = [p for p in paths if p.name.startswith(a.date.isoformat())]
    raw = load_chunks(paths)[["action", "side", "price", "size", "order_id", "flags"]]
    ann = annotate_mbo(with_book_warmup(raw[raw.index < end], a.date, a.rth_only))
    del raw
    prec = pd.concat({f"clip>={m}": readd_precision(ann, dt_grid=("1ms", "5ms", "50ms") if m > 1 else DT_GRID,
                                                     min_clip=m) for m in (1, 2, 5, 15)})
    print(prec.to_string(), flush=True)
    chains = pd.DataFrame([{"dt": dt, "min_clips": m, "chains": len(synthetic_icebergs(ann, dt=dt, min_clips=m))}
                           for dt in ("1ms", "5ms") for m in (3, 5, 10)])
    print(chains.to_string(), flush=True)
    spoof = spoof_rate_by_size(ann)
    print(spoof.to_string(), flush=True)
    tag = "-rth" if a.rth_only else ""
    p = save(f"mbo-calibration-{a.date.isoformat()}{tag}.md",
             render(f"MBO detector calibration {a.date}{' (RTH)' if a.rth_only else ''}",
                    {"synthetic iceberg: same-size re-add share, near vs +1 s": prec,
                     "synthetic iceberg chains by dt and min_clips": chains,
                     "spoof-like rate among far adds (>= 4 ticks) by size": spoof}))
    print(f"saved {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
