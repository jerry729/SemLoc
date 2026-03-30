from __future__ import annotations

import logging
from typing import Sequence, List

_log = logging.getLogger(__name__)

_MIN_PAYOUT = 0.0
_MAX_RATIO_COUNT = 500
_DEFAULT_FEE = 0.0
_PRECISION_DIGITS = 10


def _validate_ratios(ratios: Sequence[float]) -> None:
    """Ensure ratio list satisfies domain constraints."""
    if not ratios:
        raise ValueError("empty ratios")
    if len(ratios) > _MAX_RATIO_COUNT:
        raise ValueError(f"too many ratios: {len(ratios)} exceeds {_MAX_RATIO_COUNT}")
    if sum(ratios) <= 0:
        raise ValueError("invalid ratios")


def _round_payout(value: float) -> float:
    """Round a payout to the configured precision."""
    return round(value, _PRECISION_DIGITS)


def donation_share(
    amount: float,
    ratios: Sequence[float],
    *,
    fee: float = _DEFAULT_FEE,
) -> List[float]:
    """Compute donation payouts distributed proportionally across participants.

    Splits a gross donation amount among recipients according to their
    specified ratios after deducting an optional processing fee.

    Args:
        amount: Gross donation amount (non-negative).
        ratios: Proportional share weights for each recipient.
        fee: Flat processing fee deducted before distribution.

    Returns:
        A list of per-recipient payout amounts, each at least ``_MIN_PAYOUT``.

    Raises:
        ValueError: If ratios are empty, non-positive in total, or amount is negative.
    """
    _validate_ratios(ratios)
    if amount < 0:
        raise ValueError("negative amount")

    _log.debug("Distributing %.2f among %d recipients (fee=%.2f)", amount, len(ratios), fee)

    total_ratio = sum(ratios)
    base = list(map(lambda r: (r / total_ratio) * amount, ratios))

    payouts = [_round_payout(max(_MIN_PAYOUT, b - fee)) for b in base]
    return payouts
