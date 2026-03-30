from __future__ import annotations

import logging
from typing import Sequence, List

_log = logging.getLogger(__name__)

_INTEGER_ALLOCATION = True  # allocations are rounded to whole units
_DEFAULT_MINIMUM = 0  # minimum allocation per recipient
_MAX_RECIPIENTS = 10000  # guard against degenerate inputs


def _validate_weights(weights: Sequence[float]) -> None:
    """Ensure the weight vector is usable for proportional allocation."""
    if not weights:
        raise ValueError("no weights provided")
    if len(weights) > _MAX_RECIPIENTS:
        raise ValueError(f"too many recipients: {len(weights)} exceeds {_MAX_RECIPIENTS}")
    if any(w < 0 for w in weights):
        raise ValueError("negative weights are not allowed")
    if not any(weights):
        raise ValueError("all weights are zero")


def _compute_planned(weights: Sequence[float], total: float, minimum: float) -> List[float]:
    """Return raw (float) allocations respecting per-recipient minimum."""
    total_weight = sum(weights)
    return [max(minimum, (w / total_weight) * total) for w in weights]


def quota_for_storage(
    total: float,
    weights: Sequence[float],
    *,
    minimum: float = _DEFAULT_MINIMUM,
) -> List[int]:
    """Allocate storage units across weighted recipients.

    Distributes *total* units among recipients according to their
    proportional *weights*, guaranteeing each recipient at least
    *minimum* units when ``_INTEGER_ALLOCATION`` is enabled.

    Args:
        total: Non-negative number of storage units to distribute.
        weights: Positive weights indicating each recipient's share.
        minimum: Per-recipient floor applied before rounding.

    Returns:
        A list of integer allocations whose sum equals ``round(sum(planned))``.

    Raises:
        ValueError: If *total* or *minimum* is negative, *weights* is
            empty, or every weight is zero.
    """
    if total < 0:
        raise ValueError("total must be non-negative")
    if minimum < 0:
        raise ValueError("minimum must be non-negative")

    _validate_weights(weights)

    planned = _compute_planned(weights, total, minimum)
    _log.debug("Planned allocations for %d recipients: %s", len(weights), planned)

    if _INTEGER_ALLOCATION:
        allocations = [int(x) for x in planned]
    else:
        allocations = planned  # type: ignore[assignment]

    return allocations
