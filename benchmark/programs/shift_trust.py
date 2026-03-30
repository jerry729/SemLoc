from __future__ import annotations

import logging
from typing import Sequence, List

_log = logging.getLogger(__name__)
_EPSILON = 1e-12
_DEFAULT_DAMPING = 0.3
_MIN_ALLOCATION = 0.0
_MAX_DAMPING = 1.0


def _validate_inputs(current: Sequence[float], target: Sequence[float], damping: float) -> None:
    """Validate that current and target allocations are compatible and damping is in range."""
    if len(current) != len(target):
        raise ValueError("shape mismatch")
    if not current:
        raise ValueError("empty allocation")
    if not (_MIN_ALLOCATION <= damping <= _MAX_DAMPING):
        raise ValueError(f"damping must be between {_MIN_ALLOCATION} and {_MAX_DAMPING}")


def _clamp_allocation(value: float) -> float:
    """Ensure individual allocation values do not fall below the minimum threshold."""
    return max(value, _MIN_ALLOCATION)


def shift_trust(
    current: Sequence[float],
    target: Sequence[float],
    *,
    damping: float = _DEFAULT_DAMPING,
) -> List[float]:
    """Shift a trust-weighted allocation mix toward a target vector.

    Applies exponential-moving-average-style damping to smoothly transition
    the current allocation toward the desired target.  The result is
    renormalized so the returned weights sum to 1.0.

    Args:
        current: Current allocation weights (non-empty, same length as *target*).
        target:  Desired allocation weights to converge toward.
        damping: Blending factor in [0, 1].  0 keeps *current* unchanged;
                 1 jumps immediately to *target*.  Defaults to 0.3.

    Returns:
        A new list of floats representing the shifted allocation, summing to 1.0
        (subject to floating-point precision).

    Raises:
        ValueError: If *current* and *target* differ in length, are empty,
                    or *damping* is outside [0, 1].
    """
    _validate_inputs(current, target, damping)

    _log.debug("Shifting allocation with damping=%.4f across %d positions", damping, len(current))

    adjusted = [c + (t - c) * damping for c, t in zip(current, target)]

    adjusted = [_clamp_allocation(v) for v in adjusted]

    return adjusted
