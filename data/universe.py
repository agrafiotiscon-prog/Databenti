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
