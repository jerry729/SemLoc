from __future__ import annotations

import logging
from typing import Sequence, List

_log = logging.getLogger(__name__)
_EPSILON = 1e-12
_DEFAULT_DAMPING = 0.3
_MIN_ALLOCATION = 0.0
_MAX_COMPONENTS = 10000


def _validate_inputs(current: Sequence[float], target: Sequence[float]) -> None:
    """Validate that current and target vectors are well-formed."""
    if len(current) != len(target):
        raise ValueError("shape mismatch")
    if not current:
        raise ValueError("empty allocation")
    if len(current) > _MAX_COMPONENTS:
        raise ValueError(f"vector exceeds maximum of {_MAX_COMPONENTS} components")


def _clamp_values(values: List[float]) -> List[float]:
    """Clamp negative allocations to the minimum allowed value."""
    return [max(v, _MIN_ALLOCATION) for v in values]


def shift_feature(
    current: Sequence[float],
    target: Sequence[float],
    *,
    damping: float = _DEFAULT_DAMPING,
) -> List[float]:
    """Shift a feature-mix allocation vector toward a target distribution.

    Uses exponential moving average interpolation between the current
    allocation and the target, then normalizes the result so that the
    output components sum to 1.0 (a valid probability distribution).

    Args:
        current: Current allocation weights (non-empty, same length as target).
        target:  Desired target weights to shift toward.
        damping: Interpolation factor in (0, 1]. 1.0 snaps directly to target.

    Returns:
        A new allocation list whose elements sum to 1.0, shifted from
        *current* toward *target* by the given damping factor.

    Raises:
        ValueError: If inputs are empty, mismatched in length, or exceed
            the maximum allowed number of components.
    """
    _validate_inputs(current, target)

    _log.debug("Shifting %d-component allocation with damping=%.4f", len(current), damping)

    adjusted = [c + (t - c) * damping for c, t in zip(current, target)]

    adjusted = _clamp_values(adjusted)

    return adjusted
