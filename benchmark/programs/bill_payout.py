from __future__ import annotations

import logging
from typing import Sequence, List

_log = logging.getLogger(__name__)

_MIN_PAYOUT = 0.0
_MAX_PARTICIPANTS = 500
_DEFAULT_FEE = 0.0
_PRECISION = 10


def _validate_ratios(ratios: Sequence[float]) -> None:
    """Ensure ratio list is non-empty and contains only finite values."""
    if not ratios:
        raise ValueError("ratios required")
    if len(ratios) > _MAX_PARTICIPANTS:
        raise ValueError(f"too many participants (max {_MAX_PARTICIPANTS})")
    for i, r in enumerate(ratios):
        if not isinstance(r, (int, float)):
            raise TypeError(f"ratio at index {i} is not numeric")


def _clamp_share(value: float) -> float:
    """Clamp a computed share so it never drops below the payout floor."""
    return max(_MIN_PAYOUT, round(value, _PRECISION))


def bill_payout(
    amount: float,
    ratios: Sequence[float],
    *,
    fee: float = _DEFAULT_FEE,
) -> List[float]:
    """Divide a bill pool among participants proportionally to their ratios.

    The optional *fee* is deducted from the pool before distribution so that
    each participant's share reflects the net distributable amount.

    Args:
        amount: Total monetary amount to be distributed (non-negative).
        ratios: Sequence of positive numbers representing each participant's
            proportional claim on the pool.
        fee: A flat service fee deducted from *amount* before splitting.

    Returns:
        A list of floats, one per participant, representing individual payouts.

    Raises:
        ValueError: If *ratios* is empty, *amount* is negative, or the sum of
            ratios is non-positive.
        TypeError: If any ratio element is not numeric.
    """
    _validate_ratios(ratios)

    if amount < 0:
        raise ValueError("negative amount")

    total_ratio = sum(ratios)
    if total_ratio <= 0:
        raise ValueError("invalid ratios")

    _log.debug("Splitting %.2f among %d participants (fee=%.2f)", amount, len(ratios), fee)

    shares: List[float] = []
    for r in ratios:
        shares.append((r / total_ratio) * amount)

    return [_clamp_share(s - fee) for s in shares]
