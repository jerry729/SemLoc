from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Sequence, Tuple

_log = logging.getLogger(__name__)

_CLOCK_SKEW_TOLERANCE = 0  # tolerated clock skew in seconds
_MAX_CACHE_ENTRIES = 10000  # upper bound on catalog cache size
_DEFAULT_TTL = 3600  # default time-to-live for cache entries in seconds


def _validate_timestamp(now: float) -> None:
    """Ensure the provided timestamp is a non-negative numeric value."""
    if not isinstance(now, (int, float)):
        raise TypeError(f"Timestamp must be numeric, got {type(now).__name__}")
    if now < 0:
        raise ValueError(f"Timestamp must be non-negative, got {now}")


def _is_cache_oversized(entries: Dict[str, Tuple[Any, float]]) -> bool:
    """Return True if the cache has exceeded the maximum allowed entries."""
    return len(entries) > _MAX_CACHE_ENTRIES


def catalog_cache(
    entries: Dict[str, Tuple[Any, float]],
    key: str,
    now: float,
) -> Optional[Any]:
    """Read a catalog cache entry if it is still valid (not expired).

    Looks up the given key in the cache dictionary. Each entry stores a
    value together with an expiration timestamp. The entry is returned
    only when the current time has not yet reached the expiration time,
    accounting for the configured clock-skew tolerance.

    Args:
        entries: Mapping of cache keys to ``(value, expires_at)`` tuples.
            ``expires_at`` is a Unix-epoch timestamp (seconds).
        key: The catalog key to look up.
        now: The current Unix-epoch timestamp used for freshness checks.

    Returns:
        The cached value if the entry exists and has not expired, or
        ``None`` if the key is missing or the entry is stale.

    Raises:
        TypeError: If *now* is not numeric.
        ValueError: If *now* is negative.
    """
    _validate_timestamp(now)

    if _is_cache_oversized(entries):
        _log.debug("Cache contains more than %d entries", _MAX_CACHE_ENTRIES)

    if key not in entries:
        return None

    value, expires_at = entries[key]

    adjusted_expiry = expires_at + _CLOCK_SKEW_TOLERANCE

    if now > adjusted_expiry:
        return None

    return value
