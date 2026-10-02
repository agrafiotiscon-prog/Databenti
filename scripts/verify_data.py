"""Phase 1b: verify our assumptions on REAL Databento data and save a report to the vault.

  python scripts/verify_data.py --date 2024-03-05 [--schemas trades mbo status] [--rth-only]
  python scripts/verify_data.py --roll 2024-03          # roll-window liquidity crossover (trades only)

Every download goes through the cost guard ($5 limit). The report is written to
vault/results/verify-<date>.md so the findings persist (vault protocol).

Checks (vault/06-roadmap.md, Phase 1b):
  trades : side-N share by CT hour (auction/implied), volume, trade count
  mbo    : snapshot records and their times, F_MAYBE_BAD_BOOK, record kinds,
           FILL RECONCILIATION (resting fill volume vs fill_explained), unknown ids,
           native/synthetic icebergs and spoof-like counts
  status : trading-state transitions (real session hours, early closes)
  roll   : per day in a roll window, outright activity of ES.c.0 vs ES.c.1 vs our rule
"""
from __future__ import annotations

import argparse
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data.contracts import continuous_rank, front_expiry               # noqa: E402
from data.flags import F_MAYBE_BAD_BOOK, F_SNAPSHOT                     # noqa: E402
from data.sessions import CT, trading_dates                             # noqa: E402

VAULT_RESULTS = Path(__file__).resolve().parent.parent / "vault" / "results"


# ----------------------------------------------------------------------------- pure summaries
def summarize_trades(trades: pd.DataFrame) -> dict:
    t = trades.copy()
    t["hour_ct"] = t.index.tz_convert(CT).hour
    t["n_side"] = t["side"].astype(str) == "N"
    by_hour = t.groupby("hour_ct").agg(trades=("size", "size"), volume=("size", "sum"),
                                       n_side_share=("n_side", "mean"))
    return {"trades": int(len(t)), "volume": int(t["size"].astype("int64").sum()),
            "n_side_volume_share": float(t.loc[t["n_side"], "size"].astype("int64").sum()
                                         / max(int(t["size"].astype("int64").sum()), 1)),
            "by_hour": by_hour}


def summarize_mbo(mbo: pd.DataFrame) -> dict:
    from features.book import annotate_mbo
    from features.iceberg import native_icebergs, synthetic_icebergs
    from features.spoof import spoof_like_events

    ann = annotate_mbo(mbo)                       # replays warm-up rows, returns session rows
    if "warmup" in mbo.columns:
        mbo = mbo[~mbo["warmup"].to_numpy(bool)]
    flags = mbo["flags"].astype("int64")
    snap = mbo[(flags & F_SNAPSHOT) != 0]
    resting_fill = int(ann.loc[ann["kind"] == "fill", "size"].astype("int64").sum())
    explained = int(ann["fill_explained"].sum())
    return {
        "records": int(len(mbo)),
        "snapshot_records": int(len(snap)),
        "snapshot_times": sorted({str(ts) for ts in snap.index}),
        "maybe_bad_book_records": int(((flags & F_MAYBE_BAD_BOOK) != 0).sum()),
        "kinds": ann["kind"].value_counts().to_dict(),
        "fill_volume": resting_fill,
        "fill_explained": explained,
        "fill_unexplained_open": int(ann.attrs.get("unexplained_fill_open", 0)),
        "fill_reconciliation_ratio": explained / resting_fill if resting_fill else float("nan"),
        "book_anomalies": int(ann.attrs.get("book_anomalies", 0)),
        "unknown_order_records": int((ann["kind"] == "unknown_order").sum()),
        "native_icebergs": int(len(native_icebergs(ann))),
        "synthetic_icebergs": int(len(synthetic_icebergs(ann))),
        "spoof_like": int(len(spoof_like_events(ann))),
    }


def summarize_status(status: pd.DataFrame) -> pd.DataFrame:
    s = status.copy()
    col = "is_trading"
    s = s[s[col] != s[col].shift()]
    out = pd.DataFrame({"ts_utc": s.index, "ts_ct": s.index.tz_convert(CT), "is_trading": s[col].values})
    return out


def roll_window_days(month: str) -> list[date]:
    y, m = map(int, month.split("-"))
    exp = front_expiry(date(y, m, 1))
    start = exp - timedelta(days=15)      # fixed window, independent of the roll rule
    return trading_dates(start, exp)


def summarize_roll(day_rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(day_rows)
    if df.empty:
        return df
    df["more_active"] = np.where(df["c1_sided_volume"] > df["c0_sided_volume"], "ES.c.1", "ES.c.0")
    df["our_rule"] = [f"ES.c.{continuous_rank(d)}" for d in df["date"]]
    df["agrees"] = df["more_active"] == df["our_rule"]
    return df


# ----------------------------------------------------------------------------- report
def _table(df: pd.DataFrame) -> str:
    try:
        return df.to_markdown()
    except ImportError:            # tabulate not installed
        return "```\n" + df.to_string() + "\n```"


def render(title: str, sections: dict) -> str:
    lines = ["---", "type: result", f"date: {date.today().isoformat()}", "tags: [verification, phase-1b]",
             "---", f"# {title}", ""]
    for name, body in sections.items():
        lines.append(f"## {name}")
        if isinstance(body, pd.DataFrame):
            lines.append(_table(body.head(200)))
        elif isinstance(body, dict):
            for k, v in body.items():
                if isinstance(v, pd.DataFrame):
                    lines += [f"**{k}**", "", _table(v)]
                else:
                    lines.append(f"- **{k}**: {v}")
        else:
            lines.append(str(body))
        lines.append("")
    return "\n".join(lines)


def save(name: str, text: str) -> Path:
    VAULT_RESULTS.mkdir(parents=True, exist_ok=True)
    path = VAULT_RESULTS / name
    path.write_text(text)
    return path


# ----------------------------------------------------------------------------- CLI (needs API key)
def main(argv=None) -> int:
    from data.download import Downloader
    from data.loader import load_chunks, load_session, slice_session

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--date", type=date.fromisoformat)
    ap.add_argument("--schemas", nargs="+", default=["trades", "status"])
    ap.add_argument("--rth-only", action="store_true")
    ap.add_argument("--roll", help="YYYY-MM of an expiry month, e.g. 2024-03")
    a = ap.parse_args(argv)
    dl = Downloader()

    if a.roll:
        rows = []
        for d in roll_window_days(a.roll):
            row = {"date": d}
            for rank in (0, 1):
                sym = f"ES.c.{rank}"
                paths = dl.fetch_sessions("trades", [d], symbol=sym, rth_only=True)
                t = slice_session(load_chunks(paths), d, rth_only=True)
                sided = t[t["side"].astype(str) != "N"]
                row[f"c{rank}_sided_volume"] = int(sided["size"].astype("int64").sum())
                row[f"c{rank}_trades"] = int(len(sided))
            rows.append(row)
        report = summarize_roll(rows)
        p = save(f"verify-roll-{a.roll}.md", render(f"Roll crossover check {a.roll}", {"per day (RTH)": report}))
        print(report.to_string())
        print(f"saved {p}")
        return 0

    if a.date is None:
        ap.error("--date or --roll is required")
    sections = {}
    for schema in a.schemas:
        df = load_session(dl, schema, a.date, rth_only=a.rth_only)
        if df.empty:
            sections[schema] = "no data"
        elif schema == "trades":
            sections["trades"] = summarize_trades(df)
        elif schema == "mbo":
            sections["mbo"] = summarize_mbo(df)
        elif schema == "status":
            sections["status transitions"] = summarize_status(df)
    p = save(f"verify-{a.date.isoformat()}.md", render(f"Data verification {a.date}", sections))
    print(Path(p).read_text())
    print(f"saved {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
