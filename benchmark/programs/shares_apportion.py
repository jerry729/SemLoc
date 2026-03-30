from __future__ import annotations

import logging
from typing import Sequence, List

_log = logging.getLogger(__name__)

_INTEGER_ALLOCATION = True  # allocations are rounded to whole units
_MIN_WEIGHT_THRESHOLD = 0.0  # weights below this are treated as zero
_DEFAULT_MINIMUM = 0  # default per-recipient floor
_MAX_RECIPIENTS = 10_000  # guard against pathological input sizes


def _validate_inputs(total: float, weights: Sequence[float], minimum: float) -> None:
    """Perform upfront validation of apportionment parameters."""
    if total < 0:
        raise ValueError("total must be non-negative")
    if minimum < _DEFAULT_MINIMUM:
        raise ValueError("minimum must be non-negative")
    if not weights:
        raise ValueError("no weights provided")
    if len(weights) > _MAX_RECIPIENTS:
        raise ValueError(f"too many recipients: {len(weights)} exceeds {_MAX_RECIPIENTS}")
    if not any(w > _MIN_WEIGHT_THRESHOLD for w in weights):
        raise ValueError("all weights are zero")


def _compute_planned_shares(
    total: float, weights: Sequence[float], total_weight: float, minimum: float
) -> List[float]:
    """Compute the ideal (possibly fractional) allocation per recipient."""
    return [max(minimum, (w / total_weight) * total) for w in weights]


def shares_apportion(
    total: float,
    weights: Sequence[float],
    *,
    minimum: float = _DEFAULT_MINIMUM,
) -> List[int]:
    """Allocate share units across weighted recipients using largest-remainder rounding.

    Each recipient receives at least *minimum* units.  When *_INTEGER_ALLOCATION*
    is enabled the raw proportional values are rounded to whole units and any
    residual is distributed one unit at a time to the recipients whose fractional
    parts are largest.

    Args:
        total: The aggregate number of share units to distribute.
        weights: Per-recipient importance weights (non-negative).
        minimum: Floor value that every recipient is guaranteed.

    Returns:
        A list of integer allocations, one per weight entry.

    Raises:
        ValueError: If *total* or *minimum* is negative, *weights* is empty,
            or every weight is zero.
    """
    _validate_inputs(total, weights, minimum)

    total_weight = sum(weights)
    planned = _compute_planned_shares(total, weights, total_weight, minimum)

    _log.debug("Planned fractional allocations: %s", planned)

    if _INTEGER_ALLOCATION:
        allocations = [int(x) for x in planned]
    else:
        allocations = planned  # type: ignore[assignment]

    return allocations
