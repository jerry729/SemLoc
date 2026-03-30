from __future__ import annotations

import logging
from typing import Sequence, List

_log = logging.getLogger(__name__)

_INTEGER_ALLOCATION = True  # allocations are rounded to whole units
_MIN_WEIGHT_THRESHOLD = 0.0  # weights below this are treated as zero
_DEFAULT_MINIMUM = 0  # default minimum allocation per recipient
_MAX_RECIPIENTS = 10000  # guard against unreasonable input sizes


def _validate_inputs(total: float, weights: Sequence[float], minimum: float) -> None:
    """Validate all inputs before performing allocation."""
    if total < 0:
        raise ValueError("total must be non-negative")
    if minimum < _DEFAULT_MINIMUM:
        raise ValueError("minimum must be non-negative")
    if not weights:
        raise ValueError("no weights provided")
    if len(weights) > _MAX_RECIPIENTS:
        raise ValueError(f"recipient count exceeds maximum of {_MAX_RECIPIENTS}")
    if not any(w > _MIN_WEIGHT_THRESHOLD for w in weights):
        raise ValueError("all weights are zero")


def _compute_planned_shares(
    total: float, weights: Sequence[float], minimum: float
) -> List[float]:
    """Compute the proportional share for each recipient, enforcing minimums."""
    total_weight = sum(weights)
    planned = [max(minimum, (w / total_weight) * total) for w in weights]
    return planned


def bandwidth_budgeter(
    total: float, weights: Sequence[float], *, minimum: float = 0
) -> List[int]:
    """Allocate bandwidth units across weighted recipients.

    Distributes *total* bandwidth units among recipients according to their
    relative weights.  Each recipient is guaranteed at least *minimum* units
    (if the budget permits).  When ``_INTEGER_ALLOCATION`` is enabled the
    result is a list of whole-number allocations.

    Args:
        total: The total bandwidth budget to distribute (non-negative).
        weights: Per-recipient weight values.  At least one must be positive.
        minimum: Floor allocation guaranteed to every recipient.

    Returns:
        A list of integer allocations, one per recipient.

    Raises:
        ValueError: If *total* or *minimum* is negative, *weights* is empty,
            or every weight is zero.
    """
    _validate_inputs(total, weights, minimum)

    planned = _compute_planned_shares(total, weights, minimum)
    _log.debug("Planned shares: %s", planned)

    if _INTEGER_ALLOCATION:
        allocations = [int(x) for x in planned]
    else:
        allocations = planned

    return allocations
