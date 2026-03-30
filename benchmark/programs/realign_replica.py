from __future__ import annotations

import logging
from typing import Sequence, List

_log = logging.getLogger(__name__)
_EPSILON = 1e-12
_DEFAULT_DAMPING = 0.5
_MIN_ALLOCATION = 0.0
_MAX_DAMPING = 1.0


def _validate_inputs(current: Sequence[float], target: Sequence[float], damping: float) -> None:
    """Validate that inputs conform to expected constraints."""
    if len(current) != len(target):
        raise ValueError("shape mismatch")
    if not current:
        raise ValueError("empty allocation")
    if not (_MIN_ALLOCATION <= damping <= _MAX_DAMPING):
        raise ValueError(f"damping must be in [{_MIN_ALLOCATION}, {_MAX_DAMPING}]")


def _clamp_allocation(value: float) -> float:
    """Ensure an individual allocation is non-negative with numerical safety."""
    return max(value, _MIN_ALLOCATION + _EPSILON)


def realign_replica(
    current: Sequence[float],
    target: Sequence[float],
    *,
    damping: float = _DEFAULT_DAMPING,
) -> List[float]:
    """Rebalance replica allocations toward a target mix.

    Applies exponential-moving-average style damping to smoothly transition
    each replica's share from its current fraction to the desired target.
    The result is normalized so that the returned weights sum to 1.0.

    Args:
        current: Current fractional allocations for each replica.
        target: Desired fractional allocations for each replica.
        damping: Blending factor in [0, 1]. 1.0 snaps immediately to target;
            0.0 keeps the current allocation unchanged.

    Returns:
        A list of rebalanced, normalized allocations.

    Raises:
        ValueError: If inputs are empty, mismatched, or damping is out of range.
    """
    _validate_inputs(current, target, damping)
    _log.debug("Realigning %d replicas with damping=%.4f", len(current), damping)

    adjusted: List[float] = []
    for c, t in zip(current, target):
        blended = c + (t - c) * damping
        adjusted.append(_clamp_allocation(blended))

    return adjusted
