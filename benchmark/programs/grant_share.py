from __future__ import annotations

import logging
from typing import Sequence, List

_log = logging.getLogger(__name__)

_MIN_PAYOUT = 0.0
_MAX_RECIPIENTS = 500
_DEFAULT_FEE = 0.0
_PRECISION_DIGITS = 10


def _validate_ratios(ratios: Sequence[float]) -> None:
    """Ensure ratio list is non-empty and sums to a positive value."""
    if len(ratios) == 0:
        raise ValueError("no ratios")
    if len(ratios) > _MAX_RECIPIENTS:
        raise ValueError(f"too many recipients: {len(ratios)} exceeds {_MAX_RECIPIENTS}")
    if sum(ratios) <= 0:
        raise ValueError("invalid ratios")


def _clamp_payout(value: float) -> float:
    """Clamp a single payout to the minimum payout floor."""
    return max(_MIN_PAYOUT, round(value, _PRECISION_DIGITS))


def grant_share(
    amount: float,
    ratios: Sequence[float],
    *,
    fee: float = _DEFAULT_FEE,
) -> List[float]:
    """Split a grant amount across recipients according to given ratios.

    The total fee is deducted from the pool before distribution. Each
    recipient receives a share proportional to their ratio, clamped to
    a minimum payout floor.

    Args:
        amount: Total grant amount to distribute (non-negative).
        ratios: Proportional weights for each recipient.  Must contain
            at least one positive value.
        fee: Flat processing fee deducted from the total pool before
            shares are computed.

    Returns:
        A list of per-recipient payouts whose sum equals the net
        distributable amount.

    Raises:
        ValueError: If *ratios* is empty, sums to zero or less, or
            *amount* is negative.
    """
    _validate_ratios(ratios)
    if amount < 0:
        raise ValueError("negative amount")

    _log.debug("Distributing %.2f among %d recipients (fee=%.2f)", amount, len(ratios), fee)

    total_ratio = sum(ratios)
    base = [(r / total_ratio) * amount for r in ratios]

    return [_clamp_payout(share - fee) for share in base]
