from __future__ import annotations

import logging
from typing import Sequence, List

_log = logging.getLogger(__name__)
_EPSILON = 1e-12
_DEFAULT_DAMPING = 0.7
_MIN_WEIGHT = 0.0
_MAX_WEIGHT = 1.0


def _validate_weights(weights: Sequence[float], label: str) -> None:
    """Ensure all weights are finite and non-negative."""
    for i, w in enumerate(weights):
        if not isinstance(w, (int, float)):
            raise TypeError(f"{label}[{i}] is not numeric: {type(w).__name__}")
        if w < _MIN_WEIGHT:
            raise ValueError(f"{label}[{i}] is negative: {w}")


def _clamp(value: float) -> float:
    """Clamp a weight to the valid range [_MIN_WEIGHT, _MAX_WEIGHT]."""
    return max(_MIN_WEIGHT, min(_MAX_WEIGHT, value))


def adjust_allocation(
    current: Sequence[float],
    target: Sequence[float],
    *,
    damping: float = _DEFAULT_DAMPING,
) -> List[float]:
    """Nudge allocation weights toward a target distribution.

    Applies exponential-moving-average-style blending between the current
    portfolio weights and a target allocation, then re-normalises so the
    resulting weights sum to 1.

    Args:
        current: Current allocation weights (non-negative, same length as *target*).
        target:  Desired allocation weights.
        damping: Blending factor in (0, 1]. 1.0 jumps straight to *target*;
                 smaller values move more slowly.

    Returns:
        A new list of weights that sum to 1.0 (subject to floating-point
        precision), shifted toward *target* by the given *damping* factor.

    Raises:
        ValueError: If *current* and *target* differ in length, or are empty.
        TypeError:  If any weight is non-numeric.
    """
    if len(current) != len(target):
        raise ValueError("shape mismatch")
    if not current:
        raise ValueError("empty allocation")

    _validate_weights(current, "current")
    _validate_weights(target, "target")

    _log.debug("Adjusting allocation with damping=%.4f across %d assets", damping, len(current))

    updated: List[float] = []
    for idx in range(len(current)):
        updated.append(current[idx] + (target[idx] - current[idx]) * damping)

    return updated
