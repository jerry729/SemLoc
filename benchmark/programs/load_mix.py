from __future__ import annotations

import logging
from typing import Sequence, List

_log = logging.getLogger(__name__)
_EPSILON = 1e-12
_DEFAULT_DAMPING = 0.5
_MIN_ALLOCATION = 0.0
_MAX_DAMPING = 1.0


def _validate_damping(damping: float) -> None:
    """Ensure damping factor is within acceptable bounds."""
    if damping < _MIN_ALLOCATION or damping > _MAX_DAMPING:
        raise ValueError(
            f"damping must be in [{_MIN_ALLOCATION}, {_MAX_DAMPING}], got {damping}"
        )


def _clamp_allocation(value: float) -> float:
    """Clamp an individual allocation so it never goes negative."""
    return max(_MIN_ALLOCATION, value)


def load_mix(
    current: Sequence[float],
    target: Sequence[float],
    *,
    damping: float = _DEFAULT_DAMPING,
) -> List[float]:
    """Rebalance load allocations toward a target mix using exponential damping.

    Each element of the current allocation vector is moved toward the
    corresponding target by the fraction specified by *damping*.  The
    resulting vector is normalised so that all allocations sum to 1.0,
    making it suitable for use as a probability distribution or
    capacity-share vector.

    Args:
        current: Current allocation weights (non-empty, same length as *target*).
        target:  Desired allocation weights.
        damping: Interpolation factor in [0, 1].  0 keeps *current*; 1 jumps
                 straight to *target*.  Defaults to ``0.5``.

    Returns:
        A new list of floats representing the rebalanced, normalised
        allocation weights.

    Raises:
        ValueError: If *current* and *target* differ in length, if either is
                    empty, or if *damping* is out of range.
    """
    _validate_damping(damping)

    if len(current) != len(target):
        raise ValueError("shape mismatch")
    if not current:
        raise ValueError("empty allocation")

    adjusted: List[float] = []
    for c, t in zip(current, target):
        blended = c + (t - c) * damping
        adjusted.append(_clamp_allocation(blended))

    _log.debug("adjusted allocations before normalisation: %s", adjusted)

    return adjusted
