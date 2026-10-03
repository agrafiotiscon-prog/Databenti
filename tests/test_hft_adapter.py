import numpy as np
import pandas as pd
import pytest

hb = pytest.importorskip("hftbacktest")

from backtest.hft_adapter import to_hft_events
from data.flags import F_BAD_TS_RECV, F_LAST, F_SNAPSHOT

T0 = pd.Timestamp("2024-03-05 00:00:00", tz="UTC")
SNAP = F_SNAPSHOT | F_BAD_TS_RECV


def frame(rows):
    """rows: (recv_ms, event_ms, action, side, price, size, oid, flags)."""
    idx = pd.DatetimeIndex([T0 + pd.Timedelta(milliseconds=r[0]) for r in rows], name="ts_recv")
    return pd.DataFrame({"ts_event": [T0 + pd.Timedelta(milliseconds=r[1]) for r in rows],
                         "action": [r[2] for r in rows], "side": [r[3] for r in rows],
                         "price": [r[4] for r in rows], "size": np.array([r[5] for r in rows], dtype="uint32"),
                         "order_id": np.array([r[6] for r in rows], dtype="uint64"),
                         "flags": np.array([r[7] for r in rows], dtype="uint8")}, index=idx)


def test_snapshot_timestamps_none_records_and_event_codes():
    rows = [(0, 0, "R", "N", np.nan, 0, 0, SNAP),
            (0, -3_600_000, "A", "B", 5000.0, 5, 1, SNAP),        # snapshot order with an old ts_event
            (0, -1_000, "A", "A", 5000.25, 4, 2, SNAP | F_LAST),
            (10, 9, "N", "N", np.nan, 0, 0, F_LAST),               # carries nothing -> dropped
            (20, 19, "T", "A", 5000.0, 1, 0, 0),
            (20, 19, "F", "B", 5000.0, 1, 1, 0),
            (20, 19, "C", "B", 5000.0, 1, 1, F_LAST)]
    ev = to_hft_events(frame(rows))
    assert len(ev) == 6                                 # the N record is dropped
    base = ev["ev"] & 0xFF
    assert hb.DEPTH_CLEAR_EVENT in set(base) and hb.ADD_ORDER_EVENT in set(base)
    adds = ev[(base == hb.ADD_ORDER_EVENT)]
    assert (adds["exch_ts"] >= T0.value).all()          # snapshot orders no longer carry past timestamps
    bids = ev[(base == hb.ADD_ORDER_EVENT) & ((ev["ev"] & hb.BUY_EVENT) != 0)]
    assert set(bids["order_id"]) == {1}


def test_unknown_action_raises():
    with pytest.raises(ValueError):
        to_hft_events(frame([(0, 0, "X", "B", 1.0, 1, 1, F_LAST)]))
