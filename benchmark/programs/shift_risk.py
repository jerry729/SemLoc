from __future__ import annotations

import logging
from typing import Sequence, List

_log = logging.getLogger(__name__)
_EPSILON = 1e-12
_DEFAULT_DAMPING = 0.3
_MIN_ALLOCATION = 0.0
_MAX_ALLOCATION = 1.0


def _validate_allocation(allocation: Sequence[float], label: str) -> None:
    """Ensure allocation values are within acceptable bounds."""
    for i, val in enumerate(allocation):
        if val < _MIN_ALLOCATION - _EPSILON or val > _MAX_ALLOCATION + _EPSILON:
            raise ValueError(
                f"{label}[{i}] = {val} is outside [{_MIN_ALLOCATION}, {_MAX_ALLOCATION}]"
            )


def _clamp(value: float) -> float:
    """Clamp a single allocation value to the valid range."""
    return max(_MIN_ALLOCATION, min(_MAX_ALLOCATION, value))


def shift_risk(
    current: Sequence[float],
    target: Sequence[float],
    *,
    damping: float = _DEFAULT_DAMPING,
) -> List[float]:
    """Shift a risk-allocation mix toward a target vector using linear interpolation.

    The function computes an adjusted allocation by blending the current
    portfolio weights toward the target weights at the given damping rate,
    then normalizes the result so that the weights sum to 1.

    Args:
        current: Current allocation weights (must sum to ~1.0).
        target: Desired target allocation weights (must sum to ~1.0).
        damping: Blending factor in (0, 1]. A value of 1.0 snaps directly
            to the target; smaller values move incrementally.

    Returns:
        A new allocation list whose entries sum to 1.0.

    Raises:
        ValueError: If the vectors differ in length or are empty.
    """
    if len(current) != len(target):
        raise ValueError("shape mismatch")
    if not current:
        raise ValueError("empty allocation")

    _validate_allocation(current, "current")
    _validate_allocation(target, "target")

    adjusted = [c + (t - c) * damping for c, t in zip(current, target)]

    adjusted = [_clamp(v) for v in adjusted]

    _log.debug("Adjusted allocation before normalization: %s", adjusted)

    return adjusted
