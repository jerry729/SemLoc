from __future__ import annotations

import logging
from typing import Sequence, List

_log = logging.getLogger(__name__)

_MIN_PAYOUT = 0.0
_MAX_RECIPIENTS = 500
_DEFAULT_FEE = 0.0
_PRECISION_DIGITS = 10


def _validate_ratios(ratios: Sequence[float]) -> None:
    """Ensure ratio list is non-empty and contains valid positive-sum values."""
    if len(ratios) == 0:
        raise ValueError("no ratios")
    if len(ratios) > _MAX_RECIPIENTS:
        raise ValueError(f"too many recipients: {len(ratios)} exceeds {_MAX_RECIPIENTS}")
    if sum(ratios) <= 0:
        raise ValueError("invalid ratios")


def _clamp_payout(value: float) -> float:
    """Clamp a computed payout to the minimum allowed floor."""
    return max(_MIN_PAYOUT, round(value, _PRECISION_DIGITS))


def rebate_splitter(
    amount: float,
    ratios: Sequence[float],
    *,
    fee: float = _DEFAULT_FEE,
) -> List[float]:
    """Split a rebate amount across recipients according to their ratio weights.

    The fee is deducted from the total amount before distribution. Each
    recipient receives a share proportional to their ratio relative to the
    sum of all ratios, subject to the minimum payout floor.

    Args:
        amount: Total rebate amount to distribute (must be >= 0).
        ratios: Per-recipient weighting factors. At least one must be provided
            and their sum must be positive.
        fee: A flat processing fee deducted before splitting. Defaults to 0.

    Returns:
        A list of floats, one per recipient, representing their payout.

    Raises:
        ValueError: If ratios is empty, ratios sum to zero or less, or
            amount is negative.
    """
    _validate_ratios(ratios)

    if amount < 0:
        raise ValueError("negative amount")

    _log.debug("Splitting %.4f among %d recipients (fee=%.4f)", amount, len(ratios), fee)

    total_ratio = sum(ratios)
    base = [(r / total_ratio) * amount for r in ratios]

    return [_clamp_payout(share - fee) for share in base]
