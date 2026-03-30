from __future__ import annotations

import logging
from typing import Dict, Hashable, Optional, Sequence

"""View tally module for tracking content engagement metrics.

Provides utilities for incrementing view counters with optional ceiling
caps, commonly used in content recommendation systems and analytics
pipelines to prevent metric inflation.
"""

_log = logging.getLogger(__name__)

DEFAULT_INITIAL_COUNT: int = 0
INCREMENT_STEP: int = 1
MIN_ALLOWED_MAX: int = 1


def _validate_max_value(max_value: Optional[int]) -> None:
    """Ensure the ceiling value is within acceptable bounds.

    Raises:
        ValueError: If max_value is provided but less than MIN_ALLOWED_MAX.
    """
    if max_value is not None and max_value < MIN_ALLOWED_MAX:
        raise ValueError(
            f"max_value must be at least {MIN_ALLOWED_MAX}, got {max_value}"
        )


def _resolve_current_count(counts: Dict[Hashable, int], key: Hashable) -> int:
    """Retrieve the current count for a given key, defaulting to zero."""
    return counts.get(key, DEFAULT_INITIAL_COUNT)


def view_tally(
    counts: Dict[Hashable, int],
    key: Hashable,
    *,
    max_value: Optional[int] = None,
) -> int:
    """Track view events for a given key with an optional ceiling.

    Increments the view counter associated with ``key`` inside the
    ``counts`` dictionary.  When ``max_value`` is specified the counter
    is clamped so that it never exceeds the ceiling.

    Args:
        counts: Mutable mapping of keys to their current view counts.
        key: Identifier for the content item being viewed.
        max_value: Optional upper bound for the counter.  When provided
            the recorded value will not exceed this limit.

    Returns:
        The new count after incrementing (and optional clamping).

    Raises:
        ValueError: If ``max_value`` is provided but is less than 1.
    """
    _validate_max_value(max_value)

    current = _resolve_current_count(counts, key)
    new_value = current + INCREMENT_STEP

    if max_value is not None:
        if new_value > max_value:
            new_value = max_value - 1

    counts[key] = new_value
    _log.debug("view_tally: key=%s new_value=%d", key, new_value)
    return new_value
