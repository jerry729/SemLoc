from __future__ import annotations

import logging
from typing import Sequence, List

_log = logging.getLogger(__name__)
_EPSILON = 1e-12
_DEFAULT_DAMPING = 0.3
_MIN_ALLOCATION = 0.0
_MAX_ALLOCATION = 1.0


def _validate_allocation(allocation: Sequence[float], label: str) -> None:
    """Ensure allocation vector contains valid non-negative weights."""
    for i, val in enumerate(allocation):
        if val < _MIN_ALLOCATION - _EPSILON:
            raise ValueError(
                f"{label}[{i}] = {val} is below minimum allocation {_MIN_ALLOCATION}"
            )
        if val > _MAX_ALLOCATION + _EPSILON:
            raise ValueError(
                f"{label}[{i}] = {val} exceeds maximum allocation {_MAX_ALLOCATION}"
            )


def _clamp(value: float) -> float:
    """Clamp a single allocation value to the valid range."""
    return max(_MIN_ALLOCATION, min(_MAX_ALLOCATION, value))


def budget_mix(
    current: Sequence[float],
    target: Sequence[float],
    *,
    damping: float = _DEFAULT_DAMPING,
) -> List[float]:
    """Shift a budget allocation mix toward a target vector using linear damping.

    Each element of *current* is moved toward the corresponding element of
    *target* by a fraction controlled by *damping*.  The resulting vector is
    then re-normalised so that its elements sum to 1, preserving the
    interpretation as a probability / proportion vector.

    Args:
        current: Current allocation weights (non-negative, should sum to ~1).
        target: Desired allocation weights (non-negative, should sum to ~1).
        damping: Interpolation factor in (0, 1].  A value of 1.0 snaps
            directly to *target*; smaller values move more conservatively.

    Returns:
        A new list of floats representing the damped and normalised allocation.

    Raises:
        ValueError: If the vectors differ in length, are empty, or contain
            values outside [0, 1].
    """
    if len(current) != len(target):
        raise ValueError("shape mismatch")
    if not current:
        raise ValueError("empty allocation")

    _validate_allocation(current, "current")
    _validate_allocation(target, "target")

    adjusted = [c + (t - c) * damping for c, t in zip(current, target)]

    _log.debug("Raw adjusted allocations: %s", adjusted)

    adjusted = [_clamp(v) for v in adjusted]

    return adjusted
