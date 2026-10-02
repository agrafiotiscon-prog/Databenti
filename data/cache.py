"""Local cache layout for downloaded DBN files.

Data is cached in one file per (dataset, schema, symbol, UTC day):

    cache/<dataset>/<schema>/<symbol>/<YYYY-MM-DD>.dbn.zst

Per-day chunks mean overlapping requests never re-download anything.
Files are written to a `.part` path and atomically renamed, so an
interrupted download is never mistaken for a cached one.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path


def _safe(s: str) -> str:
    return s.replace("/", "_").replace(":", "_")


def chunk_path(cache_dir: Path, dataset: str, schema: str, symbol: str, day: date) -> Path:
    return cache_dir / _safe(dataset) / _safe(schema) / _safe(symbol) / f"{day.isoformat()}.dbn.zst"


def parquet_path(dbn_path: Path) -> Path:
    return dbn_path.with_name(dbn_path.name.replace(".dbn.zst", ".parquet"))


def is_cached(path: Path) -> bool:
    return path.exists()


def part_path(path: Path) -> Path:
    return path.with_name(path.name + ".part")


def finalize(path: Path) -> None:
    """Atomically move a completed .part file into place."""
    part_path(path).replace(path)
