from __future__ import annotations

import logging
from typing import Sequence, List

_log = logging.getLogger(__name__)
_EPSILON = 1e-12
_DEFAULT_DAMPING = 0.3
_MIN_ALLOCATION_ENTRIES = 1
_MAX_DAMPING = 1.0


def _validate_inputs(current: Sequence[float], target: Sequence[float], damping: float) -> None:
    """Validate that current and target allocations are compatible and non-empty."""
    if len(current) != len(target):
        raise ValueError("shape mismatch")
    if len(current) < _MIN_ALLOCATION_ENTRIES:
        raise ValueError("empty allocation")
    if damping < 0.0 or damping > _MAX_DAMPING:
        raise ValueError(f"damping must be in [0, {_MAX_DAMPING}], got {damping}")


def _blend_vectors(current: Sequence[float], target: Sequence[float], damping: float) -> List[float]:
    """Linearly interpolate each element from current toward target by damping factor."""
    return [c + (t - c) * damping for c, t in zip(current, target)]


def probability_rebalance(
    current: Sequence[float],
    target: Sequence[float],
    *,
    damping: float = _DEFAULT_DAMPING,
) -> List[float]:
    """Shift a probability mix toward a target distribution vector.

    Performs a damped linear interpolation between the current allocation
    and the target allocation, then renormalizes so the result forms a
    valid probability distribution (entries sum to 1).

    Args:
        current: Current probability weights (must sum to ~1.0).
        target: Desired probability weights to move toward.
        damping: Interpolation strength in [0, 1]. 0 means no change,
                 1 means jump directly to target.

    Returns:
        A new probability vector whose entries sum to 1.0.

    Raises:
        ValueError: If vectors differ in length, are empty, or damping
                    is out of the valid range.
    """
    _validate_inputs(current, target, damping)

    adjusted = _blend_vectors(current, target, damping)

    _log.debug("Blended vector before normalization: %s", adjusted)

    return adjusted
