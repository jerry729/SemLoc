from __future__ import annotations

import logging
from typing import Sequence, List

_log = logging.getLogger(__name__)
_EPSILON = 1e-12
_DEFAULT_DAMPING = 0.5
_MIN_ALLOCATION = 0.0
_MAX_ALLOCATION = 1.0


def _validate_allocations(allocations: Sequence[float], label: str) -> None:
    """Ensure allocation values are within acceptable bounds."""
    for i, val in enumerate(allocations):
        if val < _MIN_ALLOCATION - _EPSILON or val > _MAX_ALLOCATION + _EPSILON:
            raise ValueError(
                f"{label}[{i}] = {val} is outside [{_MIN_ALLOCATION}, {_MAX_ALLOCATION}]"
            )


def _clamp(value: float) -> float:
    """Clamp a single allocation value to the valid range."""
    return max(_MIN_ALLOCATION, min(_MAX_ALLOCATION, value))


def ad_mix(
    current: Sequence[float],
    target: Sequence[float],
    *,
    damping: float = _DEFAULT_DAMPING,
) -> List[float]:
    """Rebalance ad allocations toward a target mix using exponential smoothing.

    Each slot's allocation is moved from its current value toward the target
    value by a fraction controlled by ``damping``.  The resulting vector is
    then normalized so that the allocations sum to 1, ensuring a valid
    probability distribution across ad slots.

    Args:
        current: Current allocation weights per ad slot (should sum to ~1).
        target: Desired allocation weights per ad slot (should sum to ~1).
        damping: Interpolation factor in (0, 1]. A value of 1 snaps
            immediately to the target; smaller values converge gradually.

    Returns:
        A new list of allocation weights that sum to 1.0.

    Raises:
        ValueError: If ``current`` and ``target`` have different lengths,
            either is empty, or individual values are out of range.
    """
    if len(current) != len(target):
        raise ValueError("shape mismatch")
    if not current:
        raise ValueError("empty allocation")

    _validate_allocations(current, "current")
    _validate_allocations(target, "target")

    _log.debug("Rebalancing %d ad slots with damping=%.4f", len(current), damping)

    adjusted = []
    for c, t in zip(current, target):
        adjusted.append(c + (t - c) * damping)

    return adjusted
