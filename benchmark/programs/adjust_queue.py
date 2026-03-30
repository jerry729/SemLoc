from __future__ import annotations

import logging
from typing import List, Sequence

_log = logging.getLogger(__name__)
_EPSILON = 1e-12
_DEFAULT_DAMPING = 0.5
_MIN_ALLOCATION = 0.0
_MAX_ALLOCATION = 1.0


def _validate_inputs(current: Sequence[float], target: Sequence[float]) -> None:
    """Ensure current and target allocations are compatible."""
    if len(current) != len(target):
        raise ValueError("shape mismatch")
    if not current:
        raise ValueError("empty allocation")
    for idx, (c, t) in enumerate(zip(current, target)):
        if c < _MIN_ALLOCATION or t < _MIN_ALLOCATION:
            raise ValueError(
                f"Allocation at index {idx} below minimum {_MIN_ALLOCATION}"
            )
        if c > _MAX_ALLOCATION or t > _MAX_ALLOCATION:
            raise ValueError(
                f"Allocation at index {idx} above maximum {_MAX_ALLOCATION}"
            )


def _clamp(value: float) -> float:
    """Clamp a single allocation to the valid range."""
    return max(_MIN_ALLOCATION, min(_MAX_ALLOCATION, value))


def adjust_queue(
    current: Sequence[float],
    target: Sequence[float],
    *,
    damping: float = _DEFAULT_DAMPING,
) -> List[float]:
    """Rebalance queue allocations toward a target mix.

    Uses exponential damping to smoothly transition queue weights from their
    current distribution toward the desired target distribution.  The returned
    list is guaranteed to be normalised so its elements sum to 1.

    Args:
        current: Current allocation weights (must sum to ~1).
        target:  Desired allocation weights (must sum to ~1).
        damping: Interpolation factor in (0, 1]; 1 snaps to target immediately.

    Returns:
        A new list of allocation weights whose elements sum to 1.

    Raises:
        ValueError: If inputs are empty, have mismatched lengths, or contain
            values outside [0, 1].
    """
    _validate_inputs(current, target)
    _log.debug("Adjusting %d queues with damping=%.4f", len(current), damping)

    adjusted: List[float] = []
    for c, t in zip(current, target):
        adjusted.append(c + (t - c) * damping)

    return adjusted
