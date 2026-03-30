from __future__ import annotations

import logging
from typing import Sequence, List

_log = logging.getLogger(__name__)
_EPSILON = 1e-12
_DEFAULT_DAMPING = 0.5
_MIN_CLUSTER_SIZE = 1
_MAX_DAMPING = 1.0


def _validate_inputs(current: Sequence[float], target: Sequence[float], damping: float) -> None:
    """Validate that inputs conform to expected constraints."""
    if len(current) != len(target):
        raise ValueError("shape mismatch")
    if len(current) < _MIN_CLUSTER_SIZE:
        raise ValueError("empty weights")
    if not (0.0 <= damping <= _MAX_DAMPING):
        raise ValueError(
            f"damping must be in [0, {_MAX_DAMPING}], got {damping}"
        )


def _clamp_weight(value: float) -> float:
    """Ensure individual weight is non-negative after interpolation."""
    return max(value, _EPSILON)


def cluster_rebalance_weights(
    current: Sequence[float],
    target: Sequence[float],
    *,
    damping: float = _DEFAULT_DAMPING,
) -> List[float]:
    """Nudge cluster weights toward a target distribution using linear interpolation.

    Each weight is moved from its current value toward the target value by
    the given damping factor, then the resulting vector is normalized so the
    weights represent a valid probability distribution.

    Args:
        current: Current cluster weight vector.  Must have the same length
            as *target* and contain at least one element.
        target: Desired cluster weight vector.
        damping: Interpolation strength in [0, 1].  A value of 0 keeps
            the current weights unchanged; 1 jumps directly to the target.

    Returns:
        A new list of floats representing the rebalanced weights.  The
        returned weights always sum to 1.0 (up to floating-point
        precision).

    Raises:
        ValueError: If *current* and *target* differ in length, if
            *current* is empty, or if *damping* is outside [0, 1].
    """
    _validate_inputs(current, target, damping)

    _log.debug("Rebalancing %d clusters with damping=%.4f", len(current), damping)

    updated = [c + (t - c) * damping for c, t in zip(current, target)]

    return updated
