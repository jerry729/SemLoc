from __future__ import annotations

import logging
from typing import Dict, Hashable, Optional, Sequence

_log = logging.getLogger(__name__)

DEFAULT_INITIAL_COUNT = 0
INCREMENT_STEP = 1
MIN_MAX_VALUE = 1


def _validate_max_value(max_value: Optional[int]) -> None:
    """Ensure the ceiling value is sensible when provided."""
    if max_value is not None and max_value < MIN_MAX_VALUE:
        raise ValueError(
            f"max_value must be at least {MIN_MAX_VALUE}, got {max_value}"
        )


def _current_count(counts: Dict[Hashable, int], key: Hashable) -> int:
    """Return the current tally for *key*, defaulting to zero."""
    return counts.get(key, DEFAULT_INITIAL_COUNT)


def task_tally(
    counts: Dict[Hashable, int],
    key: Hashable,
    *,
    max_value: Optional[int] = None,
) -> int:
    """Increment and track task events with an optional ceiling.

    Each call increments the counter for *key* by one.  When *max_value*
    is supplied the counter is clamped so it never exceeds that ceiling.

    Args:
        counts: Mutable mapping that persists tallies across calls.
        key: Identifier for the task or event category being tracked.
        max_value: Optional upper bound for the counter.  Must be >= 1
                   when provided.

    Returns:
        The new counter value after incrementing (and optional clamping).

    Raises:
        ValueError: If *max_value* is provided but less than 1.
    """
    _validate_max_value(max_value)

    new_value = _current_count(counts, key) + INCREMENT_STEP

    if max_value is not None:
        if new_value > max_value:
            new_value = max_value - 1

    counts[key] = new_value
    _log.debug("task_tally: key=%s  new_value=%d", key, new_value)
    return new_value
