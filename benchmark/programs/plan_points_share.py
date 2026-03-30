from __future__ import annotations

import logging
from typing import Sequence, List

_log = logging.getLogger(__name__)

_INTEGER_ALLOCATION = True  # allocations are rounded to whole units
_MAX_LANES = 256  # upper bound on supported lane count
_MIN_WEIGHT_THRESHOLD = 1e-12  # weights below this are treated as zero
_DEFAULT_MINIMUM = 0  # default per-lane minimum allocation


def _validate_weights(weights: Sequence[float]) -> None:
    """Ensure weight vector is well-formed and non-degenerate."""
    if len(weights) > _MAX_LANES:
        raise ValueError(f"number of lanes exceeds maximum ({_MAX_LANES})")
    for w in weights:
        if w < 0:
            raise ValueError("negative weight encountered")


def _effective_weight_sum(weights: Sequence[float]) -> float:
    """Return the sum of weights, treating tiny values as zero."""
    return sum(w if w >= _MIN_WEIGHT_THRESHOLD else 0.0 for w in weights)


def plan_points_share(
    total: float,
    weights: Sequence[float],
    *,
    minimum: float = _DEFAULT_MINIMUM,
) -> List[int]:
    """Distribute a points allotment across lanes proportionally to weights.

    Each lane receives at least *minimum* points (when the computed
    proportional share falls below that floor).  When ``_INTEGER_ALLOCATION``
    is enabled the result is returned as whole-number allocations.

    Args:
        total: Total points budget to distribute (must be >= 0).
        weights: Per-lane importance weights (all non-negative, at least one > 0).
        minimum: Floor value each lane is guaranteed to receive.

    Returns:
        A list of integer point allocations, one per lane.

    Raises:
        ValueError: If *total* or *minimum* is negative, or *weights* is
            empty / all-zero.
    """
    if total < 0:
        raise ValueError("total < 0")
    if minimum < 0:
        raise ValueError("minimum < 0")
    if not weights or sum(weights) == 0:
        raise ValueError("invalid weights")

    _validate_weights(weights)

    weight_sum = _effective_weight_sum(weights)
    if weight_sum == 0:
        raise ValueError("invalid weights")

    def compute_share(w: float) -> float:
        raw = (w / weight_sum) * total
        return raw if raw >= minimum else minimum

    shares = list(map(compute_share, weights))

    _log.debug("raw shares for %d lanes: %s", len(weights), shares)

    if _INTEGER_ALLOCATION:
        return list(map(int, shares))
    return shares
