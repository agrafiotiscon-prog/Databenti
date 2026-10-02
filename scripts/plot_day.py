"""Visual check of features against price for one session (Plotly HTML).

  python scripts/plot_day.py --date 2024-03-05 [--rth-only] [--freq 1min] [--mbo]

Every marker is drawn at its `known_at` time, so lookahead is visible by eye
(a marker that "predicts" a move before its inputs existed would stand out).
Output: reports/day-<date>.html (gitignored).
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data.sessions import CT                                         # noqa: E402
from features.absorption import absorption_events                    # noqa: E402
from features.common import ohlcv_bars                               # noqa: E402
from features.footprint import bar_delta, delta_divergence, footprint  # noqa: E402
from features.imbalance import diagonal_imbalances, stacked_imbalances  # noqa: E402
from features.profile import developing_profile, vwap_bars           # noqa: E402


def _ct(x):
    return pd.DatetimeIndex(x).tz_convert(CT)


def build_figure(trades: pd.DataFrame, freq: str = "1min", mbo: pd.DataFrame | None = None,
                 absorption_kw: dict | None = None) -> go.Figure:
    bars = ohlcv_bars(trades, freq)
    fp = footprint(trades, freq)
    bd = bar_delta(fp)
    vw = vwap_bars(trades, freq)
    prof = developing_profile(trades, freq)
    div = delta_divergence(bars.join(bd[["cum_delta"]]), 10)
    stacks = stacked_imbalances(diagonal_imbalances(fp))
    absorb = absorption_events(trades, **(absorption_kw or {}))

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.75, 0.25], vertical_spacing=0.03)
    # candles are labelled by bar START; everything else at known_at (bar end / event time)
    fig.add_trace(go.Candlestick(x=_ct(bars.index), open=bars["open"], high=bars["high"], low=bars["low"],
                                 close=bars["close"], name="price"), row=1, col=1)
    k = _ct(vw["known_at"])
    fig.add_trace(go.Scatter(x=k, y=vw["vwap"], name="VWAP", line=dict(width=2)), row=1, col=1)
    for band in ("upper_1", "lower_1", "upper_2", "lower_2"):
        fig.add_trace(go.Scatter(x=k, y=vw[band], name=band, line=dict(width=1, dash="dot"),
                                 opacity=0.6), row=1, col=1)
    kp = _ct(prof["known_at"])
    fig.add_trace(go.Scatter(x=kp, y=prof["poc"], name="dev. POC", mode="lines", line=dict(dash="dash")), row=1, col=1)
    fig.add_trace(go.Scatter(x=kp, y=prof["vah"], name="dev. VAH", mode="lines", line=dict(width=1)), row=1, col=1)
    fig.add_trace(go.Scatter(x=kp, y=prof["val"], name="dev. VAL", mode="lines", line=dict(width=1)), row=1, col=1)
    for side, sym in (("buy", "triangle-up"), ("sell", "triangle-down")):
        z = stacks[stacks["side"] == side]
        if len(z):
            fig.add_trace(go.Scatter(x=_ct(z["known_at"]), y=(z["low"] + z["high"]) / 2, mode="markers",
                                     marker=dict(symbol=sym, size=9), name=f"stacked {side} imb."), row=1, col=1)
    for kind, sym in (("sell_absorbed", "circle"), ("buy_absorbed", "circle-open")):
        e = absorb[absorb["side"] == kind]
        if len(e):
            fig.add_trace(go.Scatter(x=_ct(e["known_at"]), y=e["level"], mode="markers",
                                     marker=dict(symbol=sym, size=11), name=kind), row=1, col=1)
    for col, sym in (("bearish_div", "x"), ("bullish_div", "cross")):
        d = div[div[col]]
        if len(d):
            fig.add_trace(go.Scatter(x=_ct(d["known_at"]), y=bars.loc[d.index, "close"], mode="markers",
                                     marker=dict(symbol=sym, size=9), name=col), row=1, col=1)
    if mbo is not None:
        from features.book import annotate_mbo
        from features.iceberg import native_icebergs
        from features.spoof import spoof_like_events
        ann = annotate_mbo(mbo)
        for name, ev in (("native iceberg", native_icebergs(ann)), ("spoof-like", spoof_like_events(ann))):
            if len(ev):
                fig.add_trace(go.Scatter(x=_ct(ev["known_at"]), y=ev["price"], mode="markers",
                                         marker=dict(symbol="diamond", size=8), name=name), row=1, col=1)
    fig.add_trace(go.Scatter(x=_ct(bd["known_at"]), y=bd["cum_delta"], name="cum. delta"), row=2, col=1)
    fig.update_layout(title="Order-flow features (markers at known_at, US/Central)",
                      xaxis_rangeslider_visible=False, height=900, template="plotly_white")
    return fig


def main(argv=None) -> int:
    from data.download import Downloader
    from data.loader import load_session

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--date", required=True, type=date.fromisoformat)
    ap.add_argument("--freq", default="1min")
    ap.add_argument("--rth-only", action="store_true")
    ap.add_argument("--mbo", action="store_true", help="also load MBO (costly) for iceberg/spoof markers")
    a = ap.parse_args(argv)
    dl = Downloader()
    trades = load_session(dl, "trades", a.date, rth_only=a.rth_only)
    mbo = load_session(dl, "mbo", a.date, rth_only=a.rth_only) if a.mbo else None
    out = Path("reports") / f"day-{a.date.isoformat()}.html"
    out.parent.mkdir(exist_ok=True)
    build_figure(trades, a.freq, mbo).write_html(out)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
