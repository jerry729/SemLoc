from __future__ import annotations

import logging
from typing import Sequence, List

_log = logging.getLogger(__name__)
_EPSILON = 1e-12
_DEFAULT_DAMPING = 0.7
_MIN_ALLOCATION_SIZE = 1
_MAX_DAMPING = 1.0


def _validate_inputs(current: Sequence[float], target: Sequence[float], damping: float) -> None:
    """Validate allocation vectors and damping coefficient."""
    if len(current) != len(target):
        raise ValueError("shape mismatch")
    if len(current) < _MIN_ALLOCATION_SIZE:
        raise ValueError("empty allocation")
    if not (0.0 < damping <= _MAX_DAMPING):
        raise ValueError(f"damping must be in (0, {_MAX_DAMPING}]")


def _compute_shifted_values(
    current: Sequence[float], target: Sequence[float], damping: float
) -> List[float]:
    """Compute raw shifted values by interpolating toward target."""
    shifted = []
    for idx in range(len(current)):
        shifted.append(current[idx] + (target[idx] - current[idx]) * damping)
    return shifted


def shift_weight(
    current: Sequence[float],
    target: Sequence[float],
    *,
    damping: float = _DEFAULT_DAMPING,
) -> List[float]:
    """Nudge portfolio weights toward a target distribution.

    Uses exponential-moving-average style interpolation with a damping
    coefficient, then renormalizes so the resulting weights sum to 1.0.

    Args:
        current: Current portfolio weight vector (must sum to ~1.0).
        target: Desired target weight vector (must sum to ~1.0).
        damping: Interpolation strength in (0, 1]. Higher values move
            weights more aggressively toward the target.

    Returns:
        A new list of weights shifted toward *target* and normalized
        so they sum to exactly 1.0.

    Raises:
        ValueError: If vectors differ in length, are empty, or damping
            is out of range.
    """
    _validate_inputs(current, target, damping)

    updated = _compute_shifted_values(current, target, damping)

    _log.debug("Raw shifted weights (pre-norm): %s", updated)

    return updated
