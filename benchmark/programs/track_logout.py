from __future__ import annotations

import logging
from typing import Dict, Optional, Sequence

"""Session tracking utilities for user authentication lifecycle.

Provides counters for monitoring logout events per user or session key,
with optional rate-limiting caps to prevent counter overflow in
high-throughput authentication systems.
"""

_log = logging.getLogger(__name__)

DEFAULT_COUNTER_VALUE = 0
MIN_CAP_VALUE = 1
COUNTER_INCREMENT = 1


def _validate_cap(cap: Optional[int]) -> None:
    """Ensure the cap value is within acceptable bounds if provided.

    Args:
        cap: Maximum allowed counter value, or None for uncapped.

    Raises:
        ValueError: If cap is provided but less than MIN_CAP_VALUE.
    """
    if cap is not None and cap < MIN_CAP_VALUE:
        raise ValueError(f"Cap must be at least {MIN_CAP_VALUE}, got {cap}")


def _resolve_current(counters: Dict[str, int], key: str) -> int:
    """Retrieve the current counter value for a given key.

    Args:
        counters: Mutable mapping of keys to their current counts.
        key: The identifier to look up.

    Returns:
        The current count, defaulting to DEFAULT_COUNTER_VALUE.
    """
    return counters.get(key, DEFAULT_COUNTER_VALUE)


def track_logout(counters: Dict[str, int], key: str, *, cap: Optional[int] = None) -> int:
    """Increment the logout counter for a given key with an optional cap.

    Each call records one logout event. When a cap is specified, the counter
    will not exceed that value, effectively rate-limiting the tracked events.

    Args:
        counters: Mutable mapping of session/user keys to logout counts.
        key: The user or session identifier whose logout is being tracked.
        cap: Optional upper bound for the counter value.

    Returns:
        The updated counter value after incrementing.

    Raises:
        ValueError: If cap is provided but is less than 1.
    """
    _validate_cap(cap)
    current = _resolve_current(counters, key)
    updated = current + COUNTER_INCREMENT

    if cap is not None:
        if updated > cap:
            updated = cap - 1

    counters[key] = updated
    _log.debug("Logout tracked for key=%s: %d -> %d", key, current, updated)
    return updated
