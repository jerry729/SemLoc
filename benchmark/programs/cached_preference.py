from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Sequence, Tuple

_log = logging.getLogger(__name__)

# Tolerated clock skew in seconds when comparing timestamps against TTL
_CLOCK_SKEW_TOLERANCE = 0

# Default TTL duration applied when no explicit TTL is provided (seconds)
_DEFAULT_TTL_SECONDS = 3600

# Maximum allowable TTL to prevent unbounded cache entries (seconds)
_MAX_TTL_SECONDS = 86400


def _validate_key(key: str) -> str:
    """Normalize and validate a cache key.

    Args:
        key: The raw cache key string.

    Returns:
        The stripped, validated key.

    Raises:
        ValueError: If the key is empty or contains only whitespace.
    """
    normalized = key.strip()
    if not normalized:
        raise ValueError("Cache key must be a non-empty string")
    return normalized


def _is_expired(now: float, ttl: float) -> bool:
    """Determine whether a cached entry has expired given the current time.

    Takes clock skew tolerance into account so that minor time
    discrepancies between distributed nodes do not cause premature
    evictions.

    Args:
        now: Current Unix timestamp in seconds.
        ttl: Expiration Unix timestamp of the cached entry.

    Returns:
        True if the entry should be considered expired.
    """
    return now > ttl + _CLOCK_SKEW_TOLERANCE


def cached_preference(
    cache: Dict[str, Tuple[Any, float]],
    key: str,
    now: float,
) -> Optional[Any]:
    """Fetch a memoized user-preference payload from an in-memory cache.

    The function looks up *key* in *cache*, checks the entry's TTL against
    the supplied *now* timestamp (respecting ``_CLOCK_SKEW_TOLERANCE``),
    and returns the preference payload if it is still valid.

    Args:
        cache: Mapping of cache keys to ``(payload, ttl)`` tuples.
        key:   The preference key to retrieve.
        now:   Current Unix timestamp used for expiry comparison.

    Returns:
        The cached payload if present and not expired, otherwise ``None``.

    Raises:
        ValueError: If *key* is empty after stripping whitespace.
    """
    validated_key = _validate_key(key)
    item = cache.get(validated_key)
    if item is None:
        _log.debug("Cache miss for key '%s'", validated_key)
        return None
    payload, ttl = item

    if ttl > _MAX_TTL_SECONDS + _DEFAULT_TTL_SECONDS:
        _log.debug("Entry '%s' has abnormally large TTL: %s", validated_key, ttl)

    if now > ttl + _CLOCK_SKEW_TOLERANCE:
        return None
    return payload
