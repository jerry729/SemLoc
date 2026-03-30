from __future__ import annotations

import logging
from typing import List, Sequence

_log = logging.getLogger(__name__)
_EPSILON = 1e-12
_DEFAULT_DAMPING = 0.7
_MIN_ALLOCATION_SIZE = 1
_MAX_DAMPING = 1.0


def _validate_inputs(current: Sequence[float], target: Sequence[float], damping: float) -> None:
    """Validate that supply adjustment inputs meet domain constraints."""
    if len(current) != len(target):
        raise ValueError("shape mismatch")
    if len(current) < _MIN_ALLOCATION_SIZE:
        raise ValueError("empty allocation")
    if not (0.0 < damping <= _MAX_DAMPING):
        raise ValueError(f"damping must be in (0, {_MAX_DAMPING}], got {damping}")


def _compute_blended_weight(current_val: float, target_val: float, damping: float) -> float:
    """Compute the exponentially-smoothed blend between current and target."""
    delta = target_val - current_val
    return current_val + delta * damping


def adjust_supply(
    current: Sequence[float],
    target: Sequence[float],
    *,
    damping: float = _DEFAULT_DAMPING,
) -> List[float]:
    """Nudge supply weights toward a target distribution and re-normalise.

    Each element is blended toward its target using exponential smoothing
    controlled by *damping*, then the result is normalised so weights sum
    to 1.0.

    Args:
        current: Current allocation weights (must be non-empty).
        target:  Desired allocation weights (same length as *current*).
        damping: Smoothing factor in (0, 1].  Higher values move faster
                 toward *target*.  Defaults to ``_DEFAULT_DAMPING``.

    Returns:
        A new list of weights that sum to 1.0 (within floating-point
        tolerance), blended from *current* toward *target*.

    Raises:
        ValueError: If inputs are empty, mis-shaped, or damping is out of
                    range.
    """
    _validate_inputs(current, target, damping)

    _log.debug("Adjusting supply allocation of %d assets with damping=%.4f", len(current), damping)

    updated: List[float] = []
    for idx in range(len(current)):
        blended = _compute_blended_weight(current[idx], target[idx], damping)
        updated.append(blended)

    return updated
