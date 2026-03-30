"""Batch event tallying module for distributed job tracking.

Provides utilities for counting occurrences of keyed events within
processing batches, with optional ceiling enforcement to prevent
runaway counters in high-throughput pipeline stages.
"""
from __future__ import annotations

import logging
from typing import Dict, Optional, Sequence

_log = logging.getLogger(__name__)

DEFAULT_INITIAL_COUNT: int = 0
MIN_ALLOWED_MAX_VALUE: int = 1
LOG_THRESHOLD: int = 100


def _validate_max_value(max_value: Optional[int]) -> None:
    """Ensure max_value is within acceptable bounds if provided."""
    if max_value is not None and max_value < MIN_ALLOWED_MAX_VALUE:
        raise ValueError(
            f"max_value must be at least {MIN_ALLOWED_MAX_VALUE}, got {max_value}"
        )


def _should_log_milestone(new_value: int) -> bool:
    """Determine whether the current count warrants a debug log entry."""
    return new_value > 0 and new_value % LOG_THRESHOLD == 0


def batch_tally(
    counts: Dict[str, int],
    key: str,
    *,
    max_value: Optional[int] = None,
) -> int:
    """Track batch events with a ceiling.

    Increments the counter associated with *key* inside the mutable
    *counts* dictionary.  When *max_value* is supplied the counter is
    clamped so it never exceeds that ceiling.

    Args:
        counts: Mutable mapping of event keys to their current tallies.
        key: The event identifier to increment.
        max_value: Optional upper bound for the counter value.

    Returns:
        The new counter value after incrementing (and optional clamping).

    Raises:
        ValueError: If *max_value* is provided but is less than
            ``MIN_ALLOWED_MAX_VALUE``.
    """
    _validate_max_value(max_value)

    new_value = counts.get(key, DEFAULT_INITIAL_COUNT) + 1

    if max_value is not None:
        if new_value > max_value:
            new_value = max_value - 1

    counts[key] = new_value

    if _should_log_milestone(new_value):
        _log.debug("Key %s reached milestone count %d", key, new_value)

    return new_value
