import numpy as np
import pandas as pd
import pytest

from data.flags import F_BAD_TS_RECV, F_LAST, F_SNAPSHOT
from features.book import OrderBook, annotate_mbo, mbo_heatmap, mbp10_heatmap
from features.iceberg import native_icebergs, synthetic_icebergs
from features.spoof import spoof_like_events
from tests.causality import assert_causal
from tests.synth import T0

L = F_LAST
SNAP = F_SNAPSHOT | F_BAD_TS_RECV


def mbo_df(rows):
    """rows: (ms_after_T0, action, side, price, size, order_id, flags)."""
    idx = pd.DatetimeIndex([T0 + pd.Timedelta(milliseconds=r[0]) for r in rows], name="ts_recv")
    return pd.DataFrame({
        "action": [r[1] for r in rows], "side": [r[2] for r in rows],
        "price": [float(r[3]) for r in rows], "size": np.array([r[4] for r in rows], dtype="uint32"),
        "order_id": np.array([r[5] for r in rows], dtype="uint64"),
        "flags": np.array([r[6] for r in rows], dtype="uint8")}, index=idx)


def base_book(t=0):
    """bid 5000.00 (ids 1:5, 2:3), ask 5000.25 (id 3:4)."""
    return [(t, "A", "B", 5000.00, 5, 1, L), (t + 1, "A", "B", 5000.00, 3, 2, L),
            (t + 2, "A", "A", 5000.25, 4, 3, L)]


# ----------------------------------------------------------------------- OrderBook
def test_orderbook_fifo_and_priority_rules():
    b = OrderBook()
    for oid, sz in ((1, 5), (2, 3), (3, 2)):
        b.apply("A", "B", 100.0, sz, oid)
    assert b.queue_ahead(3) == 8 and b.best_bid() == 100.0
    b.apply("C", "B", 100.0, 2, 1)            # partial cancel keeps priority
    assert b.queue_ahead(2) == 3
    b.apply("M", "B", 100.0, 1, 2)            # size decrease keeps priority
    assert b.queue_ahead(3) == 4
    b.apply("M", "B", 100.0, 9, 1)            # size increase -> back of queue
    assert b.queue_ahead(1) == 3 and b.queue_ahead(2) == 0
    b.apply("M", "B", 99.75, 1, 2)            # price change -> new level
    assert b.depth("B") == [(100.0, 11, 2), (99.75, 1, 1)]
    b.apply("C", "B", 100.0, 9, 1)
    b.apply("C", "B", 100.0, 2, 3)
    assert b.best_bid() == 99.75
    b.apply("T", "A", 99.75, 1, 0)            # trades never change the book
    assert b.level_size("B", 99.75) == 1
    b.apply("R", "N", np.nan, 0, 0)
    assert b.orders == {} and np.isnan(b.best_bid())


# ----------------------------------------------------------------------- annotate_mbo
def test_fill_removal_vs_true_cancel():
    rows = base_book() + [
        (10, "T", "A", 5000.00, 2, 99, 0),     # seller aggressor
        (10, "F", "B", 5000.00, 2, 1, 0),      # resting order 1 filled 2
        (10, "C", "B", 5000.00, 2, 1, L),      # ...and its book update -> fill_removal (partial)
        (20, "C", "B", 5000.00, 3, 2, L),      # order 2 pulled with no fill -> true cancel
    ]
    ann = annotate_mbo(mbo_df(rows))
    assert ann["kind"].tolist() == ["add", "add", "add", "trade", "fill", "fill_removal", "cancel"]
    assert ann["prev_size"].iloc[5] == 5 and ann["new_size"].iloc[5] == 3
    assert ann["exceeds_display"].sum() == 0


def test_partial_fill_reflected_by_modify():
    rows = base_book() + [(10, "F", "B", 5000.00, 1, 1, 0), (10, "M", "B", 5000.00, 4, 1, L)]
    assert annotate_mbo(mbo_df(rows))["kind"].iloc[-1] == "modify_down_fill"


def test_snapshot_records_are_labelled_and_rebuild_book():
    rows = base_book() + [
        (50, "R", "N", np.nan, 0, 0, SNAP),
        (50, "A", "B", 5000.00, 5, 1, SNAP),
        (50, "A", "A", 5000.50, 7, 3, SNAP | L),
        (60, "C", "B", 5000.00, 5, 1, L),
    ]
    ann = annotate_mbo(mbo_df(rows))
    assert ann["kind"].iloc[3:6].tolist() == ["snapshot"] * 3
    assert ann["kind"].iloc[6] == "cancel"
    assert ann["best_ask"].iloc[6] == 5000.50          # rebuilt from snapshot (order 2 gone)


def test_best_bid_is_as_of_last_completed_event():
    rows = [(0, "A", "B", 5000.00, 1, 1, L),
            (5, "A", "B", 5000.25, 1, 2, 0),            # event not finished yet
            (5, "A", "A", 5000.50, 1, 3, L)]
    ann = annotate_mbo(mbo_df(rows))
    assert np.isnan(ann["best_bid"].iloc[0])
    assert ann["best_bid"].tolist()[1:] == [5000.00, 5000.00]


# ----------------------------------------------------------------------- heatmaps
def test_mbo_heatmap_state_as_of_bucket_end():
    rows = base_book() + [(1500, "A", "B", 4999.75, 9, 4, L), (2500, "C", "B", 5000.0, 5, 1, L)]
    hm = mbo_heatmap(mbo_df(rows), freq="1s")
    t1 = hm[hm["known_at"] == T0 + pd.Timedelta("1s")]
    assert t1[t1["side"] == "B"][["price", "size"]].values.tolist() == [[5000.0, 8]]
    t2 = hm[hm["known_at"] == T0 + pd.Timedelta("2s")]
    assert t2[t2["side"] == "B"][["price", "size"]].values.tolist() == [[5000.0, 8], [4999.75, 9]]
    assert hm["consistent"].all()


def test_mbo_heatmap_flags_mid_event_boundary():
    rows = [(0, "A", "B", 5000.0, 1, 1, L), (999, "A", "B", 5000.0, 1, 2, 0), (1001, "A", "A", 5001.0, 1, 3, L)]
    hm = mbo_heatmap(mbo_df(rows), freq="1s")
    assert hm["consistent"].tolist() == [False]


def test_mbp10_heatmap_forward_fills_and_uses_f_last():
    idx = pd.DatetimeIndex([T0, T0 + pd.Timedelta("100ms"), T0 + pd.Timedelta("2500ms")])
    df = pd.DataFrame({"flags": np.array([L, 0, L], dtype="uint8"),
                       "bid_px_00": [5000.0, 4990.0, 5000.25], "bid_sz_00": [10, 1, 12], "bid_ct_00": [2, 1, 3],
                       "ask_px_00": [5000.25, 5010.0, 5000.50], "ask_sz_00": [7, 1, 8], "ask_ct_00": [1, 1, 2]},
                      index=idx)
    hm = mbp10_heatmap(df, freq="1s")
    bids = hm[hm["side"] == "B"].set_index("known_at")["price"]
    assert bids.to_dict() == {T0 + pd.Timedelta("1s"): 5000.0, T0 + pd.Timedelta("2s"): 5000.0,
                              T0 + pd.Timedelta("3s"): 5000.25}


# ----------------------------------------------------------------------- icebergs
def test_native_iceberg_fill_exceeds_display():
    rows = base_book() + [(10, "T", "A", 5000.0, 12, 99, 0), (10, "F", "B", 5000.0, 12, 1, 0),
                          (10, "M", "B", 5000.0, 5, 1, L)]       # displayed 5, filled 12, still shows 5
    ann = annotate_mbo(mbo_df(rows))
    assert ann["kind"].iloc[-1] == "refill"
    ice = native_icebergs(ann)
    assert ice[["order_id", "evidence", "price"]].values.tolist() == [[1, "fill_exceeds_display", 5000.0]]
    assert ice["known_at"].iloc[0] == T0 + pd.Timedelta(milliseconds=10)


def test_native_iceberg_same_size_refill():
    rows = base_book() + [(10, "F", "B", 5000.0, 5, 1, 0), (10, "M", "B", 5000.0, 5, 1, L)]
    ann = annotate_mbo(mbo_df(rows))
    assert ann["kind"].iloc[-1] == "refill"             # 5 - 5 filled = 0 expected, shows 5 -> refilled
    assert native_icebergs(ann)["evidence"].tolist() == ["refill_after_fill"]


def test_no_native_iceberg_for_ordinary_fill():
    rows = base_book() + [(10, "F", "B", 5000.0, 2, 1, 0), (10, "C", "B", 5000.0, 2, 1, L)]
    assert native_icebergs(annotate_mbo(mbo_df(rows))).empty


def synthetic_chain(gap_ms=2, sizes=(3, 3, 3)):
    rows, t, oid = [], 0, 20
    for k, s in enumerate(sizes):
        rows.append((t, "A", "A", 5001.0, s, oid, L))
        rows += [(t + 10, "F", "A", 5001.0, s, oid, 0), (t + 10, "C", "A", 5001.0, s, oid, L)]
        t, oid = t + 10 + gap_ms, oid + 1
    return rows


def test_synthetic_iceberg_chain():
    ice = synthetic_icebergs(annotate_mbo(mbo_df(synthetic_chain())), dt="5ms", min_clips=3)
    assert ice[["side", "price", "clip_size", "clips"]].values.tolist() == [["A", 5001.0, 3, 3]]
    assert ice["order_ids"].iloc[0] == [20, 21, 22]


@pytest.mark.parametrize("kw", [{"gap_ms": 50}, {"sizes": (3, 4, 3)}], ids=["too_slow", "size_change"])
def test_synthetic_iceberg_negative(kw):
    assert synthetic_icebergs(annotate_mbo(mbo_df(synthetic_chain(**kw))), dt="5ms", min_clips=3).empty


# ----------------------------------------------------------------------- spoof-like
def spoof_rows(extra):
    return base_book() + [(100, "A", "B", 4998.00, 100, 30, L)] + extra   # 8 ticks under best bid


def test_spoof_like_event():
    ev = spoof_like_events(annotate_mbo(mbo_df(spoof_rows([(2100, "C", "B", 4998.0, 100, 30, L)]))))
    assert len(ev) == 1
    r = ev.iloc[0]
    assert (r["order_id"], r["size"], r["dist_at_add_ticks"], r["min_dist_ticks"]) == (30, 100, 8.0, 8.0)
    assert r["known_at"] == T0 + pd.Timedelta(milliseconds=2100) and r["lifetime_s"] == 2.0


@pytest.mark.parametrize("extra", [
    [(200, "F", "B", 4998.0, 10, 30, 0), (200, "C", "B", 4998.0, 10, 30, L), (300, "C", "B", 4998.0, 90, 30, L)],
    [(20000, "C", "B", 4998.0, 100, 30, L)],                                      # lived too long
    [(500, "A", "B", 4998.25, 1, 40, L), (510, "C", "B", 5000.0, 5, 1, L),        # bid collapses toward it
     (520, "C", "B", 5000.0, 3, 2, L), (900, "C", "B", 4998.0, 100, 30, L)],
], ids=["traded", "too_old", "price_came_near"])
def test_spoof_like_negatives(extra):
    assert spoof_like_events(annotate_mbo(mbo_df(spoof_rows(extra)))).empty


def test_spoof_ignores_small_and_snapshot_orders():
    rows = base_book() + [(100, "A", "B", 4998.0, 5, 31, L), (100, "A", "B", 4997.0, 500, 32, SNAP | L),
                          (900, "C", "B", 4998.0, 5, 31, L), (950, "C", "B", 4997.0, 500, 32, L)]
    assert spoof_like_events(annotate_mbo(mbo_df(rows))).empty


# ----------------------------------------------------------------------- random stream: invariants + causality
def random_mbo(n_events=3000, seed=3):
    rng = np.random.default_rng(seed)
    rows, live, oid, t = [], {}, 1000, 0
    iceberg: dict[int, int] = {}                      # oid -> clip size (native icebergs refill)
    for _ in range(n_events):
        t += int(rng.exponential(50))
        u = rng.random()
        if u < 0.45 or len(live) < 10:
            side = "B" if rng.random() < 0.5 else "A"
            p = 5000.0 - 0.25 * rng.integers(0, 12) if side == "B" else 5000.25 + 0.25 * rng.integers(0, 12)
            size = int(rng.choice([1, 2, 5, 10, 80, 150], p=[.3, .25, .2, .15, .05, .05]))
            oid += 1
            live[oid] = [side, p, size]
            if rng.random() < 0.1:
                iceberg[oid] = size
            rows.append((t, "A", side, p, size, oid, L))
        elif u < 0.75:
            o = int(rng.choice(list(live)))
            side, p, size = live.pop(o)
            rows.append((t, "C", side, p, size, o, L))
        else:                                         # trade against a resting order
            o = int(rng.choice(list(live)))
            side, p, size = live[o]
            q = int(rng.integers(1, size + 1))
            rows += [(t, "T", "A" if side == "B" else "B", p, q, 0, 0), (t, "F", side, p, q, o, 0)]
            if q == size and o in iceberg:            # clip exhausted -> exchange refills same id
                live[o][2] = iceberg[o]
                rows.append((t, "M", side, p, iceberg[o], o, L))
            elif q == size:
                live.pop(o)
                rows.append((t, "C", side, p, q, o, L))
            else:
                live[o][2] = size - q
                rows.append((t, "M", side, p, size - q, o, L))
    return mbo_df(rows)


def test_annotate_is_prefix_stable_and_reconciles_fills():
    df = random_mbo()
    full = annotate_mbo(df)
    part = annotate_mbo(df.iloc[: len(df) // 2])
    cols = ["kind", "prev_size", "new_size", "best_bid", "best_ask", "event_id"]
    pd.testing.assert_frame_equal(full[cols].iloc[: len(part)], part[cols])
    fills = full.loc[full["kind"] == "fill", "size"].astype(int).sum()
    # every resting-order fill is explained by a removal, a reduction, or an iceberg refill
    assert fills == full["fill_explained"].sum() + full.attrs["unexplained_fill_open"]
    assert full.attrs["unexplained_fill_open"] == 0
    assert (full["kind"] == "refill").sum() > 0
    assert (full["kind"] == "unknown_order").sum() == 0 and full.attrs["book_anomalies"] == 0


@pytest.mark.parametrize("feature", [
    lambda d: mbo_heatmap(d, "1s"),
    lambda d: native_icebergs(annotate_mbo(d)),
    lambda d: synthetic_icebergs(annotate_mbo(d), dt="60ms", min_clips=2).drop(columns="order_ids"),
    lambda d: spoof_like_events(annotate_mbo(d), min_size=80, min_dist_ticks=2, near_ticks=1, max_lifetime="60s"),
], ids=["mbo_heatmap", "native_ice", "synthetic_ice", "spoof"])
def test_mbo_features_no_lookahead(feature):
    df = random_mbo()
    assert len(feature(df)) > 0, "fixture should produce some output for a meaningful check"
    assert_causal(feature, df)
