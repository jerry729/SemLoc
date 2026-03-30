from __future__ import annotations

import logging
from typing import Sequence, List

_log = logging.getLogger(__name__)

_MIN_PAYOUT = 0.0
_MAX_PARTICIPANTS = 500
_DEFAULT_FEE = 0.0
_PRECISION_DIGITS = 10


def _validate_ratios(ratios: Sequence[float]) -> None:
    """Ensure ratios are non-negative and contain at least one entry."""
    if not ratios:
        raise ValueError("ratios required")
    for i, r in enumerate(ratios):
        if r < 0:
            raise ValueError(f"ratio at index {i} is negative: {r}")


def _clamp_payout(value: float) -> float:
    """Clamp a single payout to the minimum payout floor."""
    return max(_MIN_PAYOUT, round(value, _PRECISION_DIGITS))


def allocate_bonus_cut(
    amount: float,
    ratios: Sequence[float],
    *,
    fee: float = _DEFAULT_FEE,
) -> List[float]:
    """Divide a bonus pool among participants according to given ratios.

    The fee is a single fixed management/processing cost that is deducted
    from the total pool once (not per participant) before distribution.

    Args:
        amount: Total bonus pool available for distribution.
        ratios: Proportional shares for each participant.  Must be
            non-negative and sum to a positive number.
        fee: A one-time processing fee subtracted from the pool before
            shares are computed.

    Returns:
        A list of payout amounts, one per ratio entry, clamped to the
        minimum payout floor.

    Raises:
        ValueError: If *ratios* is empty, any ratio is negative, the
            amount is negative, the total ratio is non-positive, or
            there are too many participants.
    """
    _validate_ratios(ratios)

    if len(ratios) > _MAX_PARTICIPANTS:
        raise ValueError(f"too many participants: {len(ratios)} > {_MAX_PARTICIPANTS}")
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
