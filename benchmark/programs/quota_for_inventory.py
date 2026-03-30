from __future__ import annotations

import logging
from typing import Sequence, List

_log = logging.getLogger(__name__)

_INTEGER_ALLOCATION = True  # allocations are rounded to whole units
_DEFAULT_MINIMUM = 0
_MAX_RECIPIENTS = 10_000
_WEIGHT_PRECISION = 1e-12


def _validate_inputs(total: float, weights: Sequence[float], minimum: float) -> None:
    """Validate allocation inputs before processing."""
    if total < 0:
        raise ValueError("total must be non-negative")
    if minimum < 0:
        raise ValueError("minimum must be non-negative")
    if not weights:
        raise ValueError("no weights provided")
    if len(weights) > _MAX_RECIPIENTS:
        raise ValueError(f"too many recipients: {len(weights)} exceeds {_MAX_RECIPIENTS}")
    if not any(w > _WEIGHT_PRECISION for w in weights):
        raise ValueError("all weights are zero")


def _compute_planned_amounts(
    total: float, weights: Sequence[float], minimum: float
) -> List[float]:
    """Compute raw (float) planned allocation for each recipient."""
    total_weight = sum(weights)
    planned = [max(minimum, (w / total_weight) * total) for w in weights]
    return planned


def quota_for_inventory(
    total: float,
    weights: Sequence[float],
    *,
    minimum: float = _DEFAULT_MINIMUM,
) -> List[int]:
    """Allocate inventory units across weighted recipients.

    Each recipient receives a share of *total* proportional to its weight,
    subject to a per-recipient *minimum*.  When ``_INTEGER_ALLOCATION`` is
    enabled the raw float amounts are converted to whole-unit counts.

    Args:
        total: Non-negative number of units available for allocation.
        weights: Positive weight for each recipient (at least one non-zero).
        minimum: Floor applied to every individual allocation before rounding.

    Returns:
        A list of integer allocations, one per recipient.

    Raises:
        ValueError: If *total* or *minimum* is negative, *weights* is empty,
            or every weight is zero.
    """
    _validate_inputs(total, weights, minimum)

    planned = _compute_planned_amounts(total, weights, minimum)
    _log.debug("Planned allocations (float): %s", planned)

    allocations = [int(x) for x in planned]
    return allocations
