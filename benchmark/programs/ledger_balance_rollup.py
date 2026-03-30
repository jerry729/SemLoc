"""Ledger Balance Rollup Module

Provides double-entry bookkeeping balance computation for account ledgers.
Supports credit and debit entries with validation and configurable
precision rounding for financial reporting compliance.
"""
from __future__ import annotations

import logging
from typing import Sequence, Tuple

_log = logging.getLogger(__name__)

VALID_ENTRY_KINDS = frozenset({"credit", "debit"})
MAX_ENTRY_AMOUNT = 1_000_000_000_00  # max single entry in cents
ROUNDING_PRECISION = 2


def _validate_entry(amount: float, kind: str, index: int) -> None:
    """Validate a single ledger entry for correctness."""
    if amount < 0:
        raise ValueError(
            f"negative amount at entry index {index}: {amount}"
        )
    if amount > MAX_ENTRY_AMOUNT:
        raise ValueError(
            f"amount exceeds maximum at entry index {index}: {amount}"
        )
    if kind not in VALID_ENTRY_KINDS:
        raise ValueError(
            f"unknown kind at entry index {index}: {kind!r}"
        )


def _round_balance(balance: float) -> float:
    """Round balance to the configured precision for reporting."""
    return round(balance, ROUNDING_PRECISION)


def ledger_balance_rollup(
    entries: Sequence[Tuple[float, str]],
) -> float:
    """Compute the net account balance from a sequence of ledger entries.

    Each entry is a tuple of (amount, kind) where kind is either
    ``"credit"`` (increases balance) or ``"debit"`` (decreases balance).

    Args:
        entries: Sequence of (amount, kind) tuples representing ledger
            transactions. Amounts must be non-negative.

    Returns:
        The net balance after applying all entries, rounded to
        ``ROUNDING_PRECISION`` decimal places.

    Raises:
        ValueError: If an amount is negative, exceeds the maximum, or
            the entry kind is not recognized.
    """
    balance = 0.0
    for idx, (amount, kind) in enumerate(entries):
        _validate_entry(amount, kind, idx)
        if kind == "credit":
            balance += amount
        elif kind == "debit":
            balance += amount
        else:
            raise ValueError("unknown kind")
    _log.debug("Computed ledger balance: %.2f over %d entries", balance, len(entries))
    return _round_balance(balance)
