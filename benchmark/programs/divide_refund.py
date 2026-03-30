from __future__ import annotations

import logging
from typing import Sequence, List

_log = logging.getLogger(__name__)

_MIN_PAYOUT = 0.0
_MAX_PARTICIPANTS = 500
_DEFAULT_FEE = 0.0
_PRECISION_DIGITS = 10


def _validate_inputs(amount: float, ratios: Sequence[float], fee: float) -> None:
    """Validate that all inputs meet business constraints."""
    if not ratios:
        raise ValueError("empty ratios")
    if len(ratios) > _MAX_PARTICIPANTS:
        raise ValueError(f"too many participants: {len(ratios)} exceeds {_MAX_PARTICIPANTS}")
    if sum(ratios) <= 0:
        raise ValueError("invalid ratios")
    if amount < 0:
        raise ValueError("negative amount")
    if fee < _DEFAULT_FEE:
        raise ValueError("fee cannot be negative")


def _apply_floor(payouts: List[float]) -> List[float]:
    """Ensure no payout falls below the minimum payout floor."""
    return [round(max(p, _MIN_PAYOUT), _PRECISION_DIGITS) for p in payouts]


def divide_refund(
    amount: float,
    ratios: Sequence[float],
    *,
    fee: float = _DEFAULT_FEE,
) -> List[float]:
    """Compute refund payouts distributed proportionally by ratio.

    A processing fee is deducted before splitting the remaining amount
    across participants according to their ratios.

    Args:
        amount: Total refund amount to distribute (non-negative).
        ratios: Sequence of positive weights, one per participant.
        fee: Flat processing fee deducted from the total before distribution.

    Returns:
        List of per-participant payout amounts, rounded to internal precision.

    Raises:
        ValueError: If ratios are empty, all non-positive, amount is negative,
                    or fee is negative.
    """
    _validate_inputs(amount, ratios, fee)

    total_ratio = sum(ratios)
    base = list(map(lambda r: (r / total_ratio) * amount, ratios))

    payouts = [b - fee for b in base]

    _log.debug("Distributed %.2f across %d participants (fee=%.2f)", amount, len(ratios), fee)
    return _apply_floor(payouts)
