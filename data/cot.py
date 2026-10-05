"""CFTC Commitments of Traders, legacy futures-only report (free; cftc.gov/files/dea/history/deacotYYYY.zip).

Cached as downloaded in cache/cftc/ (not in git). load_cot() returns one row per (as-of date, root) with open interest
and commercial / non-commercial long and short positions.
"""
from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "cache" / "cftc"
URL = "https://www.cftc.gov/files/dea/history/deacot{year}.zip"

# CFTC contract market code -> futures root (legacy report)
CODES = {"067651": "CL", "023651": "NG", "111659": "RB", "022651": "HO", "088691": "GC", "084691": "SI",
         "085692": "HG", "076651": "PL", "075651": "PA", "002602": "ZC", "005602": "ZS", "001602": "ZW",
         "001612": "KE", "007601": "ZL", "026603": "ZM", "057642": "LE", "054642": "HE", "061641": "GF"}
COLS = {"As of Date in Form YYYY-MM-DD": "asof", "CFTC Contract Market Code": "code", "Open Interest (All)": "oi",
        "Commercial Positions-Long (All)": "comm_long", "Commercial Positions-Short (All)": "comm_short",
        "Noncommercial Positions-Long (All)": "spec_long", "Noncommercial Positions-Short (All)": "spec_short"}


def fetch(years, cache: Path = CACHE) -> None:
    import urllib.request
    cache.mkdir(parents=True, exist_ok=True)
    for y in years:
        p = cache / f"deacot{y}.zip"
        if not p.exists():
            with urllib.request.urlopen(URL.format(year=y), timeout=60) as r:
                p.write_bytes(r.read())


def parse(raw: bytes) -> pd.DataFrame:
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        df = pd.read_csv(z.open(z.namelist()[0]), dtype={"CFTC Contract Market Code": str}, low_memory=False)
    df.columns = [c.strip() for c in df.columns]
    df = df[list(COLS)].rename(columns=COLS)
    df["code"] = df["code"].str.strip()
    df = df[df["code"].isin(CODES)].copy()
    df["root"] = df["code"].map(CODES)
    df["asof"] = pd.to_datetime(df["asof"]).dt.date
    return df.drop(columns="code")


def load_cot(cache: Path = CACHE) -> pd.DataFrame:
    parts = [parse(p.read_bytes()) for p in sorted(cache.glob("deacot*.zip"))]
    df = pd.concat(parts).drop_duplicates(["asof", "root"]).sort_values(["root", "asof"]).reset_index(drop=True)
    return df


def hedger_change(cot: pd.DataFrame, max_gap_days: int = 14) -> pd.DataFrame:
    """dH = change of commercials' net long from the previous report, / previous open interest (KRT 2020 eq. 4)."""
    out = []
    for r, g in cot.groupby("root"):
        g = g.sort_values("asof")
        net = g["comm_long"] - g["comm_short"]
        gap = pd.to_datetime(g["asof"]).diff().dt.days
        dh = net.diff() / g["oi"].shift()
        out.append(pd.DataFrame({"asof": g["asof"], "root": r, "dH": dh.where(gap <= max_gap_days)}))
    return pd.concat(out).dropna().pivot(index="asof", columns="root", values="dH").sort_index()
