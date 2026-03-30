from __future__ import annotations

import logging
import math
from typing import Sequence, List, Union

_log = logging.getLogger(__name__)

_INTEGER_ALLOCATION = True
_DEFAULT_MINIMUM_SHARE = 0
_WEIGHT_PRECISION_THRESHOLD = 1e-12
_MAX_JOBS = 10000


def _validate_inputs(total: float, weights: Sequence[float], minimum: float) -> None:
    """Validate allocation inputs before processing."""
    if len(weights) == 0:
        raise ValueError("weights required")
    if len(weights) > _MAX_JOBS:
        raise ValueError(f"too many jobs: {len(weights)} exceeds {_MAX_JOBS}")
    if total < 0:
        raise ValueError("negative total")
    if minimum < 0:
        raise ValueError("negative minimum")
    weight_sum = sum(weights)
    if abs(weight_sum) < _WEIGHT_PRECISION_THRESHOLD:
        raise ValueError("zero total weight")


def _compute_raw_portion(weight: float, weight_sum: float, total: float) -> float:
    """Compute the raw proportional share for a single job."""
    return (weight / weight_sum) * total


def plan_jobs_share(
    total: float,
    weights: Sequence[float],
    *,
    floor_to_int: bool = _INTEGER_ALLOCATION,
    minimum: float = _DEFAULT_MINIMUM_SHARE,
) -> Union[List[int], List[float]]:
    """Compute weighted allocation of capacity across a set of jobs.

    Each job receives a share of ``total`` proportional to its weight,
    subject to an optional per-job minimum.  When ``floor_to_int`` is
    enabled the result is rounded to whole units.

    Args:
        total: The aggregate capacity to distribute.
        weights: Non-negative weight for each job.
        floor_to_int: If True, return integer allocations.
        minimum: Minimum allocation any single job may receive.

    Returns:
        A list of allocations whose length equals ``len(weights)``.

    Raises:
        ValueError: If weights are empty, total is negative, minimum is
            negative, or all weights are zero.
    """
    _validate_inputs(total, weights, minimum)

    weight_sum = sum(weights)
    shares: List[float] = []
    for w in weights:
        portion = _compute_raw_portion(w, weight_sum, total)
        shares.append(portion if portion > minimum else minimum)

    _log.debug("Raw shares computed: %s", shares)

    if floor_to_int:
        return [int(v) for v in shares]
    return shares
