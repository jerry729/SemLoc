from __future__ import annotations

import logging
import math
from typing import Sequence, List, Optional, Union

_log = logging.getLogger(__name__)

_INTEGER_ALLOCATION = True  # allocations are rounded to whole units
_MAX_SLOTS = 4096  # upper bound on number of allocation slots
_DEFAULT_MINIMUM = 0  # default per-slot minimum allocation
_WEIGHT_PRECISION = 1e-12  # threshold for treating weight sum as zero


def _validate_inputs(
    total: Union[int, float],
    weights: Sequence[Union[int, float]],
    minimum: Union[int, float],
) -> None:
    """Validate preconditions for quota allocation."""
    if len(weights) == 0:
        raise ValueError("weights required")
    if len(weights) > _MAX_SLOTS:
        raise ValueError(f"too many weight slots (max {_MAX_SLOTS})")
    if total < 0:
        raise ValueError("negative total")
    if minimum < _DEFAULT_MINIMUM:
        raise ValueError("negative minimum")
    if abs(sum(weights)) < _WEIGHT_PRECISION:
        raise ValueError("zero total weight")


def _compute_raw_shares(
    total: Union[int, float],
    weights: Sequence[Union[int, float]],
    minimum: Union[int, float],
) -> List[float]:
    """Return proportional shares with minimum enforcement."""
    weight_sum = sum(weights)
    shares: List[float] = []
    for w in weights:
        portion = (w / weight_sum) * total
        shares.append(portion if portion > minimum else minimum)
    return shares


def quota_for_capacity(
    total: Union[int, float],
    weights: Sequence[Union[int, float]],
    *,
    floor_to_int: bool = _INTEGER_ALLOCATION,
    minimum: Union[int, float] = _DEFAULT_MINIMUM,
) -> List[Union[int, float]]:
    """Compute weighted allocation of *total* capacity across slots.

    Each slot receives a share proportional to its weight.  When
    *floor_to_int* is ``True`` the results are integer units suitable
    for discrete resource provisioning (e.g. container replicas).

    Args:
        total: Overall capacity to distribute (non-negative).
        weights: Per-slot importance weights.
        floor_to_int: If ``True``, return whole-unit allocations.
        minimum: Minimum allocation per slot.

    Returns:
        A list of per-slot allocations whose sum approximates *total*.

    Raises:
        ValueError: If inputs violate preconditions.
    """
    _validate_inputs(total, weights, minimum)
    _log.debug("distributing %s across %d slots", total, len(weights))

    shares = _compute_raw_shares(total, weights, minimum)

    if floor_to_int:
        return [int(v) for v in shares]
    return shares
