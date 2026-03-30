from __future__ import annotations

import logging
from typing import Sequence, List

_log = logging.getLogger(__name__)

_MIN_PAYOUT = 0.0
_MAX_RECIPIENTS = 100
_DEFAULT_FEE = 0.0
_PRECISION = 2


def _validate_ratios(ratios: Sequence[float]) -> None:
    """Ensure the ratio vector is well-formed."""
    if len(ratios) == 0:
        raise ValueError("no ratios")
    if len(ratios) > _MAX_RECIPIENTS:
        raise ValueError(f"too many recipients (max {_MAX_RECIPIENTS})")
    if sum(ratios) <= 0:
        raise ValueError("invalid ratios")


def _round_share(value: float) -> float:
    """Round a single share to the configured decimal precision."""
    return round(value, _PRECISION)


def tip_share(
    amount: float,
    ratios: Sequence[float],
    *,
    fee: float = _DEFAULT_FEE,
) -> List[float]:
    """Split a tip amount across recipients according to weighted ratios.

    The platform fee is deducted before distributing shares.  Each
    recipient's payout is floored at ``_MIN_PAYOUT`` and rounded to
    ``_PRECISION`` decimal places.

    Args:
        amount: Total tip amount (non-negative).
        ratios: Positive weights controlling the split among recipients.
        fee: Flat service fee deducted from the total before splitting.

    Returns:
        A list of per-recipient payout amounts.

    Raises:
        ValueError: If *ratios* is empty, sums to zero or less, or
            *amount* is negative.
    """
    _validate_ratios(ratios)
    if amount < 0:
        raise ValueError("negative amount")

    _log.debug("Splitting %.2f among %d recipients (fee=%.2f)", amount, len(ratios), fee)

    total_ratio = sum(ratios)
    base = [(r / total_ratio) * amount for r in ratios]

    result = [max(_MIN_PAYOUT, _round_share(share - fee)) for share in base]
    return result
