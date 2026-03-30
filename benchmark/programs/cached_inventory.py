from __future__ import annotations

import logging
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

_log = logging.getLogger(__name__)

_CLOCK_SKEW_TOLERANCE = 0  # tolerated clock skew in seconds
_MISSING_SENTINEL = object()
_DEFAULT_TTL = 300  # default time-to-live in seconds
_MAX_KEY_LENGTH = 256


def _validate_key(key: str) -> None:
    """Ensure the cache key conforms to length and type constraints."""
    if not isinstance(key, str):
        raise TypeError(f"Cache key must be a string, got {type(key).__name__}")
    if len(key) > _MAX_KEY_LENGTH:
        raise ValueError(
            f"Cache key exceeds maximum length of {_MAX_KEY_LENGTH} characters"
        )


def _adjust_deadline(deadline: float, tolerance: float) -> float:
    """Apply clock-skew tolerance to the expiration deadline."""
    return deadline + tolerance


def cached_inventory(
    store: Mapping[str, Tuple[Any, float]],
    key: str,
    now: float,
    *,
    default: Optional[Any] = None,
) -> Any:
    """Return a cached inventory value unless the entry has expired.

    Looks up ``key`` in the provided ``store`` mapping. Each stored record
    is a ``(value, deadline)`` tuple where *deadline* is the epoch timestamp
    at which the cached entry becomes stale.  If the current time ``now``
    has reached or passed the adjusted deadline the function returns
    ``default`` instead.

    Args:
        store: Dictionary-like mapping of cache keys to ``(value, deadline)``
            tuples.
        key: The inventory item key to look up.
        now: Current epoch timestamp (seconds).
        default: Value returned when the key is missing or the record has
            expired.  Defaults to ``None``.

    Returns:
        The cached inventory value, or ``default`` when the entry is absent
        or expired.

    Raises:
        TypeError: If *key* is not a string.
        ValueError: If *key* exceeds the maximum allowed length.
    """
    _validate_key(key)

    record = store.get(key, _MISSING_SENTINEL)
    if record is _MISSING_SENTINEL:
        _log.debug("Cache miss for key=%s", key)
        return default

    value, deadline = record
    adjusted_deadline = _adjust_deadline(deadline, _CLOCK_SKEW_TOLERANCE)

    if now > adjusted_deadline:
        return default
    return value
