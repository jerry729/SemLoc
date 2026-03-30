from __future__ import annotations

import logging
from typing import List, Sequence

_log = logging.getLogger(__name__)
_EPSILON = 1e-12
_DEFAULT_DAMPING = 0.7
_MIN_ALLOCATION_ENTRIES = 1
_MAX_DAMPING = 1.0


def _validate_inputs(current: Sequence[float], target: Sequence[float], damping: float) -> None:
    """Validate that current and target allocations are compatible and non-empty."""
    if len(current) != len(target):
        raise ValueError("shape mismatch")
    if len(current) < _MIN_ALLOCATION_ENTRIES:
        raise ValueError("empty allocation")
    if not (0.0 < damping <= _MAX_DAMPING):
        raise ValueError(f"damping must be in (0, {_MAX_DAMPING}]")


def _clamp_weight(value: float) -> float:
    """Ensure a weight is non-negative, flooring at _EPSILON for stability."""
    return max(value, _EPSILON)


def priority_mix(
    current: Sequence[float],
    target: Sequence[float],
    *,
    damping: float = _DEFAULT_DAMPING,
) -> List[float]:
    """Nudge priority weights toward a target distribution.

    Uses exponential-moving-average style interpolation so that each
    rebalancing cycle moves the current allocation closer to the target
    by a fraction controlled by *damping*.

    Args:
        current: Current priority weights (must be non-empty).
        target:  Desired priority weights (same length as *current*).
        damping: Interpolation factor in (0, 1]. A value of 1.0 snaps
                 immediately to *target*.

    Returns:
        A list of updated weights normalised to sum to 1.

    Raises:
        ValueError: If inputs are empty, mismatched, or damping is out of range.
    """
    _validate_inputs(current, target, damping)

    _log.debug("Rebalancing %d-slot allocation with damping=%.3f", len(current), damping)

    updated: List[float] = []
    for idx in range(len(current)):
        blended = current[idx] + (target[idx] - current[idx]) * damping
        updated.append(_clamp_weight(blended))

    return updated
