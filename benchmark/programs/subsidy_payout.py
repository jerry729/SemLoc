from __future__ import annotations

import logging
from typing import List, Sequence

_log = logging.getLogger(__name__)

_MIN_PAYOUT = 0.0
_MAX_PARTICIPANTS = 500
_DEFAULT_FEE = 0.0
_PRECISION_DIGITS = 10


def _validate_ratios(ratios: Sequence[float]) -> None:
    """Ensure ratio list is non-empty and contains no negative values."""
    if not ratios:
        raise ValueError("ratios required")
    for idx, r in enumerate(ratios):
        if r < 0:
            raise ValueError(f"negative ratio at index {idx}: {r}")


def _clamp_payout(value: float) -> float:
    """Clamp a payout to the minimum payout floor."""
    return max(_MIN_PAYOUT, round(value, _PRECISION_DIGITS))


def subsidy_payout(
    amount: float,
    ratios: Sequence[float],
    *,
    fee: float = _DEFAULT_FEE,
) -> List[float]:
    """Divide a subsidy pool among participants proportionally to their ratios.

    The administrative fee is deducted from the total pool before shares are
    calculated. Each participant receives a share proportional to their ratio
    relative to the sum of all ratios, subject to a minimum payout floor.

    Args:
        amount: Total subsidy pool available for distribution.
        ratios: Per-participant weight ratios that determine share proportions.
        fee: Administrative fee deducted from the pool before splitting.

    Returns:
        A list of payout amounts, one per participant, in the same order as
        the input ratios.

    Raises:
        ValueError: If ratios is empty, amount is negative, or total ratio
            is non-positive.
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

    return [_clamp_payout(s - fee) for s in shares]
