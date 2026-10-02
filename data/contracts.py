"""Quarterly equity-index futures calendar (ES, NQ, MES, MNQ) and roll selection.

Why this exists (see vault/01-databento/symbology-and-rolls.md):
  Databento's `ES.c.0` (calendar rule) only moves to the next contract AFTER
  the front contract expires, i.e. it stays on the dying contract during
  roll week. We instead choose, per CME trading date, which continuous rank to
  request:

      trading_date <  roll_date(front)  -> rank 0  (ES.c.0 = front contract)
      roll_date    <= trading_date <= expiry -> rank 1  (ES.c.1 = next contract)

  roll_date defaults to expiry - 4 calendar days: the MONDAY of expiry week.
  Measured on real data (scripts/roll_history.py, vault/results/roll-history-ES.md):
  every ES roll from 2022-06 to 2025-09 (14 in a row) crossed on that Monday. The old
  market convention (the Thursday 8 days before expiry) was wrong on 2 days per roll.
  Before mid-2022 the crossover was usually the Friday before (expiry - 7).

The rule uses only the calendar, so it introduces no lookahead.
Known limitation: if the 3rd Friday is an exchange holiday the real expiry
moves earlier (e.g. Good Friday 2008-03-21); verify with `definition` data.
"""
from __future__ import annotations

from datetime import date, timedelta

QUARTER_MONTHS = (3, 6, 9, 12)
MONTH_CODES = {3: "H", 6: "M", 9: "U", 12: "Z"}
DEFAULT_ROLL_DAYS_BEFORE_EXPIRY = 4


def third_friday(year: int, month: int) -> date:
    first = date(year, month, 1)
    offset = (4 - first.weekday()) % 7  # Friday == 4
    return first + timedelta(days=offset + 14)


def quarterly_expiries(start_year: int, end_year: int) -> list[date]:
    return [third_friday(y, m) for y in range(start_year, end_year + 1) for m in QUARTER_MONTHS]


def front_expiry(trading_date: date) -> date:
    """Nearest quarterly expiry on or after the trading date."""
    for exp in quarterly_expiries(trading_date.year, trading_date.year + 1):
        if exp >= trading_date:
            return exp
    raise AssertionError("unreachable")


def roll_date(expiry: date, days_before: int = DEFAULT_ROLL_DAYS_BEFORE_EXPIRY) -> date:
    return expiry - timedelta(days=days_before)


def continuous_rank(trading_date: date, days_before: int = DEFAULT_ROLL_DAYS_BEFORE_EXPIRY) -> int:
    """0 = front month, 1 = next month (inside the roll window)."""
    exp = front_expiry(trading_date)
    return 1 if trading_date >= roll_date(exp, days_before) else 0


def continuous_symbol(trading_date: date, root: str = "ES",
                      days_before: int = DEFAULT_ROLL_DAYS_BEFORE_EXPIRY) -> str:
    """Databento continuous symbol (calendar rule) to request for this trading date."""
    return f"{root}.c.{continuous_rank(trading_date, days_before)}"


def active_contract(trading_date: date, days_before: int = DEFAULT_ROLL_DAYS_BEFORE_EXPIRY) -> tuple[str, int]:
    """(month code, 4-digit year) of the contract we intend to trade on this date.

    For labelling/reporting only -- never build Databento raw symbols from this
    (CME uses 1- or 2-digit years); resolve via symbology instead.
    """
    exp = front_expiry(trading_date)
    if trading_date >= roll_date(exp, days_before):
        exp = front_expiry(exp + timedelta(days=1))
    return MONTH_CODES[exp.month], exp.year
