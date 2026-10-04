"""R7 diversified CME futures universe (D-048): contract specs used for P&L and costs.

point_value = USD per 1.00 of the quoted price; tick = minimum price increment in quoted units.
Quoted units follow Databento GLBX.MDP3 prices (grains/livestock in cents, rates in points).
Checked against price levels after download (vault/results/futures-daily-check.md).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Spec:
    root: str
    sector: str
    point_value: float
    tick: float

    @property
    def tick_value(self) -> float:
        return self.point_value * self.tick


UNIVERSE = [
    Spec("ES", "equity", 50, 0.25), Spec("NQ", "equity", 20, 0.25), Spec("RTY", "equity", 50, 0.10),
    Spec("YM", "equity", 5, 1.0),
    Spec("ZT", "rates", 2000, 1 / 256), Spec("ZF", "rates", 1000, 1 / 128), Spec("ZN", "rates", 1000, 1 / 64),
    Spec("ZB", "rates", 1000, 1 / 32),
    Spec("CL", "energy", 1000, 0.01), Spec("NG", "energy", 10000, 0.001), Spec("RB", "energy", 42000, 0.0001),
    Spec("HO", "energy", 42000, 0.0001),
    Spec("GC", "metals", 100, 0.10), Spec("SI", "metals", 5000, 0.005), Spec("HG", "metals", 25000, 0.0005),
    Spec("6E", "fx", 125000, 0.00005), Spec("6J", "fx", 12_500_000, 0.0000005), Spec("6B", "fx", 62500, 0.0001),
    Spec("6A", "fx", 100000, 0.00005), Spec("6C", "fx", 100000, 0.00005), Spec("6S", "fx", 125000, 0.00005),
    Spec("ZC", "grains", 50, 0.25), Spec("ZS", "grains", 50, 0.25), Spec("ZW", "grains", 50, 0.25),
    Spec("LE", "livestock", 400, 0.025), Spec("HE", "livestock", 400, 0.025),
]
BY_ROOT = {s.root: s for s in UNIVERSE}
START, END = "2010-06-07", "2025-10-01"          # END exclusive; holdout starts 2025-10-03

# CME micro contracts (R9.8): same underlying and price quote, point value scaled by `factor`. Used only to make
# small-account sizing realistic (no separate price data: micros track the full-size contract by arbitrage).
# Sizes from CME contract specs [doc]; launch dates marked [assumption] are not verified - a backtest that applies
# a micro before its launch is optimistic for that period. Rates, grains (micro ags launched 2023) and livestock
# have no micro used here.
MICRO = {
    "ES": ("MES", 0.1), "NQ": ("MNQ", 0.1), "RTY": ("M2K", 0.1), "YM": ("MYM", 0.1),     # May 2019
    "GC": ("MGC", 0.1), "SI": ("SIL", 0.2), "HG": ("MHG", 0.1),                          # MHG 2021 [assumption]
    "CL": ("MCL", 0.1), "NG": ("MNG", 0.1),                                               # 2021 [assumption]
    "6E": ("M6E", 0.1), "6A": ("M6A", 0.1), "6B": ("M6B", 0.1), "6J": ("MJY", 0.1),
    "6C": ("MCD", 0.1), "6S": ("MSF", 0.1),
}
MICRO_FEE_SIDE = 0.352 + 0.02 + 0.25   # MES per side in config/costs.toml (exchange + NFA + IBKR); assumed for all micros


def micro_specs() -> dict:
    """root -> Spec with the micro point value (same tick size, so tick value scales too)."""
    return {r: Spec(r, BY_ROOT[r].sector, BY_ROOT[r].point_value * f, BY_ROOT[r].tick) for r, (_, f) in MICRO.items()}
