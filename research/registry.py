"""Hypothesis registry: research/hypotheses/<ID>.yaml, written BEFORE any result is seen.

Required fields (vault/05-anti-overfitting/research-loop.md):
  id            H-001 ...
  title
  mechanism     why it should make money and who pays us (>= 40 characters, no hand-waving)
  direction     fade | follow | both
  horizon       holding time in words, e.g. "2-30 min"
  features      list of feature names it uses
  space         {param: [allowed values]}  -- the ONLY values a trial may use
  trial_budget  max number of trials (<= the size of the space)
  registered    ISO date
  status        open | closed
"""
from __future__ import annotations

import itertools
import math
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import yaml

HYPOTHESES_DIR = Path(__file__).resolve().parent / "hypotheses"
REQUIRED = ("id", "title", "mechanism", "direction", "horizon", "features", "space", "trial_budget",
            "registered", "status")


class RegistryError(ValueError):
    pass


@dataclass(frozen=True)
class Hypothesis:
    id: str
    title: str
    mechanism: str
    direction: str
    horizon: str
    features: tuple[str, ...]
    space: dict
    trial_budget: int
    registered: date
    status: str

    @property
    def space_size(self) -> int:
        return math.prod(len(v) for v in self.space.values())

    def grid(self):
        keys = sorted(self.space)
        for combo in itertools.product(*(self.space[k] for k in keys)):
            yield dict(zip(keys, combo))

    def in_space(self, params: dict) -> bool:
        return set(params) == set(self.space) and all(params[k] in self.space[k] for k in self.space)


def parse(doc: dict) -> Hypothesis:
    missing = [k for k in REQUIRED if k not in doc]
    if missing:
        raise RegistryError(f"missing fields: {missing}")
    if len(str(doc["mechanism"]).strip()) < 40:
        raise RegistryError("mechanism must explain who pays and why (>= 40 characters)")
    if doc["direction"] not in ("fade", "follow", "both"):
        raise RegistryError("direction must be fade | follow | both")
    space = doc["space"]
    if not isinstance(space, dict) or not space or not all(isinstance(v, list) and v for v in space.values()):
        raise RegistryError("space must map each parameter to a non-empty list of allowed values")
    h = Hypothesis(str(doc["id"]), str(doc["title"]), str(doc["mechanism"]).strip(), doc["direction"],
                   str(doc["horizon"]), tuple(doc["features"]), space, int(doc["trial_budget"]),
                   doc["registered"] if isinstance(doc["registered"], date) else date.fromisoformat(str(doc["registered"])),
                   str(doc["status"]))
    if not 0 < h.trial_budget <= h.space_size:
        raise RegistryError(f"trial_budget must be in 1..{h.space_size} (size of the declared space)")
    if h.status not in ("open", "closed"):
        raise RegistryError("status must be open | closed")
    return h


def load(hyp_id: str, directory: Path = HYPOTHESES_DIR) -> Hypothesis:
    path = Path(directory) / f"{hyp_id}.yaml"
    if not path.exists():
        raise RegistryError(f"{hyp_id} is not registered ({path})")
    h = parse(yaml.safe_load(path.read_text()))
    if h.id != hyp_id:
        raise RegistryError(f"file {path.name} declares id {h.id}")
    return h


def load_all(directory: Path = HYPOTHESES_DIR) -> list[Hypothesis]:
    return [load(p.stem, directory) for p in sorted(Path(directory).glob("H-*.yaml"))]
