"""Central configuration for the data layer.

All values can be overridden via environment variables (loaded from `.env`).
The API key is only ever read here and handed to the client; it is never
printed or logged.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATASET = "GLBX.MDP3"
DEFAULT_SYMBOL = "ES.c.0"          # front month, calendar roll
DEFAULT_STYPE_IN = "continuous"
SUPPORTED_SCHEMAS = ("trades", "mbp-10", "mbo", "ohlcv-1m", "ohlcv-1d", "definition")
DEFAULT_MAX_COST_USD = 5.0


@dataclass(frozen=True)
class Settings:
    cache_dir: Path
    max_cost_usd: float


def load_settings() -> Settings:
    load_dotenv(PROJECT_ROOT / ".env")
    cache_dir = Path(os.getenv("DATABENTO_CACHE_DIR", PROJECT_ROOT / "cache"))
    if not cache_dir.is_absolute():
        cache_dir = PROJECT_ROOT / cache_dir
    max_cost = float(os.getenv("DATABENTO_MAX_COST_USD", DEFAULT_MAX_COST_USD))
    return Settings(cache_dir=cache_dir, max_cost_usd=max_cost)


def get_api_key() -> str:
    """Return the API key from the environment / .env. Never print the result."""
    load_dotenv(PROJECT_ROOT / ".env")
    key = os.getenv("DATABENTO_API_KEY", "").strip()
    if not key:
        raise RuntimeError(
            "DATABENTO_API_KEY is not set. Copy .env.example to .env and add your key."
        )
    return key


def get_client():
    """Build a Databento Historical client using the key from .env."""
    import databento as db

    return db.Historical(get_api_key())
