"""Transaction costs and execution assumptions from config/costs.toml."""
from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

COSTS_TOML = Path(__file__).resolve().parent.parent / "config" / "costs.toml"


@dataclass(frozen=True)
class CostModel:
    instrument: str
    tick: float
    tick_value: float            # USD per tick per contract
    fee_per_side: float          # USD per contract per side (exchange + NFA + commission)
    latency_ms: float            # decision -> exchange arrival
    fee_multiplier: float = 1.0  # stress: 1.5, 2.0

    @property
    def point_value(self) -> float:
        return self.tick_value / self.tick

    def fee(self, qty: int) -> float:
        return abs(qty) * self.fee_per_side * self.fee_multiplier


def load_costs(instrument: str = "ES", profile: str | None = None, fee_multiplier: float = 1.0,
               latency_ms: float | None = None, path: Path = COSTS_TOML) -> CostModel:
    cfg = tomllib.loads(Path(path).read_text())
    prof = cfg["profiles"][profile or cfg["default_profile"]]
    side = prof["per_side"][instrument]
    inst = cfg["instruments"][instrument]
    return CostModel(instrument, float(inst["tick"]), float(inst["tick_value"]),
                     float(side["exchange"] + side["nfa"] + side["commission"]),
                     float(cfg["execution"]["latency_ms"] if latency_ms is None else latency_ms),
                     float(fee_multiplier))
