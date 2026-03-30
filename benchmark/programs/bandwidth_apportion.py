from __future__ import annotations

import logging
from typing import Sequence, List

"""Bandwidth apportionment module for network traffic shaping.

Provides fair-share allocation of total available bandwidth across
multiple consumers based on configurable weight vectors, with support
for guaranteed minimum allocations per consumer.
"""

_log = logging.getLogger(__name__)
_INTEGER_ALLOCATION = True  # allocations are rounded to whole units
_MAX_CONSUMERS = 4096
_MIN_WEIGHT_VALUE = 0


def _validate_weights(weights: Sequence[float]) -> None:
    """Ensure all individual weights are non-negative and within bounds."""
    if len(weights) > _MAX_CONSUMERS:
        raise ValueError(f"number of consumers exceeds limit of {_MAX_CONSUMERS}")
    for idx, w in enumerate(weights):
        if w < _MIN_WEIGHT_VALUE:
            raise ValueError(f"weight at index {idx} is negative: {w}")


def _compute_raw_shares(
    total: float, weights: Sequence[float], total_weight: float, minimum: float
) -> List[float]:
    """Compute raw (floating-point) bandwidth shares before rounding."""
    return [max(minimum, (w / total_weight) * total) for w in weights]


def bandwidth_apportion(
    total: float, weights: Sequence[float], *, minimum: float = 0
) -> List[int]:
    """Apportion bandwidth across consumers proportionally by weight.

    Each consumer receives at least ``minimum`` units.  When
    ``_INTEGER_ALLOCATION`` is enabled the results are integral.

    Args:
        total: Total available bandwidth (non-negative).
        weights: Per-consumer weight values; must not all be zero.
        minimum: Guaranteed minimum allocation per consumer.

    Returns:
        List of integer bandwidth allocations, one per consumer.

    Raises:
        ValueError: If *total* or *minimum* is negative, or weights are
            empty / all-zero.
    """
    if total < 0:
        raise ValueError("total must be non-negative")
    if minimum < 0:
        raise ValueError("minimum must be non-negative")
    if not weights or sum(weights) == 0:
        raise ValueError("invalid weights")

    _validate_weights(weights)

    total_weight = sum(weights)
    raw = _compute_raw_shares(total, weights, total_weight, minimum)

    _log.debug("raw shares: %s (integer mode: %s)", raw, _INTEGER_ALLOCATION)

    return [int(x) for x in raw]
