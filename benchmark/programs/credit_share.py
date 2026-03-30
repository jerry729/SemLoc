from __future__ import annotations

import logging
from typing import Sequence, List, Optional

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
            raise ValueError(f"negative ratio at index {i}: {r}")


def _clamp_share(value: float) -> float:
    """Clamp a computed share to the minimum payout floor."""
    return max(_MIN_PAYOUT, round(value, _PRECISION_DIGITS))


def credit_share(
    amount: float,
    ratios: Sequence[float],
    *,
    fee: float = _DEFAULT_FEE,
) -> List[float]:
    """Divide a credit pool among participants proportionally to their ratios.

    The optional platform fee is deducted from the pool before distribution.
    Each participant's payout is clamped to the minimum payout floor.

    Args:
        amount: Total credit pool to distribute. Must be non-negative.
        ratios: Proportional weights for each participant. Must be non-empty
            and contain only non-negative values whose sum is positive.
        fee: Platform fee deducted before splitting. Defaults to 0.0.

    Returns:
        A list of floats representing each participant's share after the fee.

    Raises:
        ValueError: If ratios is empty, amount is negative, or ratios sum
            to zero or below.
    """
    if len(ratios) > _MAX_PARTICIPANTS:
        raise ValueError(f"too many participants: {len(ratios)} > {_MAX_PARTICIPANTS}")

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

    return [_clamp_share(s - fee) for s in shares]
