"""Append-only trial log: research/trials.jsonl (vault/05-anti-overfitting/research-loop.md).

Every backtest variant is logged, failures included, and the count is never reset (it is the N
of the deflated Sharpe). Records are hash-chained: each stores the SHA-256 of the previous line
(`prev_sha`), so editing or deleting an earlier line is detectable with `verify()`.

A trial for a registered hypothesis must use parameters inside its declared space, and is
refused once the hypothesis's trial budget is spent. Engine sanity runs use family
"engine-sanity" and hypothesis "none".
"""
from __future__ import annotations

import fcntl
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from . import registry

TRIALS = Path(__file__).resolve().parent / "trials.jsonl"
REQUIRED = ("family", "hypothesis", "params", "data", "fill_mode", "results")


class TrialError(ValueError):
    pass


def _sha(line: str) -> str:
    return hashlib.sha256(line.encode()).hexdigest()


def _lines(path: Path) -> list[str]:
    return [l for l in Path(path).read_text().splitlines() if l.strip()] if Path(path).exists() else []


def read(path: Path = TRIALS) -> list[dict]:
    return [json.loads(l) for l in _lines(path)]


def count(path: Path = TRIALS, family: str | None = None, hypothesis: str | None = None) -> int:
    return sum(1 for r in read(path) if (family is None or r.get("family") == family)
               and (hypothesis is None or r.get("hypothesis") == hypothesis))


def verify(path: Path = TRIALS) -> int:
    """Check the hash chain; returns the number of records. Records written before chaining existed
    (no `prev_sha`) are accepted only as a prefix."""
    lines, chained = _lines(path), False
    for i, line in enumerate(lines):
        rec = json.loads(line)
        if "prev_sha" not in rec:
            if chained:
                raise TrialError(f"record {i} has no prev_sha after the chain started")
            continue
        chained = True
        expect = _sha(lines[i - 1]) if i else ""
        if rec["prev_sha"] != expect or rec.get("n") != i:
            raise TrialError(f"trial log broken at record {i}: an earlier line was changed or removed")
    return len(lines)


def append(record: dict, path: Path = TRIALS, hypotheses_dir: Path = registry.HYPOTHESES_DIR) -> dict:
    """Append one hash-chained record. An exclusive lock on <path>.lock makes the budget check, chain
    read and write atomic, so several evaluation processes can run in parallel."""
    missing = [k for k in REQUIRED if k not in record]
    if missing:
        raise TrialError(f"trial record missing {missing}")
    lock = Path(str(path) + ".lock")
    with lock.open("a") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        try:
            hyp = record["hypothesis"]
            if hyp != "none":
                h = registry.load(hyp, hypotheses_dir)
                if h.status != "open":
                    raise TrialError(f"{hyp} is closed")
                if not h.in_space(record["params"]):
                    raise TrialError(f"params {record['params']} are outside the declared space of {hyp}")
                used = count(path, hypothesis=hyp)
                if used >= h.trial_budget:
                    raise TrialError(f"{hyp} trial budget spent ({used}/{h.trial_budget})")
            verify(path)
            lines = _lines(path)
            rec = {"n": len(lines), "ts": datetime.now(timezone.utc).isoformat(), **record,
                   "prev_sha": _sha(lines[-1]) if lines else ""}
            with Path(path).open("a") as f:
                f.write(json.dumps(rec, sort_keys=True, default=str) + "\n")
        finally:
            fcntl.flock(lk, fcntl.LOCK_UN)
    return rec
