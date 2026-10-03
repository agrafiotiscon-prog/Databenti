from datetime import date

import pandas as pd

import strategies.h005 as H5
import strategies.h006 as H6
import strategies.h007 as H7


def table(rows):
    """rows: (date, {col: price})."""
    t = pd.DataFrame({d: v for d, v in rows}).T
    t.index = pd.Index(list(t.index))
    return t


def test_turn_of_month_uses_entry_contract_and_trading_days():
    days = [date(2025, 1, 29), date(2025, 1, 30), date(2025, 1, 31), date(2025, 2, 3), date(2025, 2, 4), date(2025, 2, 5)]
    P = {"ES.c.0": table([(d, {"p1500": 6000.0 + i}) for i, d in enumerate(days)]), "ES.c.1": table([])}
    t = H5.trades(P, days, {"entry_k": 2, "exit_day": 3}, 0.0, 0.0, 50.0)
    assert len(t) == 1 and t.iloc[0]["trading_date"] == date(2025, 2, 5)
    assert t.iloc[0]["gross_pnl"] == (6005.0 - 6001.0) * 50                 # entry Jan 30, exit Feb 5


def test_gap_fade_direction_threshold_and_costs():
    d0, d1 = date(2025, 2, 3), date(2025, 2, 4)
    P = {"ES.c.0": table([(d0, {"p1500": 6000.0}), (d1, {"p0900": 6030.0, "p1000": 6020.0, "p1100": 6010.0})]),
         "ES.c.1": table([])}
    t = H6.trades(P, [d0, d1], {"min_gap_bp": 25, "exit_at": "11:00"}, 1.0, 4.51, 50.0)
    assert len(t) == 1 and t.iloc[0]["side"] == -1                          # +50 bp gap -> short
    assert t.iloc[0]["gross_pnl"] == ((6030.0 - 0.25) - (6010.0 + 0.25)) * 50
    assert H6.trades(P, [d0, d1], {"min_gap_bp": 60, "exit_at": "11:00"}, 1.0, 4.51, 50.0).empty


def test_fomc_dates_are_scheduled_and_well_formed():
    ds = H7.fomc_dates()
    assert len(ds) >= 120 and all(d.weekday() < 5 for d in ds)              # announcements on weekdays
    assert date(2025, 9, 17) in ds and date(2020, 3, 15) not in ds and date(2020, 3, 31) not in ds


def test_h008_z_uses_only_previous_buckets():
    import numpy as np
    import strategies.h008 as H8
    from data.sessions import CT
    d = date(2025, 2, 4)
    base = pd.Timestamp(d.isoformat(), tz=CT) + pd.Timedelta(hours=8, minutes=30)
    idx, side = [], []
    for k in range(30):                                   # 30 five-minute buckets
        n = 50 if k == 25 else 2 + k % 3                  # bucket 25: one-sided buying burst
        for j in range(n):
            idx.append(base + pd.Timedelta(minutes=5 * k, seconds=j))
            side.append("B" if (k == 25 or j % 2 == 0) else "A")
    tr = pd.DataFrame({"price": 6000.0, "side": side, "size": 1}, index=pd.DatetimeIndex(idx).tz_convert("UTC"))
    ev = H8.prepare_day(tr, d, {})
    hot = ev[ev["z"].abs() >= 3]
    assert len(hot) == 1
    assert hot.iloc[0]["known_at"] == (base + pd.Timedelta(minutes=5 * 26)).value   # known at bucket END
    assert np.isfinite(ev["z"]).all()


def test_h008_flat_history_gives_no_signal():
    import strategies.h008 as H8
    from data.sessions import CT
    d = date(2025, 2, 4)
    base = pd.Timestamp(d.isoformat(), tz=CT) + pd.Timedelta(hours=8, minutes=30)
    idx = [base + pd.Timedelta(minutes=5 * k, seconds=j) for k in range(25) for j in range(2)]
    side = ["B", "A"] * 25
    idx.append(base + pd.Timedelta(minutes=5 * 25)); side.append("B")
    tr = pd.DataFrame({"price": 6000.0, "side": side, "size": 1}, index=pd.DatetimeIndex(idx).tz_convert("UTC"))
    assert H8.prepare_day(tr, d, {}).empty                   # std 0 before the last bucket -> z undefined
