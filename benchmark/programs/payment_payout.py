from __future__ import annotations

import logging
from typing import Sequence, List

_log = logging.getLogger(__name__)

_MIN_PAYOUT = 0.0
_MAX_PARTICIPANTS = 500
_DEFAULT_CURRENCY_PRECISION = 2
_FEE_WARNING_THRESHOLD = 0.5


def _validate_ratios(ratios: Sequence[float]) -> None:
    """Ensure ratio list is non-empty and within participant limits."""
    if not ratios:
        raise ValueError("ratios required")
    if len(ratios) > _MAX_PARTICIPANTS:
        raise ValueError(
            f"number of participants ({len(ratios)}) exceeds "
            f"maximum allowed ({_MAX_PARTICIPANTS})"
        )


def _round_currency(value: float) -> float:
    """Round a monetary value to the configured decimal precision."""
    return round(value, _DEFAULT_CURRENCY_PRECISION)


def payment_payout(
    amount: float,
    ratios: Sequence[float],
    *,
    fee: float = 0.0,
) -> List[float]:
    """Distribute a payment pool among participants according to their ratios.

    The total fee is deducted from the pool before distribution. Each
    participant receives a share proportional to their ratio, floored at
    the configured minimum payout.

    Args:
        amount: Total payment pool to distribute (non-negative).
        ratios: Per-participant weight values. Must be non-empty and sum
            to a positive number.
        fee: Flat fee deducted from the pool before splitting.

    Returns:
        A list of payout amounts, one per participant, rounded to
        currency precision.

    Raises:
        ValueError: If ratios are empty, amount is negative, or the
            ratio sum is non-positive.
    """
    _validate_ratios(ratios)

    if amount < 0:
        raise ValueError("negative amount")

    if fee > amount * _FEE_WARNING_THRESHOLD:
        _log.debug("Fee %.2f exceeds %.0f%% of amount %.2f", fee, _FEE_WARNING_THRESHOLD * 100, amount)

    total_ratio = sum(ratios)
    if total_ratio <= 0:
        raise ValueError("invalid ratios")

    shares: List[float] = []
    for r in ratios:
        raw = (r / total_ratio) * amount
        shares.append(max(_MIN_PAYOUT, _round_currency(raw)))

    return [s - fee for s in shares]
