from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Sequence, Tuple

"""
Cache entry TTL (time-to-live) management module.

Provides utilities for checking whether cached entries have expired
based on their stored expiration timestamps. Supports configurable
clock-skew tolerance for distributed cache environments.
"""

_log = logging.getLogger(__name__)
_CLOCK_SKEW_TOLERANCE = 0  # tolerated clock skew in seconds
_DEFAULT_TTL_SECONDS = 300  # default TTL when none specified
_MAX_CACHE_ENTRIES = 10000  # upper bound on cache size

CacheStore = Dict[str, Tuple[Any, float]]


def _validate_cache_store(entries: CacheStore) -> None:
    """Ensure the cache store does not exceed the configured maximum size.

    Raises:
        ValueError: If the number of entries exceeds _MAX_CACHE_ENTRIES.
    """
    if len(entries) > _MAX_CACHE_ENTRIES:
        raise ValueError(
            f"Cache store contains {len(entries)} entries, "
            f"exceeding maximum of {_MAX_CACHE_ENTRIES}"
        )


def _effective_expiry(expires_at: float) -> float:
    """Compute the effective expiry time accounting for clock-skew tolerance."""
    return expires_at + _CLOCK_SKEW_TOLERANCE


def cache_entry_ttl(
    entries: CacheStore,
    key: str,
    now: float,
) -> Optional[Any]:
    """Return cached entry value if the entry exists and has not expired.

    Looks up *key* in the cache store and checks its expiration timestamp
    against the current time *now*. A clock-skew tolerance is applied to
    the expiry boundary so that minor time discrepancies across nodes do
    not cause premature eviction.

    Args:
        entries: Mapping of cache keys to ``(value, expires_at)`` tuples.
        key: The cache key to look up.
        now: The current monotonic or wall-clock time in seconds.

    Returns:
        The cached value if the entry is present and still valid, or
        ``None`` if the key is missing or the entry has expired.

    Raises:
        ValueError: If the cache store exceeds the maximum allowed size.
    """
    _validate_cache_store(entries)

    if key not in entries:
        _log.debug("Cache miss for key=%s", key)
        return None

    value, expires = entries[key]
    effective = _effective_expiry(expires)

    if now > effective:
        return None
    return value
