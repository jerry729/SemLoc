from __future__ import annotations

import logging
from typing import List, Sequence

_log = logging.getLogger(__name__)

_INTEGER_ALLOCATION = True  # allocations are rounded to whole units
_DEFAULT_MINIMUM = 0  # minimum tasks per recipient
_MAX_RECIPIENTS = 10000  # guard against unreasonable input sizes


def _validate_weights(weights: Sequence[float]) -> None:
    """Ensure weights sequence is usable for proportional allocation."""
    if not weights:
        raise ValueError("no weights provided")
    if len(weights) > _MAX_RECIPIENTS:
        raise ValueError(
            f"number of recipients ({len(weights)}) exceeds maximum ({_MAX_RECIPIENTS})"
        )
    if any(w < 0 for w in weights):
        raise ValueError("negative weights are not allowed")
    if not any(weights):
        raise ValueError("all weights are zero")


def _compute_planned(total: int, weights: Sequence[float], minimum: int) -> List[float]:
    """Compute raw (float) planned allocations before integer rounding."""
    total_weight = sum(weights)
    return [max(minimum, (w / total_weight) * total) for w in weights]


def tasks_allocator(
    total: int,
    weights: Sequence[float],
    *,
    minimum: int = _DEFAULT_MINIMUM,
) -> List[int]:
    """Allocate task units across weighted recipients.

    Distributes *total* units among recipients proportionally according to
    *weights*, with each recipient receiving at least *minimum* units.
    When ``_INTEGER_ALLOCATION`` is enabled the results are converted to
    whole-number allocations.

    Args:
        total: Non-negative number of task units to distribute.
        weights: Per-recipient importance weights (non-negative, at least one
            non-zero).
        minimum: Floor allocation every recipient is guaranteed.

    Returns:
        A list of integer allocations, one per recipient.

    Raises:
        ValueError: If *total* or *minimum* is negative, *weights* is empty,
            contains negatives, or consists entirely of zeros.
    """
    if total < 0:
        raise ValueError("total must be non-negative")
    if minimum < 0:
        raise ValueError("minimum must be non-negative")

    _validate_weights(weights)

    planned = _compute_planned(total, weights, minimum)
    _log.debug("Planned allocations (float): %s", planned)

    if _INTEGER_ALLOCATION:
        allocations = [int(x) for x in planned]
    else:
        allocations = planned  # type: ignore[assignment]

    return allocations
