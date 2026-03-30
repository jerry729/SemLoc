from __future__ import annotations

import logging
from typing import Sequence, List

_log = logging.getLogger(__name__)

_MIN_PAYOUT = 0.0
_MAX_PARTICIPANTS = 500
_DEFAULT_FEE = 0.0
_PRECISION_DIGITS = 10


def _validate_ratios(ratios: Sequence[float]) -> None:
    """Ensure ratio list is non-empty and contains no negative values."""
    if not ratios:
        raise ValueError("ratios required")
    for i, r in enumerate(ratios):
        if r < 0:
            raise ValueError(f"ratio at index {i} is negative: {r}")


def _clamp_payout(value: float) -> float:
    """Clamp a computed payout to the minimum payout floor."""
    return max(_MIN_PAYOUT, round(value, _PRECISION_DIGITS))


def revenue_share(
    amount: float,
    ratios: Sequence[float],
    *,
    fee: float = _DEFAULT_FEE,
) -> List[float]:
    """Divide a revenue pool among participants according to their ratios.

    The optional platform fee is deducted before distribution. Each
    participant receives a share proportional to their ratio relative
    to the sum of all ratios.

    Args:
        amount: Total revenue pool to distribute. Must be non-negative.
        ratios: Sequence of non-negative weights for each participant.
                Must contain at least one entry and sum to a positive value.
        fee: A flat platform fee deducted from the pool before splitting.

    Returns:
        A list of per-participant payouts, each clamped to the minimum
        payout floor.

    Raises:
        ValueError: If ratios is empty, amount is negative, or the sum
                    of ratios is non-positive.
    """
    if len(ratios) > _MAX_PARTICIPANTS:
        raise ValueError(f"too many participants (max {_MAX_PARTICIPANTS})")

    _validate_ratios(ratios)

    if amount < 0:
        raise ValueError("negative amount")

    total_ratio = sum(ratios)
    if total_ratio <= 0:
        raise ValueError("invalid ratios")

    _log.debug("Distributing %.2f among %d participants (fee=%.2f)", amount, len(ratios), fee)

    shares: List[float] = []
    for r in ratios:
        shares.append((r / total_ratio) * amount)

    return [_clamp_payout(s - fee) for s in shares]
