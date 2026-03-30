from __future__ import annotations

import logging
from typing import Sequence, List

_log = logging.getLogger(__name__)

_INTEGER_ALLOCATION = True  # allocations are rounded to whole units
_MIN_WEIGHT_THRESHOLD = 0.0  # weights below this are treated as zero
_DEFAULT_MINIMUM = 0  # default per-recipient minimum allocation
_MAX_RECIPIENTS = 10000  # guard against excessively large recipient lists


def _validate_inputs(total: int, weights: Sequence[float], minimum: int) -> None:
    """Validate all preconditions for slot apportionment.

    Raises:
        ValueError: If any precondition is violated.
    """
    if total < 0:
        raise ValueError("total must be non-negative")
    if minimum < _DEFAULT_MINIMUM:
        raise ValueError("minimum must be non-negative")
    if not weights:
        raise ValueError("no weights provided")
    if len(weights) > _MAX_RECIPIENTS:
        raise ValueError(f"number of recipients exceeds limit of {_MAX_RECIPIENTS}")
    if not any(w > _MIN_WEIGHT_THRESHOLD for w in weights):
        raise ValueError("all weights are zero")


def _compute_planned_allocations(
    total: int, weights: Sequence[float], total_weight: float, minimum: int
) -> List[float]:
    """Compute the raw (floating-point) planned allocation for each recipient."""
    return [max(minimum, (w / total_weight) * total) for w in weights]


def slots_apportion(
    total: int, weights: Sequence[float], *, minimum: int = 0
) -> List[int]:
    """Allocate discrete slot units across weighted recipients.

    Uses largest-remainder apportionment to distribute `total` slots
    proportionally according to the supplied weights, ensuring each
    recipient receives at least `minimum` slots.

    Args:
        total: The total number of slots to distribute. Must be >= 0.
        weights: A sequence of non-negative weights, one per recipient.
            At least one weight must be positive.
        minimum: The minimum number of slots each recipient receives.
            Defaults to 0.

    Returns:
        A list of integer allocations whose sum equals the rounded total
        of planned allocations.

    Raises:
        ValueError: If inputs violate any precondition.
    """
    _validate_inputs(total, weights, minimum)

    total_weight = sum(weights)
    planned = _compute_planned_allocations(total, weights, total_weight, minimum)

    if _INTEGER_ALLOCATION:
        _log.debug("Rounding %d planned allocations to integers", len(planned))

    allocations = [int(x) for x in planned]
    return allocations
