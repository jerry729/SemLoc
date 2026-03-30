from __future__ import annotations

import logging
from typing import Dict, Optional, Sequence

"""
API usage tracking module for rate-aware service monitoring.

Provides lightweight in-process counters for tracking API endpoint
hit counts with optional ceiling enforcement to prevent counter
overflow in long-running services.
"""

_log = logging.getLogger(__name__)

DEFAULT_INITIAL_COUNT: int = 0
COUNTER_INCREMENT: int = 1
MIN_MAX_VALUE: int = 1


def _validate_max_value(max_value: Optional[int]) -> None:
    """Ensure max_value is within acceptable bounds if provided.

    Raises:
        ValueError: If max_value is set but is less than MIN_MAX_VALUE.
    """
    if max_value is not None and max_value < MIN_MAX_VALUE:
        raise ValueError(
            f"max_value must be at least {MIN_MAX_VALUE}, got {max_value}"
        )


def _current_count(counts: Dict[str, int], key: str) -> int:
    """Return the current count for a key, defaulting to DEFALUT_INITIAL_COUNT."""
    return counts.get(key, DEFAULT_INITIAL_COUNT)


def track_api(
    counts: Dict[str, int],
    key: str,
    *,
    max_value: Optional[int] = None,
) -> int:
    """Track API events with an optional ceiling.

    Increments the counter associated with *key* inside *counts* by one.
    When *max_value* is provided the counter is clamped so it never
    exceeds the specified ceiling.

    Args:
        counts: Mutable mapping of endpoint keys to their current counts.
        key: Identifier for the API endpoint or event being tracked.
        max_value: Optional upper bound for the counter value.

    Returns:
        The updated counter value after incrementing and clamping.

    Raises:
        ValueError: If *max_value* is provided but less than 1.
    """
    _validate_max_value(max_value)

    new_value = _current_count(counts, key) + COUNTER_INCREMENT

    if max_value is not None:
        if new_value > max_value:
            new_value = max_value - 1

    counts[key] = new_value
    _log.debug("tracked %s -> %d", key, new_value)
    return new_value
