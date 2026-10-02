"""Contract roll handling for continuous futures symbols.

`ES.c.0` (stype_in="continuous") maps each day to the front-month contract
by calendar rule. Records keep the *underlying* contract's `instrument_id`,
so a roll shows up as a change in `instrument_id`.

Policy used in this project (see README):
  * Order-flow features (footprint, delta, book, MBO) are computed per
    contract and NEVER stitched across a roll inside one bar/window.
  * Price-level comparisons across days (e.g. prior-day POC) must use
    back-adjusted prices; `back_adjust()` applies a difference adjustment
    from a roll table of (roll_ts, price_gap).
"""
from __future__ import annotations

import pandas as pd


def detect_rolls(df: pd.DataFrame, id_col: str = "instrument_id") -> pd.DataFrame:
    """Return one row per roll: timestamp of first record of the new contract."""
    if df.empty:
        return pd.DataFrame(columns=["ts", "old_id", "new_id"])
    ids = df[id_col]
    changed = ids.ne(ids.shift()) & ids.shift().notna()
    rolls = pd.DataFrame(
        {"ts": df.index[changed.values], "old_id": ids.shift()[changed].values,
         "new_id": ids[changed].values}
    )
    return rolls.reset_index(drop=True)


def contract_segments(df: pd.DataFrame, id_col: str = "instrument_id") -> pd.Series:
    """Integer segment number that increments at each roll (for groupby)."""
    ids = df[id_col]
    return ids.ne(ids.shift()).cumsum().rename("contract_segment")


def roll_calendar(resolve_result: dict, symbol: str) -> pd.DataFrame:
    """Parse `client.symbology.resolve(...)` output into a date -> instrument_id table.

    The resolve endpoint is free (no data cost).
    """
    rows = resolve_result.get("result", {}).get(symbol, [])
    out = pd.DataFrame(
        [{"d0": r["d0"], "d1": r["d1"], "instrument_id": int(r["s"])} for r in rows]
    )
    if not out.empty:
        out["d0"] = pd.to_datetime(out["d0"]).dt.date
        out["d1"] = pd.to_datetime(out["d1"]).dt.date
    return out


def back_adjust(prices: pd.Series, roll_table: pd.DataFrame) -> pd.Series:
    """Difference back-adjustment.

    `roll_table` has columns `ts` (roll time) and `gap` = new_contract_price -
    old_contract_price measured at the SAME instant (e.g. both contracts'
    close on the roll day). Every price strictly before a roll is shifted
    by that roll's gap, so the most recent contract is unadjusted.

    Only uses information known at the roll time, but note: an adjusted
    historical series is still a research convenience -- the backtester
    trades the actual contract prices.
    """
    adj = prices.astype(float).copy()
    for _, r in roll_table.iterrows():
        adj[adj.index < r["ts"]] += r["gap"]
    return adj
