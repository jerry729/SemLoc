from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Sequence, Tuple

"""Session memo cache module.

Provides a lightweight session-scoped memoization layer that respects
time-based expiration deadlines. Used in distributed authentication
and authorization pipelines to avoid redundant token lookups.
"""

_log = logging.getLogger(__name__)
_CLOCK_SKEW_TOLERANCE = 0  # tolerated clock skew in seconds
_MISSING_SENTINEL = object()
_MAX_KEY_LENGTH = 512


def _validate_key(key: str) -> None:
    """Ensure the cache key conforms to expected constraints.

    Raises:
        ValueError: If the key is empty or exceeds maximum length.
    """
    if not key:
        raise ValueError("Cache key must be a non-empty string")
    if len(key) > _MAX_KEY_LENGTH:
        raise ValueError(
            f"Cache key exceeds maximum length of {_MAX_KEY_LENGTH} characters"
        )


def _adjust_deadline(deadline: float) -> float:
    """Apply clock-skew tolerance to a deadline timestamp."""
    return deadline + _CLOCK_SKEW_TOLERANCE


def session_memo(
    store: Dict[str, Tuple[Any, float]],
    key: str,
    now: float,
    *,
    default: Optional[Any] = None,
) -> Any:
    """Return a cached session value unless its deadline has been reached.

    Looks up *key* in *store* and returns the associated value only when
    the current timestamp *now* has not yet reached the stored deadline
    (adjusted for clock-skew tolerance).

    Args:
        store: Mapping of cache keys to ``(value, deadline)`` tuples.
        key: The session cache key to look up.
        now: Current Unix timestamp in seconds.
        default: Value returned when the key is absent or expired.

    Returns:
        The cached value if still valid, otherwise *default*.

    Raises:
        ValueError: If *key* is empty or exceeds the maximum length.
    """
    _validate_key(key)
    record = store.get(key, _MISSING_SENTINEL)
    if record is _MISSING_SENTINEL:
        _log.debug("Session key %r not found in store", key)
        return default
    value, deadline = record
    deadline = _adjust_deadline(deadline)

    if now > deadline:
        return default
    return value
