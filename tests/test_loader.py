"""Round-trip a real (synthetic) DBN file through the cache/loader path."""
from datetime import date

import databento_dbn as dbn
import pandas as pd
import pytest

from data import cache
from data.loader import load_chunks, slice_session

NS = 1_000_000_000


def write_trades(path, trades):
    meta = dbn.Metadata(
        dataset="GLBX.MDP3", schema=dbn.Schema.TRADES, start=0, end=None,
        stype_in=dbn.SType.RAW_SYMBOL, stype_out=dbn.SType.INSTRUMENT_ID,
        symbols=[], partial=[], not_found=[], mappings=[],
    )
    buf = bytes(meta.encode())
    for ts_s, px, size, side, iid in trades:
        buf += bytes(dbn.TradeMsg(
            publisher_id=1, instrument_id=iid, ts_event=ts_s * NS, ts_recv=ts_s * NS + 1000,
            price=int(px * NS), size=size, action=dbn.Action.TRADE, side=side, depth=0,
        ))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(buf)


def test_load_cached_chunk_and_slice(tmp_path):
    t_rth = int(pd.Timestamp("2024-03-05 15:00", tz="UTC").timestamp())   # 09:00 CT
    t_eth = int(pd.Timestamp("2024-03-05 01:00", tz="UTC").timestamp())   # 19:00 CT Mon
    p = cache.chunk_path(tmp_path, "GLBX.MDP3", "trades", "ES.c.0", date(2024, 3, 5))
    write_trades(p, [(t_eth, 5100.25, 2, dbn.Side.BID, 42), (t_rth, 5101.50, 3, dbn.Side.ASK, 42)])

    df = load_chunks([p])
    assert list(df["price"]) == [5100.25, 5101.50]
    assert list(df["side"]) == ["B", "A"]
    assert cache.parquet_path(p).exists()

    # Second load is served from parquet and is identical.
    pd.testing.assert_frame_equal(load_chunks([p]), df)

    sess = slice_session(df, date(2024, 3, 5))
    assert list(sess["session"]) == ["ETH", "RTH"]
    assert list(slice_session(df, date(2024, 3, 5), rth_only=True)["price"]) == [5101.50]


def test_file_order_is_preserved(tmp_path):
    """Databento file order carries FIFO priority; the loader must never re-sort."""
    t0 = int(pd.Timestamp("2024-03-05 15:00", tz="UTC").timestamp())
    p1 = cache.chunk_path(tmp_path, "GLBX.MDP3", "trades", "ES.c.0", date(2024, 3, 4))
    p2 = cache.chunk_path(tmp_path, "GLBX.MDP3", "trades", "ES.c.0", date(2024, 3, 5))
    write_trades(p1, [(t0 - 86400, 5000.0, 1, dbn.Side.BID, 42)])
    # second record has an EARLIER timestamp (e.g. F_BAD_TS_RECV) -- must stay second
    write_trades(p2, [(t0 + 5, 5001.0, 1, dbn.Side.ASK, 42), (t0, 5002.0, 1, dbn.Side.ASK, 42)])
    df = load_chunks([p2, p1], use_parquet=False)   # passed out of order on purpose
    assert list(df["price"]) == [5000.0, 5001.0, 5002.0]


def test_refuses_to_mix_contracts(tmp_path):
    p1 = cache.chunk_path(tmp_path, "GLBX.MDP3", "trades", "ES.c.0", date(2024, 3, 6))
    p2 = cache.chunk_path(tmp_path, "GLBX.MDP3", "trades", "ES.c.1", date(2024, 3, 6))
    with pytest.raises(ValueError, match="several symbols"):
        load_chunks([p1, p2])
