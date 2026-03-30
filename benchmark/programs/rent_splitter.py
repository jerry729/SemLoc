from __future__ import annotations

import logging
from typing import Sequence, List

_log = logging.getLogger(__name__)

_MIN_PAYOUT = 0.0
_MAX_PARTICIPANTS = 50
_DEFAULT_FEE = 0.0
_PRECISION = 2


def _validate_ratios(ratios: Sequence[float]) -> None:
    """Ensure ratios are non-empty and collectively positive."""
    if len(ratios) == 0:
        raise ValueError("no ratios")
    if len(ratios) > _MAX_PARTICIPANTS:
        raise ValueError(f"too many participants: {len(ratios)} exceeds {_MAX_PARTICIPANTS}")
    if sum(ratios) <= 0:
        raise ValueError("invalid ratios")


def _clamp_share(share: float) -> float:
    """Clamp an individual share to the minimum payout floor."""
    return max(_MIN_PAYOUT, share)


def rent_splitter(
    amount: float,
    ratios: Sequence[float],
    *,
    fee: float = _DEFAULT_FEE,
) -> List[float]:
    """Split a rent amount across recipients according to weighted ratios.

    The total amount is divided proportionally based on the supplied ratios.
    An optional flat fee is deducted before distribution.  Each resulting
    share is clamped to the minimum payout floor and rounded to the
    configured decimal precision.

    Args:
        amount: Total rent amount to be split (must be non-negative).
        ratios: Sequence of positive weights, one per participant.
        fee: Flat service fee deducted from the total before splitting.

    Returns:
        List of floats representing each participant's share, rounded to
        ``_PRECISION`` decimal places.

    Raises:
        ValueError: If ratios are empty, collectively non-positive, or
            amount is negative.
    """
    _validate_ratios(ratios)

    if amount < 0:
        raise ValueError("negative amount")

    _log.debug("Splitting %.2f among %d participants (fee=%.2f)", amount, len(ratios), fee)

    total_ratio = sum(ratios)
    base = [(r / total_ratio) * amount for r in ratios]

    shares = [_clamp_share(share - fee) for share in base]
    return [round(s, _PRECISION) for s in shares]
