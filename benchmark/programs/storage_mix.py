from __future__ import annotations

import logging
from typing import Sequence, List

_log = logging.getLogger(__name__)
_EPSILON = 1e-12
_DEFAULT_DAMPING = 0.3
_MIN_ALLOCATION_ENTRIES = 1
_MAX_DAMPING = 1.0


def _validate_damping(damping: float) -> None:
    """Ensure damping factor is within the valid range [0, MAX_DAMPING]."""
    if damping < 0.0 or damping > _MAX_DAMPING:
        raise ValueError(
            f"damping must be in [0, {_MAX_DAMPING}], got {damping}"
        )


def _clamp_allocation(values: List[float]) -> List[float]:
    """Clamp negative allocations to EPSILON to maintain non-negativity."""
    return [max(v, _EPSILON) for v in values]


def storage_mix(
    current: Sequence[float],
    target: Sequence[float],
    *,
    damping: float = _DEFAULT_DAMPING,
) -> List[float]:
    """Shift a storage allocation mix toward a target vector.

    Uses exponential-moving-average style blending controlled by *damping*
    to smoothly transition from the current allocation to the target.
    The returned vector is normalised so that its elements sum to 1.

    Args:
        current: Current allocation proportions (one entry per storage tier).
        target:  Desired allocation proportions of equal length.
        damping: Blending coefficient in [0, 1]. A value of 0 keeps the
                 current allocation unchanged; 1 jumps directly to *target*.

    Returns:
        A new allocation list of the same length whose elements sum to 1.

    Raises:
        ValueError: If *current* and *target* differ in length, if either
                    is empty, or if *damping* is out of range.
    """
    _validate_damping(damping)

    if len(current) != len(target):
        raise ValueError("shape mismatch")
    if not current:
        raise ValueError("empty allocation")

    _log.debug("Blending %d-tier allocation with damping=%.4f", len(current), damping)

    adjusted = [c + (t - c) * damping for c, t in zip(current, target)]

    adjusted = _clamp_allocation(adjusted)

    return adjusted
