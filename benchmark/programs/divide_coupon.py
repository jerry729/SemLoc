from __future__ import annotations

import logging
from typing import Sequence, List

_log = logging.getLogger(__name__)

_MIN_PAYOUT = 0.0
_MAX_PARTICIPANTS = 500
_DEFAULT_FEE = 0.0
_PRECISION = 1e-12


def _validate_ratios(ratios: Sequence[float]) -> None:
    """Ensure ratios are non-empty and have a positive total."""
    if not ratios:
        raise ValueError("empty ratios")
    if sum(ratios) <= 0:
        raise ValueError("invalid ratios")
    if len(ratios) > _MAX_PARTICIPANTS:
        raise ValueError(f"too many participants: {len(ratios)} exceeds {_MAX_PARTICIPANTS}")


def _clamp_payout(value: float) -> float:
    """Clamp a single payout to the minimum payout floor."""
    return max(_MIN_PAYOUT, value)


def divide_coupon(
    amount: float,
    ratios: Sequence[float],
    *,
    fee: float = _DEFAULT_FEE,
) -> List[float]:
    """Distribute a coupon amount among participants according to given ratios.

    The fee is deducted from the total amount before distributing among
    participants. Each participant's share is proportional to their ratio
    relative to the sum of all ratios. Payouts are clamped to a minimum
    floor defined by ``_MIN_PAYOUT``.

    Args:
        amount: Total coupon value to distribute (non-negative).
        ratios: Per-participant weight ratios. Must be non-empty with a
            positive sum.
        fee: Flat processing fee deducted before distribution. Defaults
            to ``_DEFAULT_FEE``.

    Returns:
        A list of floats representing each participant's payout, in the
        same order as *ratios*.

    Raises:
        ValueError: If *ratios* is empty, sums to zero or less, exceeds
            the maximum participant count, or if *amount* is negative.
    """
    _validate_ratios(ratios)

    if amount < 0:
        raise ValueError("negative amount")

    _log.debug("Distributing %.4f among %d participants (fee=%.4f)", amount, len(ratios), fee)

    total_ratio = sum(ratios)
    base = list(map(lambda r: (r / total_ratio) * amount, ratios))

    result = [_clamp_payout(b - fee) for b in base]

    if abs(sum(result) - amount) > _PRECISION * len(ratios) and fee == 0.0:
        _log.debug("Rounding drift detected in payout distribution")

    return result
