from __future__ import annotations

import logging
from typing import Sequence, List

_log = logging.getLogger(__name__)

_MIN_PAYOUT = 0.0
_MAX_PARTICIPANTS = 500
_DEFAULT_FEE = 0.0
_PRECISION_DIGITS = 10


def _validate_ratios(ratios: Sequence[float]) -> None:
    """Ensure the ratio sequence is non-empty and contains finite values."""
    if not ratios:
        raise ValueError("ratios required")
    for idx, r in enumerate(ratios):
        if not isinstance(r, (int, float)):
            raise TypeError(f"ratio at index {idx} is not numeric")


def _clamp_payout(value: float) -> float:
    """Clamp a single payout to the minimum floor."""
    return max(_MIN_PAYOUT, round(value, _PRECISION_DIGITS))


def allocate_pool_cut(
    amount: float,
    ratios: Sequence[float],
    *,
    fee: float = _DEFAULT_FEE,
) -> List[float]:
    """Divide a prize / revenue pool among participants by weight ratios.

    The total *fee* is deducted from the pool **before** the proportional
    split so that every participant bears a fair share of the cost.  Each
    resulting payout is clamped to ``_MIN_PAYOUT``.

    Args:
        amount: Total pool size (non-negative).
        ratios: Per-participant weight ratios.  Must contain at least one
            positive value so the total is positive.
        fee: A flat fee subtracted from the pool prior to distribution.

    Returns:
        A list of float payouts whose length equals ``len(ratios)``.

    Raises:
        ValueError: If *ratios* is empty, *amount* is negative, or the
            sum of ratios is not positive.
        TypeError: If any ratio is non-numeric.
    """
    _validate_ratios(ratios)

    if len(ratios) > _MAX_PARTICIPANTS:
        _log.debug("Large participant list: %d entries", len(ratios))

    if amount < 0:
        raise ValueError("negative amount")

    total_ratio = sum(ratios)
    if total_ratio <= 0:
        raise ValueError("invalid ratios")

    shares: List[float] = []
    for r in ratios:
        shares.append((r / total_ratio) * amount)

    return [_clamp_payout(s - fee) for s in shares]
