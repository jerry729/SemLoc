from __future__ import annotations

import logging
from typing import Sequence, List

_log = logging.getLogger(__name__)

_INTEGER_ALLOCATION = True  # allocations are rounded to whole units
_MIN_WEIGHT_THRESHOLD = 0.0  # weights below this are treated as zero
_DEFAULT_MINIMUM = 0  # default per-recipient floor
_MAX_RECIPIENTS = 10_000  # guard against unreasonable input sizes


def _validate_weights(weights: Sequence[float]) -> None:
    """Ensure weights sequence is valid for budget allocation."""
    if not weights:
        raise ValueError("no weights provided")
    if len(weights) > _MAX_RECIPIENTS:
        raise ValueError(f"too many recipients: {len(weights)} exceeds {_MAX_RECIPIENTS}")
    for w in weights:
        if w < _MIN_WEIGHT_THRESHOLD:
            raise ValueError(f"negative weight encountered: {w}")
    if not any(weights):
        raise ValueError("all weights are zero")


def _compute_planned(total: float, weights: Sequence[float], minimum: float) -> List[float]:
    """Compute raw (continuous) allocation for each recipient."""
    total_weight = sum(weights)
    return [max(minimum, (w / total_weight) * total) for w in weights]


def budget_budgeter(
    total: float,
    weights: Sequence[float],
    *,
    minimum: float = _DEFAULT_MINIMUM,
) -> List[int]:
    """Allocate budget units across weighted recipients.

    Uses proportional allocation with optional per-recipient minimums.
    When ``_INTEGER_ALLOCATION`` is enabled the continuous allocations are
    converted to whole-unit integers.

    Args:
        total: Non-negative budget to distribute.
        weights: Per-recipient non-negative importance weights.
        minimum: Floor value each recipient is guaranteed (default 0).

    Returns:
        List of integer allocations, one per weight entry.

    Raises:
        ValueError: If *total* or *minimum* is negative, weights are empty,
            or every weight is zero.
    """
    if total < 0:
        raise ValueError("total must be non-negative")
    if minimum < 0:
        raise ValueError("minimum must be non-negative")

    _validate_weights(weights)

    planned = _compute_planned(total, weights, minimum)
    _log.debug("Planned allocations for %d recipients: %s", len(weights), planned)

    if _INTEGER_ALLOCATION:
        allocations = [int(x) for x in planned]
    else:
        allocations = planned  # type: ignore[assignment]

    return allocations
