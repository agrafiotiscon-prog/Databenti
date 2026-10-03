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


def test_overnight_and_reversal_strategies():
    import strategies.h009 as H9
    import strategies.h010 as H10
    d0, d1 = date(2025, 2, 6), date(2025, 2, 7)          # Thu -> Fri
    d2 = date(2025, 2, 10)                                 # Mon
    P = {"ES.c.0": table([(d0, {"p0900": 6000.0, "p1500": 6010.0}),
                          (d1, {"p0800": 6015.0, "p0900": 6016.0, "p1000": 6012.0, "p1500": 6005.0}),
                          (d2, {"p0800": 6001.0, "p0900": 6002.0, "p1000": 6003.0, "p1500": 6008.0})]),
         "ES.c.1": table([])}
    days = [d0, d1, d2]
    t = H9.trades(P, days, {"exit_at": "08:00", "skip_weekends": False}, 0.0, 0.0, 50.0)
    assert list(t["gross_pnl"]) == [(6015 - 6010) * 50, (6001 - 6005) * 50]
    t2 = H9.trades(P, days, {"exit_at": "08:00", "skip_weekends": True}, 0.0, 0.0, 50.0)
    assert len(t2) == 1                                     # Fri -> Mon skipped
    r = H10.trades(P, days, {"min_abs_bp": 0, "entry_at": "10:00"}, 0.0, 0.0, 50.0)
    assert r.iloc[0]["side"] == -1 and r.iloc[0]["gross_pnl"] == -(6005 - 6012) * 50   # Thu up -> short Fri


def test_h011_vwap_signal_is_causal():
    import strategies.h011 as H11
    from data.sessions import CT
    d = date(2025, 2, 4)
    base = pd.Timestamp(d.isoformat(), tz=CT) + pd.Timedelta(hours=8, minutes=30)
    idx = [base + pd.Timedelta(seconds=10 * k) for k in range(600)]
    price = [6000.0 + (0.25 if k % 2 else 0.0) for k in range(600)]
    price[-1] = 6010.0                                     # last print spikes far above VWAP
    tr = pd.DataFrame({"price": price, "side": "B", "size": 1}, index=pd.DatetimeIndex(idx).tz_convert("UTC"))
    ev = H11.prepare_day(tr, d, {})
    assert ev["z"].iloc[:-1].abs().max() < 2                 # nothing extreme before the spike
    assert ev["z"].iloc[-1] > 3 and ev["known_at"].iloc[-1] > pd.Timestamp(idx[-1]).value


def test_fomc_cycle_weeks_and_holding_periods(monkeypatch):
    import strategies.h012 as H12
    days = [d.date() for d in pd.bdate_range("2025-01-02", "2025-02-28")]
    monkeypatch.setattr(H12, "fomc_dates", lambda: [date(2025, 1, 29)])
    wk = H12.cycle_weeks(days)
    assert wk[date(2025, 1, 28)] == 0                                  # day -1 before the statement
    assert wk[date(2025, 1, 27)] is None                               # before any statement in the data
    assert wk[date(2025, 1, 29)] == 0                                  # statement day
    k = {d: i for i, d in enumerate(days)}
    i0 = k[date(2025, 1, 29)]
    assert wk[days[i0 + 3]] == 0 and wk[days[i0 + 4]] == 1 and wk[days[i0 + 9]] == 2
    P = {"ES.c.0": table([(d, {"p1500": 6000.0 + i}) for i, d in enumerate(days)]), "ES.c.1": table([])}
    t = H12.trades(P, days, {"weeks": "w0_w2"}, 0.0, 0.0, 50.0)
    assert (t["gross_pnl"] > 0).all() and len(t) >= 2                 # week 0 and week 2 blocks, one trade each


def test_intraday_periodicity_uses_previous_days_only():
    import strategies.h013 as H13
    days = [d.date() for d in pd.bdate_range("2025-01-02", periods=15)]
    rows = []
    for i, d in enumerate(days):
        up = 1.0 if i < 14 else -50.0                      # last day: big DOWN move in hour 09:00-10:00
        rows.append((d, {"p0900": 6000.0, "p1000": 6000.0 + up}))
    P = {"ES.c.0": table(rows), "ES.c.1": table([])}
    t = H13.trades(P, days, {"lookback": 10, "min_abs_bp": 0}, 0.0, 0.0, 50.0)
    last = t[t["trading_date"] == days[-1]]
    assert len(last) == 1 and last.iloc[0]["side"] == 1 and last.iloc[0]["gross_pnl"] < 0   # signal from earlier days


def test_tsmom_signal_is_lagged_and_rolls_are_charged(monkeypatch):
    import strategies.h014 as H14
    days = [d.date() for d in pd.bdate_range("2025-01-02", periods=8)]
    prices = [100, 101, 102, 103, 102, 101, 100, 99]
    P = {"ES.c.0": table([(d, {"p0900": float(p), "p1500": float(p)}) for d, p in zip(days, prices)]),
         "ES.c.1": table([(d, {"p0900": float(p) + 10, "p1500": float(p) + 10}) for d, p in zip(days, prices)])}
    monkeypatch.setattr(H14, "sym_of", lambda d: "ES.c.0")
    s = H14.signals(P, days, 2)
    assert s[:2] == [0, 0] and s[2] == 1 and s[5] == -1             # uses closes up to that day only
    t = H14.segments(P, days, s, 0.0, 0.0, 1.0)
    assert list(t["side"]) == [1, -1] and t.iloc[0]["gross_pnl"] == 101 - 103   # long at day 3 open, flat signal on day 4 -> exit day 5 open
    monkeypatch.setattr(H14, "sym_of", lambda d: "ES.c.1" if d >= days[5] else "ES.c.0")
    t2 = H14.segments(P, days, [1] * 8, 0.0, 0.0, 1.0)
    assert len(t2) == 2                                             # roll splits the position (extra round trip)


def test_macro_days_and_placebo(monkeypatch):
    import strategies.h015 as H15
    days = [d.date() for d in pd.bdate_range("2025-01-02", periods=40)]
    ev = {days[5], days[15], days[25]}
    monkeypatch.setattr(H15, "macro_dates", lambda kind: ev)
    monkeypatch.setattr(H15, "fomc_dates", lambda: [])
    # event days rise 10 points, other days are flat -> placebo p must be ~0
    rows = []
    for i, d in enumerate(days):
        base = 6000.0 + 10 * sum(1 for e in ev if e <= d)
        rows.append((d, {"p0800": base - (10 if d in ev else 0), "p1500": base}))
    P = {"ES.c.0": table(rows), "ES.c.1": table([])}
    monkeypatch.setattr(H15, "sym_of", lambda d: "ES.c.0")
    t = H15.trades(P, days, {"events": "both", "window": "c2c"}, 0.0, 0.0, 50.0)
    assert len(t) == 3 and (t["gross_pnl"] == 500.0).all()
    assert H15.placebo(P, days, {"events": "both", "window": "c2c"}, 0.0, 0.0, 50.0, days, n_draws=500) == 0.0


def test_pre_holiday_detection_and_placebo(monkeypatch):
    import strategies.h016 as H16
    monkeypatch.setattr(H16, "sym_of", lambda d: "ES.c.0")
    allb = [d.date() for d in pd.bdate_range("2025-01-02", periods=60)]
    hol = {allb[10], allb[30], allb[50]}                     # weekdays with no bars
    days = [d for d in allb if d not in hol]
    pre = {allb[9], allb[29], allb[49]}
    rows, lvl = [], 6000.0
    for d in days:
        if d in pre:
            rows.append((d, {"p0900": lvl, "p1500": lvl + 8}))
            lvl += 8
        else:
            rows.append((d, {"p0900": lvl, "p1500": lvl}))
    P = {"ES.c.0": table(rows), "ES.c.1": table([])}
    assert H16.holidays(P) == hol and H16.pre_holidays(P, days) == pre
    t = H16.trades(P, days, {"window": "rth"}, 0.0, 0.0, 50.0)
    assert len(t) == 3 and (t["gross_pnl"] == 400.0).all() and (t["side"] == 1).all()
    assert len(H16.trades(P, days, {"window": "c2c"}, 0.0, 0.0, 50.0)) == 3
    assert H16.placebo(P, days, {"window": "rth"}, 0.0, 0.0, 50.0, days, n_draws=500) == 0.0


def test_opex_week_windows_and_placebo(monkeypatch):
    import strategies.h017 as H17
    monkeypatch.setattr(H17, "sym_of", lambda d: "ES.c.0")
    days = [d.date() for d in pd.bdate_range("2025-01-02", "2025-06-30")]
    w = H17.windows(days, "all")
    assert w[0] == (date(2025, 1, 10), date(2025, 1, 16))   # OPEX 2025-01-17
    assert all(e.weekday() == 4 and x.weekday() == 3 and (x - e).days == 6 for e, x in w)
    assert [e.month for e, _ in H17.windows(days, "quarterly")] == [3, 6]
    # price rises only inside OPEX weeks -> every hold +X, placebo p ~ 0
    inside = {d for e, x in w for d in days if e < d <= x}
    lvl, rows = 6000.0, []
    for d in days:
        lvl += 5 if d in inside else 0
        rows.append((d, {"p1500": lvl}))
    P = {"ES.c.0": table(rows), "ES.c.1": table([])}
    t = H17.trades(P, days, {"months": "all"}, 0.0, 0.0, 50.0)
    assert len(t) == len(w) and (t["gross_pnl"] == 4 * 5 * 50).all()
    assert H17.placebo(P, days, {"months": "all"}, 0.0, 0.0, 50.0, days, n_draws=500) == 0.0


def test_monday_reversal_only_after_friday(monkeypatch):
    import strategies.h018 as H18
    monkeypatch.setattr(H18, "sym_of", lambda d: "ES.c.0")
    fri, mon, tue = date(2025, 2, 7), date(2025, 2, 10), date(2025, 2, 11)
    P = {"ES.c.0": table([(fri, {"p0900": 6000.0, "p1500": 6060.0}), (mon, {"p0900": 6050.0, "p1500": 6030.0}),
                          (tue, {"p0900": 6030.0, "p1500": 6000.0})]), "ES.c.1": table([])}
    t = H18.trades(P, [fri, mon, tue], {"min_abs_bp": 50}, 1.0, 4.51, 50.0)
    assert len(t) == 1 and t.iloc[0]["trading_date"] == mon and t.iloc[0]["side"] == -1   # +100 bp Friday -> short
    assert t.iloc[0]["gross_pnl"] == ((6050.0 - 0.25) - (6030.0 + 0.25)) * 50
    assert H18.trades(P, [fri, mon, tue], {"min_abs_bp": 150}, 1.0, 4.51, 50.0).empty
    gap = {"ES.c.0": table([(date(2025, 2, 6), {"p0900": 6000.0, "p1500": 6060.0}),
                            (mon, {"p0900": 6050.0, "p1500": 6030.0})]), "ES.c.1": table([])}
    assert H18.trades(gap, [date(2025, 2, 6), mon], {"min_abs_bp": 0}, 0.0, 0.0, 50.0).empty   # no Friday session


def test_month_end_fade_windows_signal_and_placebo(monkeypatch):
    import strategies.h019 as H19
    monkeypatch.setattr(H19, "sym_of", lambda d: "ES.c.0")
    days = [d.date() for d in pd.bdate_range("2025-01-02", "2025-06-30")]
    w = H19.month_windows(days)
    m0, ie, ix = w[0]
    assert days[m0] == date(2025, 1, 31) and days[ix] == date(2025, 2, 28) and ix - ie == 4
    bad = H19.turn_days(days)
    assert days.index(date(2025, 2, 28)) in bad and days.index(date(2025, 3, 3)) in bad
    assert days.index(date(2025, 3, 4)) in bad and days.index(date(2025, 3, 5)) not in bad
    # price drifts up during each month, then falls in its last 4 days -> fade (short) wins at every month-end
    lvl, rows = 6000.0, []
    ends = {days[i] for _, ie, ix in w for i in range(ie + 1, ix + 1)}
    for d in days:
        lvl += -10 if d in ends else 2
        rows.append((d, {"p1500": lvl}))
    P = {"ES.c.0": table(rows), "ES.c.1": table(rows)}
    t = H19.trades(P, days, {"min_abs_bp": 0}, 0.0, 0.0, 50.0)
    assert len(t) == len(w) and (t["side"] == -1).all() and (t["gross_pnl"] == 40 * 50).all()
    assert H19.trades(P, days, {"min_abs_bp": 1000}, 0.0, 0.0, 50.0).empty
    assert H19.placebo(P, days, {"min_abs_bp": 0}, 0.0, 0.0, 50.0, days, n_draws=500) == 0.0


def test_same_contract_px_follows_the_contract_across_databento_rank_shift(monkeypatch):
    import strategies.bars_common as B
    monkeypatch.setattr(B, "sym_of", lambda d: "ES.c.0")
    feb, mar = date(2025, 2, 28), date(2025, 3, 25)               # 2025-03-21 expiry in between
    P = {"ES.c.0": table([(feb, {"p1500": 6000.0}), (mar, {"p1500": 6100.0})]),
         "ES.c.1": table([(feb, {"p1500": 6050.0}), (mar, {"p1500": 6150.0})])}
    assert B.same_contract_px(P, mar, feb, "p1500") == 6050.0        # June contract was rank 1 in Feb
    assert B.same_contract_px(P, feb, mar, "p1500") is None          # March contract has expired by then
    assert B.same_contract_px(P, mar, mar, "p1500") == 6100.0
