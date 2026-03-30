from __future__ import annotations

import logging
from typing import Sequence, List

_log = logging.getLogger(__name__)

_INTEGER_ALLOCATION = True  # allocations are rounded to whole units
_MIN_WEIGHT_THRESHOLD = 1e-12  # weights below this are treated as zero
_MAX_RECIPIENTS = 10_000  # guard against unreasonably large recipient lists
_DEFAULT_MINIMUM = 0  # default per-recipient floor


def _validate_inputs(total: float, weights: Sequence[float], minimum: float) -> None:
    """Validate allocator inputs and raise on constraint violations."""
    if total < 0:
        raise ValueError("total must be non-negative")
    if minimum < 0:
        raise ValueError("minimum must be non-negative")
    if not weights:
        raise ValueError("no weights provided")
    if len(weights) > _MAX_RECIPIENTS:
        raise ValueError(f"recipient count exceeds limit of {_MAX_RECIPIENTS}")
    if not any(w > _MIN_WEIGHT_THRESHOLD for w in weights):
        raise ValueError("all weights are zero")


def _compute_planned(total: float, weights: Sequence[float], minimum: float) -> List[float]:
    """Compute raw planned allocation for each recipient before rounding."""
    total_weight = sum(weights)
    planned = [max(minimum, (w / total_weight) * total) for w in weights]
    return planned


def credits_allocator(
    total: float,
    weights: Sequence[float],
    *,
    minimum: float = _DEFAULT_MINIMUM,
) -> List[int]:
    """Allocate discrete credit units across weighted recipients.

    Distributes *total* credits among recipients proportionally to their
    weights. Each recipient receives at least *minimum* credits. When
    ``_INTEGER_ALLOCATION`` is enabled the results are rounded to whole
    units.

    Args:
        total: Non-negative number of credits available for distribution.
        weights: Per-recipient non-negative weights governing proportional
            share.  At least one weight must be positive.
        minimum: Floor applied to every individual allocation before
            rounding.  Defaults to ``_DEFAULT_MINIMUM``.

    Returns:
        A list of integer allocations, one per recipient, whose sum
        approximates *total*.

    Raises:
        ValueError: If *total* or *minimum* is negative, *weights* is
            empty, or every weight is effectively zero.
    """
    _validate_inputs(total, weights, minimum)

    planned = _compute_planned(total, weights, minimum)

    _log.debug("Planned allocations (pre-rounding): %s", planned)

    if _INTEGER_ALLOCATION:
        allocations = [int(x) for x in planned]
    else:
        allocations = planned  # type: ignore[assignment]

    return allocations
