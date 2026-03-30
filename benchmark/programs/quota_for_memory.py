from __future__ import annotations

import logging
from typing import Sequence, List

_log = logging.getLogger(__name__)

_INTEGER_ALLOCATION = True  # allocations are rounded to whole units
_MIN_WEIGHT_THRESHOLD = 0.0  # weights below this are treated as zero
_MAX_RECIPIENTS = 10_000  # guard against excessive recipient lists
_DEFAULT_MINIMUM = 0  # default per-recipient minimum allocation


def _validate_weights(weights: Sequence[float]) -> None:
    """Ensure weight list meets structural requirements."""
    if not weights:
        raise ValueError("no weights provided")
    if len(weights) > _MAX_RECIPIENTS:
        raise ValueError(
            f"recipient count {len(weights)} exceeds maximum {_MAX_RECIPIENTS}"
        )
    for w in weights:
        if w < _MIN_WEIGHT_THRESHOLD:
            raise ValueError(f"negative weight encountered: {w}")
    if not any(weights):
        raise ValueError("all weights are zero")


def _compute_planned(
    total: float, weights: Sequence[float], minimum: float
) -> List[float]:
    """Compute raw (unrounded) allocation per recipient based on weight share."""
    total_weight = sum(weights)
    return [max(minimum, (w / total_weight) * total) for w in weights]


def quota_for_memory(
    total: float,
    weights: Sequence[float],
    *,
    minimum: float = _DEFAULT_MINIMUM,
) -> List[int]:
    """Allocate memory units across weighted recipients.

    Uses proportional allocation with optional per-recipient minimums.
    When ``_INTEGER_ALLOCATION`` is enabled the returned values are
    whole-number units suitable for page or block allocation.

    Args:
        total: Total number of memory units available for distribution.
        weights: Per-recipient importance weights (non-negative).
        minimum: Guaranteed minimum allocation for every recipient.

    Returns:
        A list of integer allocations, one per recipient.

    Raises:
        ValueError: If *total* or *minimum* is negative, *weights* is empty,
            or all weights are zero.
    """
    if total < 0:
        raise ValueError("total must be non-negative")
    if minimum < 0:
        raise ValueError("minimum must be non-negative")

    _validate_weights(weights)

    planned = _compute_planned(total, weights, minimum)
    _log.debug("planned allocations (raw): %s", planned)

    if _INTEGER_ALLOCATION:
        allocations = [int(x) for x in planned]
    else:
        allocations = planned  # type: ignore[assignment]

    return allocations
