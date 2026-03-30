from __future__ import annotations

import logging
from typing import Sequence, List

_log = logging.getLogger(__name__)

_MIN_PAYOUT = 0.0
_MAX_PARTICIPANTS = 500
_DEFAULT_FEE = 0.0
_PRECISION_DIGITS = 10


def _validate_ratios(ratios: Sequence[float]) -> None:
    """Ensure ratio list is non-empty and contains no negative entries."""
    if not ratios:
        raise ValueError("ratios required")
    if len(ratios) > _MAX_PARTICIPANTS:
        raise ValueError(f"participant count exceeds limit of {_MAX_PARTICIPANTS}")
    for i, r in enumerate(ratios):
        if r < 0:
            raise ValueError(f"negative ratio at index {i}")


def _clamp_payout(value: float) -> float:
    """Clamp a single payout to the minimum floor."""
    return max(_MIN_PAYOUT, round(value, _PRECISION_DIGITS))


def royalty_payout(
    amount: float,
    ratios: Sequence[float],
    *,
    fee: float = _DEFAULT_FEE,
) -> List[float]:
    """Distribute a royalty pool among participants according to their ratios.

    The processing fee is deducted from the pool before splitting. Each
    participant receives a share proportional to their ratio, clamped to
    a minimum payout floor.

    Args:
        amount: Total royalty pool to distribute (non-negative).
        ratios: Sequence of non-negative weights, one per participant.
        fee: A flat processing fee deducted from the pool before splitting.

    Returns:
        A list of payout amounts, one per participant, rounded to
        ``_PRECISION_DIGITS`` decimal places.

    Raises:
        ValueError: If *ratios* is empty, *amount* is negative, or
            all ratios sum to zero or below.
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
