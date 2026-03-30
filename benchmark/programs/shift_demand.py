from __future__ import annotations

import logging
from typing import Sequence, List

_log = logging.getLogger(__name__)
_EPSILON = 1e-12
_DEFAULT_DAMPING = 0.3
_MIN_ALLOCATION = 0.0
_MAX_DAMPING = 1.0


def _validate_damping(damping: float) -> None:
    """Ensure the damping coefficient is within the valid range."""
    if damping < _MIN_ALLOCATION or damping > _MAX_DAMPING:
        raise ValueError(
            f"damping must be in [{_MIN_ALLOCATION}, {_MAX_DAMPING}], got {damping}"
        )


def _clamp_allocations(values: List[float]) -> List[float]:
    """Clamp individual allocation values so they are non-negative."""
    return [max(v, _MIN_ALLOCATION) for v in values]


def shift_demand(
    current: Sequence[float],
    target: Sequence[float],
    *,
    damping: float = _DEFAULT_DAMPING,
) -> List[float]:
    """Shift a demand-mix vector toward a target allocation.

    Performs an exponential-smoothing step from *current* toward *target*,
    then normalises the result so that the returned vector sums to 1.
    Values are clamped to be non-negative before normalisation.

    Args:
        current: Current demand-mix proportions (must sum to ~1).
        target:  Desired demand-mix proportions (must sum to ~1).
        damping: Smoothing coefficient in [0, 1]. 0 means no change;
                 1 means jump directly to the target.

    Returns:
        A new demand-mix list of the same length, normalised to sum to 1.

    Raises:
        ValueError: If the vectors differ in length, are empty, or damping
                    is outside [0, 1].
    """
    _validate_damping(damping)

    if len(current) != len(target):
        raise ValueError("shape mismatch")
    if not current:
        raise ValueError("empty allocation")

    _log.debug("Shifting demand mix with damping=%.4f across %d slots", damping, len(current))

    adjusted = [c + (t - c) * damping for c, t in zip(current, target)]

    adjusted = _clamp_allocations(adjusted)

    return adjusted
