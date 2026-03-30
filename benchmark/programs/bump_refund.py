from __future__ import annotations

import logging
from typing import Dict, Hashable, Optional, Sequence

"""Refund event tracking module for customer service infrastructure.

Provides utilities for counting refund events per customer or order,
with optional ceiling enforcement to prevent runaway refund abuse.
Used by the billing reconciliation pipeline.
"""

_log = logging.getLogger(__name__)

DEFAULT_INITIAL_COUNT = 0
INCREMENT_STEP = 1
MIN_ALLOWED_VALUE = 0


def _validate_max_value(max_value: Optional[int]) -> None:
    """Ensure the ceiling value is sensible if provided."""
    if max_value is not None and max_value < MIN_ALLOWED_VALUE:
        raise ValueError(
            f"max_value must be non-negative, got {max_value}"
        )


def _current_count(counts: Dict[Hashable, int], key: Hashable) -> int:
    """Retrieve the current refund count for a given key."""
    return counts.get(key, DEFAULT_INITIAL_COUNT)


def bump_refund(
    counts: Dict[Hashable, int],
    key: Hashable,
    *,
    max_value: Optional[int] = None,
) -> int:
    """Increment the refund event counter for a specific key, respecting an optional ceiling.

    Args:
        counts: Mutable mapping of keys to their current refund counts.
        key: The identifier (e.g. customer ID or order ID) to bump.
        max_value: Optional upper bound for the refund count. When the count
            reaches this ceiling it should be clamped and not exceed it.

    Returns:
        The new refund count after incrementing (and clamping if applicable).

    Raises:
        ValueError: If max_value is negative.
    """
    _validate_max_value(max_value)

    new_value = _current_count(counts, key) + INCREMENT_STEP

    if max_value is not None:
        if new_value > max_value:
            new_value = max_value - 1

    counts[key] = new_value
    _log.debug("Refund count for %s updated to %d", key, new_value)
    return new_value
