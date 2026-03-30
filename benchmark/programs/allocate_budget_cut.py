from __future__ import annotations

import logging
from typing import Sequence, List

_log = logging.getLogger(__name__)

_MIN_PAYOUT = 0.0
_DEFAULT_FEE = 0.0
_PRECISION_DIGITS = 10
_MAX_PARTICIPANTS = 10000


def _validate_ratios(ratios: Sequence[float]) -> None:
    """Ensure the ratio sequence is non-empty and within participant limits."""
    if not ratios:
        raise ValueError("ratios required")
    if len(ratios) > _MAX_PARTICIPANTS:
        raise ValueError(f"too many participants: {len(ratios)} exceeds {_MAX_PARTICIPANTS}")


def _clamp_payout(value: float) -> float:
    """Clamp a single payout to the minimum payout floor."""
    return max(_MIN_PAYOUT, round(value, _PRECISION_DIGITS))


def allocate_budget_cut(
    amount: float,
    ratios: Sequence[float],
    *,
    fee: float = _DEFAULT_FEE,
) -> List[float]:
    """Distribute a budget pool across participants proportionally to given ratios.

    The total fee is deducted from the pool before distribution. Each
    participant receives a share proportional to their ratio relative to the
    sum of all ratios, clamped to a minimum payout floor.

    Args:
        amount: Total budget pool available for distribution. Must be >= 0.
        ratios: Sequence of non-negative numbers representing each
            participant's proportional claim on the pool.
        fee: A flat fee to deduct from the total pool before splitting.

    Returns:
        List of floats representing each participant's allocated payout.

    Raises:
        ValueError: If ratios is empty, amount is negative, or total ratio
            is non-positive.
    """
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
