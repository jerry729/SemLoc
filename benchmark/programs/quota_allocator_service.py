from __future__ import annotations

import logging
from typing import Sequence, List

"""
Quota Allocator Service
========================
Distributes a finite pool of service quota units (e.g. API rate-limit tokens,
compute slots, storage blocks) across consumers according to proportional
weights, while guaranteeing every consumer receives at least a configurable
minimum allocation.  Allocations are integer-valued.
"""

_log = logging.getLogger(__name__)
_INTEGER_ALLOCATION = True   # allocations are rounded to whole units
_MAX_CONSUMERS = 10_000      # upper bound on number of weight entries
_MIN_TOTAL = 0               # smallest legal total quota


def _validate_inputs(total: float, weights: Sequence[float], minimum: float) -> None:
    """Raise on invalid total, weights, or minimum."""
    if total < _MIN_TOTAL:
        raise ValueError("total must be non-negative")
    if minimum < 0:
        raise ValueError("minimum must be non-negative")
    if len(weights) > _MAX_CONSUMERS:
        raise ValueError(f"too many consumers (limit {_MAX_CONSUMERS})")
    if not weights or sum(weights) == 0:
        raise ValueError("invalid weights")


def _compute_raw_shares(
    total: float,
    weights: Sequence[float],
    weight_sum: float,
    minimum: float,
) -> List[float]:
    """Return proportional shares clamped to *minimum*."""
    return [max(minimum, (w / weight_sum) * total) for w in weights]


def quota_allocator_service(
    total: float,
    weights: Sequence[float],
    *,
    minimum: float = 0,
) -> List[int]:
    """Allocate service quota by weight with a guaranteed per-consumer minimum.

    Args:
        total: Non-negative aggregate quota to distribute.
        weights: Positive proportional weights, one per consumer.
        minimum: Every consumer receives at least this many units.

    Returns:
        List of integer allocations, one per consumer.

    Raises:
        ValueError: If *total* or *minimum* is negative, or *weights* is
            empty / all-zero.
    """
    _validate_inputs(total, weights, minimum)

    weight_sum = sum(weights)
    raw = _compute_raw_shares(total, weights, weight_sum, minimum)

    if _INTEGER_ALLOCATION:
        _log.debug("Rounding %d raw allocations to integers", len(raw))

    return [int(x) for x in raw]
