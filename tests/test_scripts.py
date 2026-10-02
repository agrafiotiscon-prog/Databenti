from datetime import date

import pandas as pd

from scripts import plot_day, verify_data
from tests.synth import random_trades
from tests.test_features_mbo import random_mbo


def test_plot_day_builds_figure(tmp_path):
    fig = plot_day.build_figure(random_trades(), absorption_kw={"min_vol": 60, "window": "20s"},
                                mbo=random_mbo(800))
    names = {t.name for t in fig.data}
    assert {"price", "VWAP", "dev. POC", "cum. delta"} <= names
    fig.write_html(tmp_path / "x.html")
    assert (tmp_path / "x.html").stat().st_size > 10_000


def test_verify_summaries_and_report():
    tr = verify_data.summarize_trades(random_trades())
    assert 0 < tr["n_side_volume_share"] < 0.2 and tr["trades"] == 4000
    mb = verify_data.summarize_mbo(random_mbo())
    assert mb["fill_reconciliation_ratio"] == 1.0 and mb["book_anomalies"] == 0
    status = pd.DataFrame({"is_trading": ["Y", "Y", "N", "Y"]},
                          index=pd.DatetimeIndex(["2024-12-23 23:00", "2024-12-24 01:00",
                                                  "2024-12-24 18:15", "2024-12-25 23:00"], tz="UTC"))
    st = verify_data.summarize_status(status)
    assert st["is_trading"].tolist() == ["Y", "N", "Y"]
    assert str(st["ts_ct"].iloc[1].time()) == "12:15:00"       # Christmas Eve early close (CT)
    text = verify_data.render("t", {"trades": tr, "mbo": mb, "status": st})
    assert text.startswith("---\ntype: result") and "fill_reconciliation_ratio" in text


def test_roll_summary_compares_with_rule():
    days = verify_data.roll_window_days("2024-03")
    assert days[0] == date(2024, 2, 29) and days[-1] == date(2024, 3, 15)
    rows = [{"date": d, "c0_sided_volume": 100 if d < date(2024, 3, 11) else 10,
             "c1_sided_volume": 10 if d < date(2024, 3, 11) else 100} for d in days]
    rep = verify_data.summarize_roll(rows)
    assert rep["agrees"].all()


def test_roll_history_finds_crossover_and_scores_rules():
    from scripts.roll_history import roll_table, summarize
    exp = date(2024, 3, 15)
    days = [d.date() for d in pd.bdate_range("2024-02-29", "2024-03-15")]
    c1_from = date(2024, 3, 11)                                    # Monday of expiry week
    v0 = pd.Series([100 if d < c1_from else 10 for d in days], index=days)
    v1 = pd.Series([10 if d < c1_from else 100 for d in days], index=days)
    v1[date(2024, 3, 1)] = 200                                     # an early blip is not the crossover
    t = roll_table(v0, v1, [exp])
    assert t.loc[0, "crossover"] == c1_from and t.loc[0, "weekday"] == "Mon"
    # the 03-01 blip is one wrong day for every calendar rule
    assert t.loc[0, "wrong_cal4"] == 1
    assert t.loc[0, "wrong_cal8"] == 3                             # blip + Thu + Fri too early
    assert t.loc[0, "wrong_prevday_volume"] == 3                   # blip, day after blip, crossover day
    assert summarize(t).index[0] == "wrong_cal4"


def test_roll_history_folds_weekend_bars_into_monday():
    from scripts.roll_history import to_trading_dates
    idx = pd.DatetimeIndex(["2024-03-08", "2024-03-10", "2024-03-11"], tz="UTC")   # Fri, Sun, Mon
    out = to_trading_dates(pd.Series([5, 1, 7], index=idx))
    assert out.to_dict() == {date(2024, 3, 8): 5, date(2024, 3, 11): 8}
