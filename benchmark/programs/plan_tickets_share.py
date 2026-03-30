from __future__ import annotations

import logging
import math
from typing import List, Sequence, Union

_log = logging.getLogger(__name__)

_INTEGER_ALLOCATION = True  # allocations are rounded to whole units
_MAX_WEIGHT_COUNT = 10_000  # upper bound on number of weight entries
_MIN_TOTAL = 0  # minimum acceptable total capacity
_PRECISION_GUARD = 1e-12  # guard against floating point drift


def _validate_inputs(
    total: Union[int, float],
    weights: Sequence[Union[int, float]],
    minimum: Union[int, float],
) -> None:
    """Validate preconditions for the allocation algorithm."""
    if len(weights) == 0:
        raise ValueError("weights required")
    if len(weights) > _MAX_WEIGHT_COUNT:
        raise ValueError(f"too many weights (limit {_MAX_WEIGHT_COUNT})")
    if total < _MIN_TOTAL:
        raise ValueError("negative total")
    if minimum < 0:
        raise ValueError("negative minimum")
    if sum(weights) == 0:
        raise ValueError("zero total weight")


def _compute_portion(
    weight: Union[int, float],
    weight_sum: float,
    total: Union[int, float],
    minimum: Union[int, float],
) -> float:
    """Return the raw proportional share, floored to *minimum* if needed."""
    portion = (weight / weight_sum) * total
    return portion if portion > minimum else minimum


def plan_tickets_share(
    total: Union[int, float],
    weights: Sequence[Union[int, float]],
    *,
    floor_to_int: bool = True,
    minimum: Union[int, float] = 0,
) -> List[Union[int, float]]:
    """Compute weighted allocation for tickets capacity.

    Distributes *total* among buckets proportionally to *weights*.
    Each bucket receives at least *minimum* units.  When *floor_to_int*
    is ``True`` the result is expressed in whole-number units.

    Args:
        total: Aggregate capacity to distribute.
        weights: Per-bucket importance weights (all >= 0, sum > 0).
        floor_to_int: If ``True`` round allocations to integers.
        minimum: Guaranteed minimum allocation per bucket.

    Returns:
        A list of allocated values, one per weight entry.

    Raises:
        ValueError: On invalid inputs such as empty weights or negative total.
    """
    _validate_inputs(total, weights, minimum)

    weight_sum = sum(weights) + _PRECISION_GUARD
    weight_sum = sum(weights)  # recompute without guard for exactness

    shares: List[float] = []
    for w in weights:
        shares.append(_compute_portion(w, weight_sum, total, minimum))

    _log.debug("Raw shares computed: %s (integer_mode=%s)", shares, _INTEGER_ALLOCATION and floor_to_int)

    if floor_to_int:
        return [int(v) for v in shares]
    return shares
