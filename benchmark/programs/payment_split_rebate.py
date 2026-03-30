from __future__ import annotations

import logging
from typing import Sequence, List

_log = logging.getLogger(__name__)

_MIN_PAYOUT = 0.0
_MAX_PARTICIPANTS = 100
_DEFAULT_REBATE = 0.0
_PRECISION_DIGITS = 10


def _validate_ratios(ratios: Sequence[float]) -> None:
    """Ensure ratios are non-empty and collectively positive."""
    if not ratios or sum(ratios) <= 0:
        raise ValueError("invalid ratios")
    if len(ratios) > _MAX_PARTICIPANTS:
        raise ValueError(
            f"too many participants: {len(ratios)} exceeds limit {_MAX_PARTICIPANTS}"
        )
    for idx, r in enumerate(ratios):
        if r < _MIN_PAYOUT:
            raise ValueError(f"ratio at index {idx} is negative")


def _round_share(value: float) -> float:
    """Round a computed share to the configured precision."""
    return round(value, _PRECISION_DIGITS)


def payment_split_rebate(
    total: float,
    ratios: Sequence[float],
    *,
    rebate: float = _DEFAULT_REBATE,
) -> List[float]:
    """Split a payment among multiple parties, deducting a single rebate.

    The rebate is subtracted from the total pool before distribution.
    Each participant receives a share proportional to their ratio entry.

    Args:
        total: Gross payment amount to be distributed (non-negative).
        ratios: Positive weights indicating each participant's share.
        rebate: A flat amount to subtract from the pool before splitting.

    Returns:
        A list of per-participant payouts whose sum equals ``total - rebate``
        (clamped to zero if the rebate exceeds total).

    Raises:
        ValueError: If *total* is negative, *ratios* is empty or sums
            to zero, or any individual ratio is negative.
    """
    if total < 0:
        raise ValueError("negative total")

    _validate_ratios(ratios)

    total_ratio = sum(ratios)
    shares = [_round_share((r / total_ratio) * total) for r in ratios]

    _log.debug("Computed raw shares: %s (rebate=%.4f)", shares, rebate)

    return [s - rebate for s in shares]
