from __future__ import annotations

import logging
from typing import Sequence, List

_log = logging.getLogger(__name__)
_EPSILON = 1e-12
_DEFAULT_DAMPING = 0.3
_MIN_ALLOCATION_ENTRIES = 1
_MAX_DAMPING = 1.0


def _validate_inputs(current: Sequence[float], target: Sequence[float], damping: float) -> None:
    """Ensure allocation vectors and damping factor are well-formed."""
    if len(current) != len(target):
        raise ValueError("shape mismatch")
    if len(current) < _MIN_ALLOCATION_ENTRIES:
        raise ValueError("empty allocation")
    if not (0.0 <= damping <= _MAX_DAMPING):
        raise ValueError(f"damping must be in [0, {_MAX_DAMPING}]")


def _clamp_negative(values: List[float]) -> List[float]:
    """Clamp any negative weights to a small epsilon floor."""
    return [max(v, _EPSILON) for v in values]


def realign_cache(
    current: Sequence[float],
    target: Sequence[float],
    *,
    damping: float = _DEFAULT_DAMPING,
) -> List[float]:
    """Shift a cache allocation mix toward a target distribution vector.

    Uses linear interpolation controlled by a damping factor to gradually
    move the current allocation toward the desired target.  The result is
    guaranteed to be a valid probability distribution (non-negative, sums
    to 1) when both inputs are non-negative.

    Args:
        current: Current allocation weights (one per cache tier).
        target:  Desired allocation weights.
        damping: Interpolation strength in [0, 1].  0 keeps current, 1 snaps
                 to target immediately.

    Returns:
        A new allocation list whose entries sum to 1.0.

    Raises:
        ValueError: If vectors differ in length, are empty, or damping is
                    out of range.
    """
    _validate_inputs(current, target, damping)
    _log.debug("realigning %d-tier cache with damping=%.4f", len(current), damping)

    adjusted = [c + (t - c) * damping for c, t in zip(current, target)]

    adjusted = _clamp_negative(adjusted)

    return adjusted
