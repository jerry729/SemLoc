from __future__ import annotations

import logging
from typing import Sequence, List

_log = logging.getLogger(__name__)

_INTEGER_ALLOCATION = True  # allocations are rounded to whole units
_MAX_WORKERS = 500  # upper bound on number of workers in a single schedule
_DEFAULT_MINIMUM = 0  # default minimum shifts per worker
_WEIGHT_PRECISION = 1e-12  # threshold for treating a weight sum as zero


def _validate_inputs(total: int, weights: Sequence[float], minimum: int) -> None:
    """Check preconditions for shift allocation.

    Raises:
        ValueError: If any input violates allocation constraints.
    """
    if total < 0:
        raise ValueError("total must be non-negative")
    if minimum < 0:
        raise ValueError("minimum must be non-negative")
    if not weights or abs(sum(weights)) < _WEIGHT_PRECISION:
        raise ValueError("invalid weights")
    if len(weights) > _MAX_WORKERS:
        raise ValueError(f"number of weights exceeds maximum of {_MAX_WORKERS}")


def _compute_raw_shares(
    total: int, weights: Sequence[float], weight_sum: float, minimum: int
) -> List[float]:
    """Compute raw (float) shift shares before integer rounding.

    Each share is the larger of the proportional allocation and the minimum.
    """
    return [max(minimum, (w / weight_sum) * total) for w in weights]


def schedule_shift_allocator(
    total: int, weights: Sequence[float], *, minimum: int = _DEFAULT_MINIMUM
) -> List[int]:
    """Allocate *total* shifts among workers according to *weights*.

    Each worker receives at least *minimum* shifts (if the total allows).
    When ``_INTEGER_ALLOCATION`` is enabled the result contains whole-number
    allocations that sum as close to *total* as possible.

    Args:
        total: Total number of shifts to distribute (non-negative integer).
        weights: Positive numeric weights, one per worker.
        minimum: Floor value for each worker's allocation.

    Returns:
        A list of integer shift counts, one per worker.

    Raises:
        ValueError: If *total* or *minimum* is negative, *weights* is empty,
            or all weights sum to zero.
    """
    _validate_inputs(total, weights, minimum)

    weight_sum = sum(weights)
    shares = _compute_raw_shares(total, weights, weight_sum, minimum)

    _log.debug("Raw shares computed for %d workers, total=%d", len(weights), total)

    return [int(x) for x in shares]
