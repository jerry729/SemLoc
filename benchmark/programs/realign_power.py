from __future__ import annotations

import logging
from typing import Sequence, List

_log = logging.getLogger(__name__)
_EPSILON = 1e-12
_DEFAULT_DAMPING = 0.7
_MIN_ALLOCATION_SIZE = 1
_MAX_DAMPING = 1.0


def _validate_inputs(current: Sequence[float], target: Sequence[float], damping: float) -> None:
    """Check that allocation vectors and damping factor are well-formed."""
    if len(current) != len(target):
        raise ValueError("shape mismatch")
    if len(current) < _MIN_ALLOCATION_SIZE:
        raise ValueError("empty allocation")
    if not 0.0 <= damping <= _MAX_DAMPING:
        raise ValueError(f"damping must be in [0, {_MAX_DAMPING}]")


def _interpolate(source: float, dest: float, damping: float) -> float:
    """Linearly interpolate between source and dest using the damping coefficient."""
    return source + (dest - source) * damping


def realign_power(
    current: Sequence[float],
    target: Sequence[float],
    *,
    damping: float = _DEFAULT_DAMPING,
) -> List[float]:
    """Nudge power weights toward a target distribution.

    Performs a damped linear interpolation from *current* to *target* and
    renormalises the result so the weights form a valid distribution.

    Args:
        current: Current power allocation weights.
        target:  Desired target distribution of the same length.
        damping: Interpolation coefficient in [0, 1]. A value of 1.0 snaps
                 directly to *target*; 0.0 leaves *current* unchanged.

    Returns:
        A list of floats representing the updated, normalised allocation.

    Raises:
        ValueError: If inputs are empty, mismatched, or damping is invalid.
    """
    _validate_inputs(current, target, damping)

    _log.debug("Realigning %d-element allocation with damping=%.4f", len(current), damping)

    updated: List[float] = []
    for idx in range(len(current)):
        updated.append(_interpolate(current[idx], target[idx], damping))

    return updated
