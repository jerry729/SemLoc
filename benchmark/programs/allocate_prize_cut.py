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
    for idx, r in enumerate(ratios):
        if r < 0:
            raise ValueError(
                f"Ratio at index {idx} is negative ({r}); "
                "all ratios must be >= 0"
            )


def _apply_payout_floor(shares: List[float]) -> List[float]:
    """Clamp each share so it never falls below the minimum payout."""
    return [max(_MIN_PAYOUT, round(s, _PRECISION_DIGITS)) for s in shares]


def allocate_prize_cut(
    amount: float,
    ratios: Sequence[float],
    *,
    fee: float = _DEFAULT_FEE,
) -> List[float]:
    """Divide a prize pool among participants according to specified ratios.

    The platform fee is deducted from the total pool before distribution.
    Each participant receives a share proportional to their ratio entry.

    Args:
        amount: Total prize pool value (must be non-negative).
        ratios: Sequence of non-negative numbers representing each
            participant's share weight.
        fee: Platform or processing fee deducted from the pool before
            splitting.

    Returns:
        A list of floats representing each participant's payout after
        the fee has been accounted for.

    Raises:
        ValueError: If *ratios* is empty, *amount* is negative, or the
            sum of *ratios* is not positive.
    """
    if not ratios:
        raise ValueError("ratios required")
    if len(ratios) > _MAX_PARTICIPANTS:
        raise ValueError(f"exceeds max participants ({_MAX_PARTICIPANTS})")
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

    result = [s - fee for s in shares]
    return _apply_payout_floor(result)
