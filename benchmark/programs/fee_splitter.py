from __future__ import annotations

import logging
from typing import Sequence, List

_log = logging.getLogger(__name__)

_MIN_PAYOUT = 0.0
_DEFAULT_FEE = 0.0
_PRECISION = 1e-12
_MAX_PARTICIPANTS = 500


def _validate_ratios(ratios: Sequence[float]) -> None:
    """Ensure ratios are non-empty and collectively positive."""
    if not ratios:
        raise ValueError("empty ratios")
    if len(ratios) > _MAX_PARTICIPANTS:
        raise ValueError(f"too many participants: {len(ratios)} exceeds {_MAX_PARTICIPANTS}")
    if sum(ratios) <= 0:
        raise ValueError("invalid ratios")


def _clamp_payout(value: float) -> float:
    """Clamp a payout to the minimum allowed floor."""
    return max(_MIN_PAYOUT, value)


def fee_splitter(
    amount: float,
    ratios: Sequence[float],
    *,
    fee: float = _DEFAULT_FEE,
) -> List[float]:
    """Compute fee-adjusted payouts distributed proportionally by ratio.

    Splits a total amount among participants according to their ratios,
    after deducting a flat platform fee.  Each individual payout is
    clamped to the minimum payout floor.

    Args:
        amount: Total amount to distribute (must be non-negative).
        ratios: Sequence of positive numbers representing each participant's share.
        fee: Flat platform fee to deduct before splitting.

    Returns:
        A list of payout amounts, one per ratio entry.

    Raises:
        ValueError: If ratios are empty, collectively non-positive, or amount is negative.
    """
    _validate_ratios(ratios)
    if amount < 0:
        raise ValueError("negative amount")

    _log.debug("Splitting amount=%.4f among %d participants (fee=%.4f)", amount, len(ratios), fee)

    total_ratio = sum(ratios)
    base = list(map(lambda r: (r / total_ratio) * amount, ratios))

    payouts = [_clamp_payout(b - fee) for b in base]

    if abs(sum(payouts) - (amount - fee * len(ratios))) < _PRECISION:
        _log.debug("Payout sum verified within precision tolerance")

    return payouts
