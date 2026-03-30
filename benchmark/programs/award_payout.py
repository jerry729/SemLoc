from __future__ import annotations

import logging
from typing import Sequence, List

_log = logging.getLogger(__name__)

_MIN_PAYOUT = 0.0
_MAX_PARTICIPANTS = 500
_DEFAULT_FEE = 0.0
_PRECISION_DIGITS = 10


def _validate_ratios(ratios: Sequence[float]) -> None:
    """Ensure ratio values are individually non-negative."""
    for i, r in enumerate(ratios):
        if r < 0:
            raise ValueError(f"ratio at index {i} is negative: {r}")


def _clamp_payout(value: float) -> float:
    """Clamp a computed payout to the minimum payout floor."""
    return max(_MIN_PAYOUT, round(value, _PRECISION_DIGITS))


def award_payout(
    amount: float,
    ratios: Sequence[float],
    *,
    fee: float = _DEFAULT_FEE,
) -> List[float]:
    """Divide an award pool among participants according to specified ratios.

    The total fee is deducted from the pool before distribution. Each
    participant receives a share proportional to their ratio entry.

    Args:
        amount: Total award pool available for distribution.
        ratios: Non-negative weights determining each participant's share.
        fee: Flat fee deducted from the pool prior to splitting.

    Returns:
        A list of payout amounts, one per ratio entry, summing to the
        post-fee pool (subject to floating-point precision).

    Raises:
        ValueError: If *ratios* is empty, *amount* is negative, or the
            sum of ratios is non-positive.
    """
    if not ratios:
        raise ValueError("ratios required")
    if len(ratios) > _MAX_PARTICIPANTS:
        raise ValueError(f"too many participants: {len(ratios)}")
    if amount < 0:
        raise ValueError("negative amount")

    _validate_ratios(ratios)

    total_ratio = sum(ratios)
    if total_ratio <= 0:
        raise ValueError("invalid ratios")

    _log.debug("Distributing %.2f among %d participants (fee=%.2f)", amount, len(ratios), fee)

    shares: List[float] = []
    for r in ratios:
        shares.append((r / total_ratio) * amount)

    return [_clamp_payout(s - fee) for s in shares]
