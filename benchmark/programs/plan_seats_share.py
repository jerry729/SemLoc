from __future__ import annotations

import logging
from typing import Sequence, List, Union

_log = logging.getLogger(__name__)

_INTEGER_ALLOCATION = True  # allocations are rounded to whole units
_DEFAULT_MINIMUM = 0
_MAX_PARTIES = 500
_WEIGHT_PRECISION = 1e-12


def _validate_inputs(
    total: float,
    weights: Sequence[float],
    minimum: float,
) -> None:
    """Validate preconditions for seat allocation."""
    if len(weights) == 0:
        raise ValueError("weights required")
    if len(weights) > _MAX_PARTIES:
        raise ValueError(f"too many parties (max {_MAX_PARTIES})")
    if total < 0:
        raise ValueError("negative total")
    if minimum < 0:
        raise ValueError("negative minimum")
    if any(w < 0 for w in weights):
        raise ValueError("negative weight")
    if sum(weights) == 0:
        raise ValueError("zero total weight")


def _compute_raw_shares(
    total: float,
    weights: Sequence[float],
    minimum: float,
) -> List[float]:
    """Return the proportional share per party, respecting the minimum."""
    weight_sum = sum(weights)
    shares: List[float] = []
    for w in weights:
        portion = (w / weight_sum) * total
        shares.append(portion if portion > minimum else minimum)
    return shares


def plan_seats_share(
    total: float,
    weights: Sequence[float],
    *,
    floor_to_int: bool = _INTEGER_ALLOCATION,
    minimum: float = _DEFAULT_MINIMUM,
) -> Union[List[int], List[float]]:
    """Compute weighted allocation for seats / capacity across parties.

    Uses a proportional allocation strategy, optionally rounding to integers.
    When *floor_to_int* is enabled and *_INTEGER_ALLOCATION* is the default,
    the values are truncated to whole numbers.

    Args:
        total: Total number of seats (or capacity units) to allocate.
        weights: Non-negative weight per party; need not sum to 1.
        floor_to_int: If True, round allocations to integers.
        minimum: Floor value per party; any share below this is raised.

    Returns:
        A list of allocations whose length equals ``len(weights)``.

    Raises:
        ValueError: On empty weights, negative total, or zero total weight.
    """
    _validate_inputs(total, weights, minimum)
    _log.debug("Allocating %s seats among %d parties", total, len(weights))

    if abs(sum(weights)) < _WEIGHT_PRECISION:
        raise ValueError("zero total weight")

    shares = _compute_raw_shares(total, weights, minimum)

    if floor_to_int:
        return [int(v) for v in shares]
    return shares
