"""R3.5 tier-B fill calibration: the same passive probe orders under three fill models.

  python scripts/calibrate_fills.py --date 2024-03-05

Probe (not a strategy, nothing is selected): every 5 minutes in RTH, alternate a 1-lot buy limit at
the best bid and a sell limit at the best ask; cancel after 60 s; 100 ms order latency both ways.
Fill models:
  * engine trade_through  - L1 from TBBO; fills only when a trade prints through our price (pessimistic)
  * engine queue_l1       - L1 from TBBO; joins behind the displayed touch size, fills when it trades away
  * hftbacktest l3_fifo   - full MBO book, our order queued FIFO behind every resting order (reference)
Reported per model: fill rate, time to fill, and 60 s markout (mid move in our favour, ticks) of the
fills - the adverse-selection cost a passive strategy pays. Output: vault/results/fill-calibration-<date>.md
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

TICK = 0.25
LAT_NS = 100_000_000
LIFE = pd.Timedelta(seconds=60)
MARK = pd.Timedelta(seconds=60)


def probe_times(day: date) -> list[pd.Timestamp]:
    from data.sessions import session_bounds
    start, end = session_bounds(day, rth_only=True)
    t = pd.date_range(start + pd.Timedelta(minutes=5), end - pd.Timedelta(minutes=5), freq="5min")
    return list(t.tz_convert("UTC"))


def mid_at(l1: pd.DataFrame, ts) -> float:
    i = l1.index.searchsorted(ts, side="right") - 1
    r = l1.iloc[max(i, 0)]
    return float((r["bid_px"] + r["ask_px"]) / 2)


def engine_probe(l1: pd.DataFrame, times, mode: str) -> pd.DataFrame:
    from backtest.costs import load_costs
    from backtest.engine import run
    costs = load_costs()
    state = {"k": 0, "live": None}

    def strat(ts, rec, ctx):
        o = state["live"]
        if o is not None and ts >= o.submit_ts + LIFE:
            ctx.cancel(o)
            state["live"] = None
        if state["k"] < len(times) and ts >= times[state["k"]]:
            side = 1 if state["k"] % 2 == 0 else -1
            state["live"] = ctx.limit(side, rec.bid_px if side > 0 else rec.ask_px, tag=f"p{state['k']}")
            state["k"] += 1

    res = run(l1, strat, costs, max_position=10_000, fill_mode=mode)
    f = res.fills[~res.fills["end_flatten"]]
    rows = []
    for k, t in enumerate(times):
        side = 1 if k % 2 == 0 else -1
        g = f[f["tag"] == f"p{k}"]
        if len(g):
            r = g.iloc[0]
            rows.append({"k": k, "side": side, "filled": True, "maker": r["liquidity"] == "maker",
                         "price": r["price"], "fill_ts": r["fill_ts"], "submit_ts": r["submit_ts"]})
        else:
            rows.append({"k": k, "side": side, "filled": False, "maker": False, "price": np.nan,
                         "fill_ts": pd.NaT, "submit_ts": t})
    return pd.DataFrame(rows)


def hft_probe(events: np.ndarray, times) -> pd.DataFrame:
    from hftbacktest import GTX, LIMIT, BacktestAsset, HashMapMarketDepthBacktest
    asset = (BacktestAsset().data([events]).linear_asset(1.0).constant_order_latency(LAT_NS, LAT_NS)
             .l3_fifo_queue_model().no_partial_fill_exchange().trading_value_fee_model(0.0, 0.0)
             .tick_size(TICK).lot_size(1.0).last_trades_capacity(0))
    hbt = HashMapMarketDepthBacktest([asset])
    step = 100_000_000
    rows = []
    for k, t in enumerate(times):
        side = 1 if k % 2 == 0 else -1
        gap = int(t.value - hbt.current_timestamp)
        if gap > 0 and hbt.elapse(gap) != 0:
            break
        d = hbt.depth(0)
        px = d.best_bid if side > 0 else d.best_ask
        pos0 = hbt.position(0)
        if side > 0:
            hbt.submit_buy_order(0, k + 1, px, 1.0, GTX, LIMIT, False)
        else:
            hbt.submit_sell_order(0, k + 1, px, 1.0, GTX, LIMIT, False)
        fill_ts = None
        for _ in range(int(LIFE.value // step)):
            if hbt.elapse(step) != 0:
                break
            if hbt.position(0) != pos0:
                fill_ts = hbt.current_timestamp
                break
        if fill_ts is None:
            hbt.cancel(0, k + 1, False)
            for _ in range(3):                         # a fill can still happen while the cancel travels
                hbt.elapse(step)
                if hbt.position(0) != pos0:
                    fill_ts = hbt.current_timestamp
                    break
        hbt.clear_inactive_orders(0)
        rows.append({"k": k, "side": side, "filled": fill_ts is not None, "maker": fill_ts is not None,
                     "price": px if fill_ts is not None else np.nan,
                     "fill_ts": pd.Timestamp(fill_ts, tz="UTC") if fill_ts is not None else pd.NaT, "submit_ts": t})
    hbt.close()
    return pd.DataFrame(rows)


def summarise(df: pd.DataFrame, l1: pd.DataFrame) -> dict:
    f = df[df["filled"]]
    mk = [s * (mid_at(l1, ts + MARK) - p) / TICK for s, p, ts in zip(f["side"], f["price"], f["fill_ts"])]
    wait = (f["fill_ts"] - f["submit_ts"]).dt.total_seconds()
    return {"probes": len(df), "filled": len(f), "fill_rate": round(len(f) / max(len(df), 1), 3),
            "maker_fills": int(f["maker"].sum()), "median_wait_s": round(float(wait.median()), 1) if len(f) else None,
            "markout60_ticks_mean": round(float(np.mean(mk)), 2) if mk else None,
            "markout60_ticks_median": round(float(np.median(mk)), 2) if mk else None}


def main(argv=None) -> int:
    from backtest.engine import l1_from_tbbo
    from backtest.hft_adapter import to_hft_events
    from data.download import Downloader
    from data.loader import load_session
    from scripts.run_h001 import md
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--date", required=True, type=date.fromisoformat)
    a = ap.parse_args(argv)
    dl = Downloader()
    times = probe_times(a.date)
    l1 = l1_from_tbbo(load_session(dl, "tbbo", a.date, rth_only=True))
    out = {m: engine_probe(l1, times, m) for m in ("trade_through", "queue_l1")}
    mbo = load_session(dl, "mbo", a.date, rth_only=False)
    mbo = mbo[mbo.index <= times[-1] + pd.Timedelta(minutes=5)]
    out["hft_l3_fifo"] = hft_probe(to_hft_events(mbo.drop(columns=["warmup", "trading_date", "session"], errors="ignore")), times)
    summ = pd.DataFrame({m: summarise(df, l1) for m, df in out.items()}).T
    agree = pd.DataFrame({m: out[m]["filled"].to_numpy() for m in out}).astype(int)
    both = {f"{m} vs hft": round(float((agree[m] == agree["hft_l3_fifo"]).mean()), 3) for m in ("trade_through", "queue_l1")}
    print(summ.to_string(), "\n", both)
    path = ROOT / "vault" / "results" / f"fill-calibration-{a.date}.md"
    path.write_text("\n".join([
        "---", "type: result", f"date: {date.today().isoformat()}", "tags: [phase-3, R3.5, fills, calibration]", "---",
        f"# Tier-B fill calibration on {a.date} (R3.5, `scripts/calibrate_fills.py`)", "",
        f"{len(times)} passive 1-lot probes (every 5 min in RTH, alternating buy at bid / sell at ask, 60 s life, "
        "100 ms latency). Markout = mid 60 s after the fill minus fill price, in our favour, ticks.", "",
        md(summ), "", f"Fill/no-fill agreement with the L3 FIFO reference: {both}", ""]) + "\n")
    print("saved", path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
