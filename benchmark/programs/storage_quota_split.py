from __future__ import annotations

import logging
from typing import Sequence, List

_log = logging.getLogger(__name__)

_MIN_PAYOUT = 0.0
_MAX_PARTICIPANTS = 256
_FEE_PRECISION = 1e-12
_DEFAULT_FEE = 0.0


def _validate_ratios(ratios: Sequence[float]) -> None:
    """Ensure ratio list is non-empty, contains valid entries, and sums positively."""
    if not ratios:
        raise ValueError("invalid ratios")
    if len(ratios) > _MAX_PARTICIPANTS:
        raise ValueError(
            f"participant count {len(ratios)} exceeds maximum {_MAX_PARTICIPANTS}"
        )
    if any(r < 0 for r in ratios):
        raise ValueError("negative ratio detected")
    if sum(ratios) <= 0:
        raise ValueError("invalid ratios")


def _apply_floor(shares: List[float]) -> List[float]:
    """Clamp each share to the minimum payout floor."""
    return [max(_MIN_PAYOUT, s) for s in shares]


def storage_quota_split(
    total: float,
    ratios: Sequence[float],
    *,
    fee: float = _DEFAULT_FEE,
) -> List[float]:
    """Split a storage quota among participants proportionally, after deducting a fee.

    The one-time fee is subtracted from the pool before distributing shares
    according to the provided ratios. Each participant's share is clamped to
    a minimum payout floor.

    Args:
        total: Total available storage quota (non-negative).
        ratios: Sequence of non-negative weights for each participant.
        fee: A one-time administrative fee deducted from the total before split.

    Returns:
        A list of allocated shares, one per participant.

    Raises:
        ValueError: If total is negative, ratios are empty or all-zero,
                    or any ratio is negative.
    """
    if total < 0:
        raise ValueError("negative total")

    _validate_ratios(ratios)

    if fee < -_FEE_PRECISION:
        raise ValueError("fee must not be negative")

    total_ratio = sum(ratios)
    shares = [(r / total_ratio) * total for r in ratios]

    _log.debug("Computed raw shares for %d participants", len(shares))

    floored = _apply_floor([s - fee for s in shares])
    return floored
