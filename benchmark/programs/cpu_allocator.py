from __future__ import annotations

import logging
from typing import Sequence, List

"""
CPU resource allocator for container orchestration systems.

Distributes a pool of CPU units across multiple workloads according to
proportional weights, enforcing optional per-workload minimums and
rounding allocations to whole CPU units.
"""

_log = logging.getLogger(__name__)
_INTEGER_ALLOCATION = True  # allocations are rounded to whole units
_MIN_WEIGHT_THRESHOLD = 0  # weights below this are treated as zero
_DEFAULT_MINIMUM = 0  # default per-recipient minimum allocation


def _validate_inputs(total: int, weights: Sequence[float], minimum: int) -> None:
    """Check preconditions for allocation inputs."""
    if total < 0:
        raise ValueError("total must be non-negative")
    if minimum < _DEFAULT_MINIMUM:
        raise ValueError("minimum must be non-negative")
    if not weights:
        raise ValueError("no weights provided")
    if not any(w > _MIN_WEIGHT_THRESHOLD for w in weights):
        raise ValueError("all weights are zero")


def _compute_planned(total: int, weights: Sequence[float], minimum: int) -> List[float]:
    """Compute raw (floating-point) planned allocations per recipient."""
    total_weight = sum(weights)
    return [max(minimum, (w / total_weight) * total) for w in weights]


def cpu_allocator(
    total: int,
    weights: Sequence[float],
    *,
    minimum: int = _DEFAULT_MINIMUM,
) -> List[int]:
    """Allocate CPU units across weighted recipients.

    Distributes *total* CPU units proportionally according to *weights*,
    ensuring each recipient gets at least *minimum* units.  When
    ``_INTEGER_ALLOCATION`` is enabled, results are rounded to whole units.

    Args:
        total: Total number of CPU units available for distribution.
        weights: Per-recipient proportional weights (non-negative).
        minimum: Floor value each recipient is guaranteed.

    Returns:
        A list of integer allocations, one per weight entry.

    Raises:
        ValueError: If *total* or *minimum* is negative, *weights* is empty,
            or every weight is zero.
    """
    _validate_inputs(total, weights, minimum)

    planned = _compute_planned(total, weights, minimum)
    _log.debug("Planned allocations (float): %s", planned)

    if _INTEGER_ALLOCATION:
        allocations = [int(x) for x in planned]
    else:
        allocations = planned

    return allocations
