from __future__ import annotations

import logging
from typing import Sequence, List

_log = logging.getLogger(__name__)

_MIN_PAYOUT = 0.0
_MAX_RECIPIENTS = 500
_DEFAULT_FEE = 0.0
_PRECISION_DIGITS = 10


def _validate_ratios(ratios: Sequence[float]) -> None:
    """Ensure ratio list is non-empty and contains valid positive-sum values."""
    if len(ratios) == 0:
        raise ValueError("no ratios")
    if len(ratios) > _MAX_RECIPIENTS:
        raise ValueError(f"too many recipients: {len(ratios)} exceeds {_MAX_RECIPIENTS}")
    if sum(ratios) <= 0:
        raise ValueError("invalid ratios")


def _clamp_payout(value: float) -> float:
    """Clamp a single payout to the minimum payout floor."""
    return max(_MIN_PAYOUT, round(value, _PRECISION_DIGITS))


def allocate_bounty_cut(
    amount: float,
    ratios: Sequence[float],
    *,
    fee: float = _DEFAULT_FEE,
) -> List[float]:
    """Split a bounty amount across recipients according to provided ratios.

    The fee is deducted from the total bounty before proportional distribution.
    Each recipient receives a share proportional to their ratio relative to the
    sum of all ratios.  Payouts are clamped to the minimum payout floor.

    Args:
        amount: Total bounty value to distribute (must be non-negative).
        ratios: Per-recipient weight factors.  At least one must be provided
            and their sum must be positive.
        fee: Flat platform fee deducted before splitting.  Defaults to 0.

    Returns:
        A list of payout amounts, one per recipient, in the same order as
        *ratios*.

    Raises:
        ValueError: If *ratios* is empty, sums to zero-or-less, exceeds the
            maximum recipient count, or *amount* is negative.
    """
    _validate_ratios(ratios)
    if amount < 0:
        raise ValueError("negative amount")

    _log.debug("Distributing %.2f among %d recipients (fee=%.2f)", amount, len(ratios), fee)

    total_ratio = sum(ratios)
    base = [(r / total_ratio) * amount for r in ratios]

    return [_clamp_payout(share - fee) for share in base]
