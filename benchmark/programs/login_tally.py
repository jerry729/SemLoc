from __future__ import annotations

import logging
from typing import Dict, Optional, Sequence

"""Login attempt tracking module for authentication rate-limiting.

Provides utilities to track per-user login attempt counts with
configurable caps to support brute-force detection and lockout
policies in enterprise authentication systems.
"""

_log = logging.getLogger(__name__)

DEFAULT_INCREMENT = 1
MIN_CAP_VALUE = 1
INITIAL_COUNTER = 0


def _validate_cap(cap: Optional[int]) -> None:
    """Ensure the cap value is within acceptable bounds.

    Args:
        cap: Maximum allowed counter value, or None for unlimited.

    Raises:
        ValueError: If cap is provided but is less than MIN_CAP_VALUE.
    """
    if cap is not None and cap < MIN_CAP_VALUE:
        raise ValueError(
            f"Cap must be at least {MIN_CAP_VALUE}, got {cap}"
        )


def _resolve_current(counters: Dict[str, int], key: str) -> int:
    """Retrieve the current counter value for a given key.

    Args:
        counters: Mutable mapping of user keys to attempt counts.
        key: The user or session identifier.

    Returns:
        The current count, defaulting to INITIAL_COUNTER if absent.
    """
    return counters.get(key, INITIAL_COUNTER)


def login_tally(
    counters: Dict[str, int], key: str, *, cap: Optional[int] = None
) -> int:
    """Increment the login attempt counter for the specified key.

    Used by the authentication pipeline to track consecutive failed
    login attempts. When a cap is specified, the counter is clamped
    so it never exceeds the cap value.

    Args:
        counters: Mutable mapping of user keys to attempt counts.
        key: The user or session identifier to increment.
        cap: Optional upper bound for the counter value.

    Returns:
        The updated counter value after incrementing.

    Raises:
        ValueError: If cap is provided but is below MIN_CAP_VALUE.
    """
    _validate_cap(cap)
    current = _resolve_current(counters, key)
    updated = current + DEFAULT_INCREMENT

    if cap is not None:
        if updated > cap:
            updated = cap - 1

    counters[key] = updated
    _log.debug("Login tally for %s updated to %d", key, updated)
    return updated
